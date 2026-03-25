# views.py
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import os
from decouple import config

# region DIFY版本（已废弃）
# 绝绝子，个人的小服务器内存不太够拉dify的，为了方便展示，服务器版本代码直接用deepseek api
# DIFY_API_URL = "http://localhost/v1/chat-messages"
# DIFY_API_KEY = config('DIFY_API_KEY')
#
# @csrf_exempt
# @require_POST
# def ai_chat(request):
#     body = json.loads(request.body)
#
#     message = (body.get("message") or body.get("query") or "").strip()
#     conversation_id = body.get("conversation_id")
#
#     if not message:
#         return JsonResponse({"error": "message/query is required"}, status=400)
#
#     headers = {
#         "Authorization": f"Bearer {DIFY_API_KEY}",
#         # "Authorization": "Bearer app-zaKzGutweyXCwjk60HcBcMty",
#         "Content-Type": "application/json"
#     }
#
#     payload = {
#         "inputs": {},
#         "query": message,
#         "response_mode": "streaming",
#         "user": f"user-test-001"
#     }
#
#     # 只允许UUID通过
#     if conversation_id and len(conversation_id) > 30:
#         payload["conversation_id"] = conversation_id
#
#     full_answer = ""
#     final_conversation_id = conversation_id
#
#     with requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True) as resp:
#         resp.raise_for_status()
#         # 判断是不是 SSE
#         content_type = resp.headers.get("Content-Type", "")
#         print("判断开始")
#         # ===== 情况1：streaming =====
#         if "text/event-stream" in content_type:
#             for line in resp.iter_lines(chunk_size=1, decode_unicode=True):
#                 if not line:
#                     continue
#                 if line.startswith("data: "):
#                     raw = line[6:]
#                     try:
#                         event = json.loads(raw)
#                     except:
#                         continue
#                     print("EVENT:", event.get("event"))
#                     # 拼接文本
#                     if event.get("event") == "message":
#                         full_answer += event.get("answer", "")
#                     # ✅ 关键：收到结束信号就 break
#                     # 拿最终会话ID
#                     if event.get("event") == "workflow_finished":
#                         data = event.get("data", {})
#                         final_conversation_id = data.get("conversation_id", final_conversation_id)
#                         break
#
#         # ===== 情况2：blocking =====
#         else:
#             data = resp.json()
#             full_answer = data.get("answer", "")
#             final_conversation_id = data.get("conversation_id")
#
#     return JsonResponse({
#         "answer": full_answer,
#         "conversation_id": final_conversation_id
#     })
# endregion

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = config('DEEPSEEK_API_KEY')
SYSTEM_PROMPT_WORD = config('SYSTEM_PROMPT_WORD')
@csrf_exempt
@require_POST
def ai_chat(request):
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "请求体不是合法 JSON"}, status=400)

    message = (body.get("message") or body.get("query") or "").strip()
    messages = body.get("messages")
    conversation_id = body.get("conversation_id")  # 先保留，当前版本不真正使用

    if (not message) and (not isinstance(messages, list) or len(messages) == 0):
        return JsonResponse({"error": "message/query or messages is required"}, status=400)

    system_prompt = (SYSTEM_PROMPT_WORD)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    ds_messages = [{"role": "system", "content": system_prompt}]

    if isinstance(messages, list) and len(messages) > 0:
        # 允许前端传 user/assistant/system；也兼容传 ai
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = (m.get("role") or "").strip()
            content = (m.get("content") or "").strip()
            if not role or not content:
                continue
            if role == "ai":
                role = "assistant"
            if role not in ("system", "user", "assistant"):
                continue
            ds_messages.append({"role": role, "content": content})
    else:
        ds_messages.append({"role": "user", "content": message})

    payload = {
        "model": "deepseek-chat",
        "messages": ds_messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        return JsonResponse({"error": "DeepSeek 请求超时"}, status=504)
    except requests.RequestException as e:
        error_text = ""
        try:
            error_text = e.response.text
        except Exception:
            error_text = str(e)
        return JsonResponse(
            {"error": "DeepSeek 请求失败", "detail": error_text},
            status=502,
        )

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return JsonResponse(
            {"error": "DeepSeek 返回格式异常", "raw": data},
            status=502,
        )

    return JsonResponse({
        "answer": answer,
        "conversation_id": conversation_id,  # 暂时原样返回，避免前端改太多
    })