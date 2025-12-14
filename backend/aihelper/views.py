from django.shortcuts import render
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
# Create your views here.
# AI逻辑
'''
第一层：意图识别（Intent / Slot）
输入：网页内一段自然语言（如“帮我建一个客户叫张三，电话xxx，并给他打上VIP”）。
输出：意图 + 参数（如 intent=customer.create, slots={name, phone, tags}）。
LLM 分类（覆盖长尾）：让模型只做“选意图 + 填槽”，不要生成任何可执行代码。

第二层：指令生成（Command Schema）
后端把意图映射到固定的指令协议（非常关键）：
command: "route.push" | "api.call" | "ui.openModal" | "ui.fillForm"
payload: { path, query, api, method, body, modalId, formValues }
例子：
用户说“我要看上周新增客户”
→ { command:"route.push", payload:{ path:"/customers", query:{ created_after:"2025-12-07", created_before:"2025-12-14", ordering:"-created_at"} } }
注意：后端必须做二次校验（权限、字段合法性、过滤条件上限），不要相信模型给的任何参数。

第三层：客户端执行（Router + Action Executor）
前端只做两件事：
把用户文本发给后端：POST /ai/command { text, context }
context 里带当前页面、用户角色、当前选中的客户/项目ID（如果有）。
接收后端返回的 command，然后走一个执行器：
route.push：调用前端路由跳转（react-router / vue-router / uni-app 的 navigateTo）
ui.openModal/ui.fillForm：打开弹窗并预填表单
api.call：调用既有接口（仍走你现有鉴权与权限系统）
关键安全边界（必须做）
白名单：只允许有限的 intent 与 command；任何未知值直接拒绝。
权限：意图级别权限校验（比如 customer.delete 必须管理员）。
可解释与可回滚：返回“将要执行什么”，前端默认“确认后执行”，尤其是写操作（创建/删除/更新）。
观测与迭代：把 text、intent、slots、最终执行结果落日志，方便你补规则/微调提示词。
'''


# LLM调用
def call_llm(system_prompt, user_prompt):
    # deepseek api 调用
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key="？？",  # todo 待修改环境变量
        base_url="https://api.deepseek.com"
    )
    # 获取用户输入的问题
    question = "问题"
    # 调用大模型 API
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{user_prompt}"},
        ],
        stream=False)
    # 提取回答内容
    answer = response.choices[0].message.content
    return answer

# 意图识别
def llm_intent_parse(self, text: str):
    """
    实验态：全 AI 意图识别
    """
    system_prompt = """
你是一个意图分类器。
你只能从以下intent中选择一个：
customer.create
customer.list
unknown

你只能返回 JSON，不要解释，不要多余文字。
JSON 格式：
{
  "intent": "...",
  "slots": { ... }
}
"""
    user_prompt = f"用户输入：{text}"
    result = call_llm(system_prompt, user_prompt)
    return result["intent"], result.get("slots", {})


class AIIntentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        text: str = request.data.get("text", "").strip()
        intent, slots = self.rule_intent_parse(text)
        return Response({
            "intent": intent,
            "slots": slots
        })

    def rule_intent_parse(self, text: str):
        """
        规则优先的意图识别
        """
        # ---------- customer.create ----------
        if self._match_any(text, ["创建客户", "新增客户", "加客户", "建一个客户"]):
            slots = {}

            # 姓名
            name_match = re.search(r"客户叫(.+?)(，|,|$)", text)
            if name_match:
                slots["name"] = name_match.group(1).strip()

            # 电话
            phone_match = re.search(r"(电话|手机号)(是)?(\d{6,15})", text)
            if phone_match:
                slots["phone"] = phone_match.group(3)

            # 标签
            if "VIP" in text:
                slots.setdefault("tags", []).append("VIP")

            return "customer.create", slots

        # ---------- customer.list ----------
        if self._match_any(text, ["客户列表", "查看客户", "所有客户"]):
            return "customer.list", {}

        # ---------- customer.detail ----------
        if self._match_any(text, ["客户详情", "查看客户"]):
            name_match = re.search(r"客户(.+)", text)
            if name_match:
                return "customer.detail", {
                    "name": name_match.group(1).strip()
                }

        # ---------- fallback ----------
        return "unknown", {}

    def _match_any(self, text: str, keywords: list[str]) -> bool:
        return any(k in text for k in keywords)