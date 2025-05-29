import os
import requests
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Header, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage
from pydantic import BaseModel

# LINE Bot 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# Dify 設定
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL")

headers = {
    "Authorization": f"Bearer {DIFY_API_KEY}",
    "Content-Type": "application/json"
}

router = APIRouter(
    tags=["chatbot"],
    responses={404: {"description": "Not found"}},
)

@router.post("/webhook")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="chatbot handle body error.")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    user_input = event.message.text
    reply_text = ask_dify(user_input)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def ask_dify(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "query": user_message,
        "inputs": {
            "sys.query": user_message,
            "1742898316566.text": "一般的には〜という見方が多いようです。",
            "17482722005320.text": "OK",
            "context": ""
        }
    }

    try:
        response = requests.post(f"{DIFY_BASE_URL}/chat-messages", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("answer", "すみません、うまく返答できませんでした。")
    except Exception as e:
        print(f"Dify API error: {e}")
        return "Difyとの通信に失敗しました。"
