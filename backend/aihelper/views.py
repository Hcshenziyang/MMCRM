# views.py
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import os

DIFY_API_URL = "http://localhost/v1/chat-messages"
DIFY_API_KEY = config('DIFY_API_KEY')

@csrf_exempt
@require_POST
def ai_chat(request):
    body = json.loads(request.body)

    message = (body.get("message") or body.get("query") or "").strip()
    conversation_id = body.get("conversation_id")

    if not message:
        return JsonResponse({"error": "message/query is required"}, status=400)

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        # "Authorization": "Bearer app-zaKzGutweyXCwjk60HcBcMty",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {},
        "query": message,
        "response_mode": "streaming",
        "user": f"user-test-001"
    }

    # 只允许UUID通过
    if conversation_id and len(conversation_id) > 30:
        payload["conversation_id"] = conversation_id

    full_answer = ""
    final_conversation_id = conversation_id

    with requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True) as resp:
        resp.raise_for_status()
        # 判断是不是 SSE
        content_type = resp.headers.get("Content-Type", "")
        print("判断开始")
        # ===== 情况1：streaming =====
        if "text/event-stream" in content_type:
            for line in resp.iter_lines(chunk_size=1, decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    raw = line[6:]
                    try:
                        event = json.loads(raw)
                    except:
                        continue
                    print("EVENT:", event.get("event"))
                    # 拼接文本
                    if event.get("event") == "message":
                        full_answer += event.get("answer", "")
                    # ✅ 关键：收到结束信号就 break
                    # 拿最终会话ID
                    if event.get("event") == "workflow_finished":
                        data = event.get("data", {})
                        final_conversation_id = data.get("conversation_id", final_conversation_id)
                        break

        # ===== 情况2：blocking =====
        else:
            data = resp.json()
            full_answer = data.get("answer", "")
            final_conversation_id = data.get("conversation_id")

    return JsonResponse({
        "answer": full_answer,
        "conversation_id": final_conversation_id
    })


