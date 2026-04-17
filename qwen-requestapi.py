#!/usr/bin/env python3
import asyncio
import aiohttp
import uuid
import json
import time

BASE_URL = "https://chat.qwen.ai"
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJhYmFiMmQ3LTJjMjQtNDI1Ny04NTVmLTM4YmMyOTdhZmI3NCIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzc1MjgzMTE5LCJleHAiOjE3Nzc4NzU4NzZ9.zwyRzRIDtCbVUpTl-mvEkcQzUa8JakQN20jaOnRi9rY"
COOKIE_STR = "x-ap=eu-central-1; acw_tc=0a06abd717752830692835583e23985d02f06101ed553dd91fc56cd9b17899; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJhYmFiMmQ3LTJjMjQtNDI1Ny04NTVmLTM4YmMyOTdhZmI3NCIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzc1MjgzMTE5LCJleHAiOjE3Nzc4NzU4NzZ9.zwyRzRIDtCbVUpTl-mvEkcQzUa8JakQN20jaOnRi9rY"

COOKIES = {}
for item in COOKIE_STR.split("; "):
    if "=" in item:
        k, v = item.split("=", 1)
        COOKIES[k] = v

HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; NX666J Build/SKQ1.211113.001) AliApp(QWENCHAT/1.19.1) AppType/Release AplusBridgeLite",
    "Connection": "Keep-Alive",
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "X-Platform": "android",
    "Authorization": AUTH_TOKEN,
    "source": "app",
    "Accept-Language": "en-US",
    "Accept-Charset": "UTF-8",
}

def gen_id(): return str(uuid.uuid4())

async def create_new_chat(session):
    h = HEADERS.copy()
    h["x-request-id"] = gen_id()
    h["Content-Type"] = "application/json"
    async with session.post(f"{BASE_URL}/api/v2/chats/new",
                            headers=h, json={"chat_mode": "normal", "project_id": ""},
                            cookies=COOKIES) as resp:
        data = await resp.json()
        return data['data']['id']

async def send_message(session, chat_id, user_message, parent_id=""):
    h = HEADERS.copy()
    h.update({
        "x-request-id": gen_id(),
        "Accept": "*/*,text/event-stream",
        "Accept-Encoding": "gzip, deflate",
        "Accept-language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-store",
        "Content-Type": "application/json; charset=UTF-8",
    })

    msg = {
        "chat_type": "t2t", "content": user_message, "role": "user",
        "feature_config": {
            "output_schema": "phase", "thinking_enabled": True,
            "thinking_format": "summary", "auto_thinking": True, "auto_search": True,
        },
        "timestamp": int(time.time()), "sub_chat_type": "t2t",
        "models": ["qwen3.6-plus"], "fid": gen_id(),
        "user_action": "chat", "extra": {"meta": {"subChatType": "t2t"}},
    }
    # نضيف parent_id في الرسالة بس لو عنده قيمة
    if parent_id:
        msg["parentId"] = parent_id
        msg["parent_id"] = parent_id

    payload = {
        "stream": True, "incremental_output": True,
        "chat_id": chat_id, "chat_mode": "normal", "model": "qwen3.6-plus",
        "messages": [msg],
        "timestamp": int(time.time()), "share_id": "", "origin_branch_message_id": "",
    }
    if parent_id:
        payload["parent_id"] = parent_id

    full_reply = ""
    new_parent_id = parent_id

    async with session.post(
        f"{BASE_URL}/api/v2/chat/completions?chat_id={chat_id}",
        headers=h, json=payload, cookies=COOKIES
    ) as resp:
        if resp.status != 200:
            raise Exception(f"خطأ {resp.status}: {await resp.text()}")

        async for line in resp.content:
            line = line.decode('utf-8').strip()
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                obj = json.loads(data_str)

                # ✅ استخراج parent_id من حدث response.created
                if "response.created" in obj:
                    new_parent_id = obj["response.created"].get("parent_id", parent_id)
                    continue

                # ✅ نطبع الـ content بس لو phase == "answer"
                choices = obj.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    if delta.get("phase") == "answer":
                        content = delta.get("content", "")
                        if content:
                            print(content, end="", flush=True)
                            full_reply += content
            except json.JSONDecodeError:
                pass

    print()
    return full_reply, new_parent_id

async def main():
    print("=== Qwen Chat - new = محادثة جديدة, exit = خروج ===")
    async with aiohttp.ClientSession() as session:
        chat_id = await create_new_chat(session)
        print(f"[Chat ID: {chat_id}]")
        parent_id = ""

        loop = asyncio.get_running_loop()
        while True:
            try:
                user_input = await loop.run_in_executor(None, input, "\nأنت: ")
                user_input = user_input.strip()
                if user_input.lower() == "exit":
                    print("وداعاً!")
                    break
                elif user_input.lower() == "new":
                    chat_id = await create_new_chat(session)
                    parent_id = ""
                    print(f"[محادثة جديدة - Chat ID: {chat_id}]")
                    continue
                elif not user_input:
                    continue

                print("Qwen: ", end="")
                _, parent_id = await send_message(session, chat_id, user_input, parent_id)

            except KeyboardInterrupt:
                print("\nتم الإنهاء.")
                break
            except Exception as e:
                print(f"\nخطأ: {e}")

if __name__ == "__main__":
    asyncio.run(main())
