
import requests
import json
from decouple import config

DIFY_API_KEY = config('DIFY_API_KEY')
print(DIFY_API_KEY)

url = "http://localhost/v1/chat-messages"
headers = {
    "Authorization": f"Bearer {DIFY_API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "inputs": {},
    "query": "你好！介绍下你自己。",
    "response_mode": "streaming",
    "user": "shen-test-001",
}

# with requests.post(url, headers=headers, jsoAn=payload, stream=True) as r:
#     # print(r.status_code, r.headers.get("Content-Type"))
#     for line in r.iter_lines(decode_unicode=True):
#         if line:
#             print(line)

with requests.post(url, headers=headers, json=payload, stream=True) as r:
    r.raise_for_status()

    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        # 只处理 data: 开头的行
        if line.startswith("data: "):
            raw = line[6:]
            try:
                event_data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            event_type = event_data.get("event")
            # 只打印流式文本片段
            if event_type == "message":
                print(event_data.get("answer", ""), end="", flush=True)
    print()


