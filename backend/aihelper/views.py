# views.py
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import os

DIFY_API_URL = "http://localhost/v1/chat-messages"
DIFY_API_KEY = os.getenv("DIFY_API_KEY")

@csrf_exempt
@require_POST
def ai_chat(request):
    body = json.loads(request.body)
    message = body.get("message", "").strip()
    conversation_id = body.get("conversation_id")

    payload = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking",
        "user": f"user-{request.user.id if request.user.is_authenticated else 'guest'}"
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    return JsonResponse({
        "answer": data.get("answer", ""),
        "conversation_id": data.get("conversation_id", "")
    })