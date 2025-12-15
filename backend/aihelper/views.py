import json
import logging
from datetime import datetime, timedelta

# Django & DRF Imports
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI

# LLM-api调用
def call_llm(system_prompt: str, user_prompt: str):
    try:
        client = OpenAI(
            api_key=getattr(settings, 'DEEPSEEK_API_KEY', None),  # 环境变量中配置API
            base_url="https://api.deepseek.com"
        )
        if not client.api_key:
            print("DEEPSEEK_API_KEY 未在 Django settings 中配置。")
            return json.dumps({
                "intent": "error",
                "slots": {"message": "AI服务配置错误，请联系管理员。"}
            })

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            temperature=0,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"调用 LLM API 时发生错误: {e}")
        return json.dumps({
            "intent": "error",
            "slots": {"message": f"调用AI服务时发生未知错误: {e}"}
        })

# 接收自然语言并转换为前端指令
class AiCommandView(APIView):
    # 确保只有登录用户才能访问。你还可以创建更精细的权限。
    permission_classes = [IsAuthenticated]

    def _llm_intent_parse(self, text: str):
        system_prompt = """
        你是一个意图分类器和信息提取器。
        你的任务是分析用户输入的文本，并从中识别出意图和相关的参数（槽位）。

        你只能从以下意图中选择一个：
        - customer.create: 当用户想要创建一个新客户时。需要提取 name, phone等信息。
        - customer.list: 当用户想要查看、搜索或筛选客户列表时。
        - unknown: 当用户意图不明确或超出你的能力范围时。
        - talk: 当用户只是在进行日常对话时。

        你必须返回一个 JSON 对象，不能包含任何解释或其他多余的文字。
        JSON 格式如下：
        {
          "intent": "...",
          "slots": { ... }
        }
        """
        user_prompt = f"用户输入：{text}"

        # 调用LLM并获取返回的字符串
        llm_response_str = call_llm(system_prompt, user_prompt)

        # 将LLM返回的JSON字符串解析为Python字典
        try:
            result = json.loads(llm_response_str)
            intent = result.get("intent", "unknown")
            slots = result.get("slots", {})
            return intent, slots
        except json.JSONDecodeError:
            print(f"无法解析LLM返回的JSON: {llm_response_str}")
            return "error", {"message": "无法解析AI服务的返回结果。"}

    def _generate_command_from_intent(self, intent: str, slots: dict, user):
        # --- 安全边界：意图级别权限校验 ---
        if intent == "customer.create" and not user.has_perm('app_name.add_customer'):
            # 假设你的权限模型是 'app_name.add_customer'
            return {
                "command": "ui.showMessage",
                "payload": {"type": "error", "message": "你没有创建客户的权限。"}
            }

        # --- 逻辑判断与指令生成 ---
        if intent == "customer.create":
            # 校验slots中的字段合法性（例如电话号码格式）
            # ... 此处添加你的校验逻辑 ...

            return {
                "command": "ui.openModal",
                "payload": {
                    "modalId": "customerCreateModal",
                    "formValues": {
                        "name": slots.get("name"),
                        "phone": slots.get("phone"),
                        "tags": slots.get("tags")
                    }
                }
            }

        elif intent == "customer.list":
            # 例子：“我要看上周新增客户”
            # LLM可能不会直接给你日期，你需要在这里做语义理解和转换
            # 这是一个简化的例子，实际可能需要更复杂的日期解析库
            query = {"ordering": "-created_at"}
            if "上周" in slots.get("time_range", ""):
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_last_week = start_of_week - timedelta(seconds=1)
                start_of_last_week = end_of_last_week - timedelta(days=7)
                query["created_after"] = start_of_last_week.strftime('%Y-%m-%d')
                query["created_before"] = end_of_last_week.strftime('%Y-%m-%d')

            return {
                "command": "route.push",
                "payload": {
                    "path": "/customers",
                    "query": query
                }
            }

        elif intent == "talk":
            # 对于闲聊，可以直接返回一个显示消息的指令
            return {
                "command": "ui.showMessage",
                "payload": {"type": "info", "message": "很高兴为您服务，需要我做什么吗？"}
            }

        elif intent == "error":
            # 处理LLM调用或解析时发生的错误
            return {
                "command": "ui.showMessage",
                "payload": {"type": "error", "message": slots.get("message", "发生未知错误")}
            }

        else:  # 对应 unknown 意图
            return {
                "command": "ui.showMessage",
                "payload": {"type": "warning", "message": "抱歉，我暂时无法理解您的指令。"}
            }

    def post(self, request, *args, **kwargs):
        """
        处理前端发送的 POST /ai/command 请求
        """
        # 从请求体中获取用户输入的文本和上下文
        text = request.data.get('text')
        context = request.data.get('context', {})  # context可以包含当前页面等信息

        if not text:
            return Response(
                {"error": "缺少 'text' 字段。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 调用LLM进行意图识别
        intent, slots = self._llm_intent_parse(text)

        # 根据意图生成指令
        command = self._generate_command_from_intent(intent, slots, request.user)

        # 第三层：将指令返回给客户端执行
        return Response(command, status=status.HTTP_200_OK)