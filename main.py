import asyncio
from pathlib import Path
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

def read_token(path: str | Path) -> str:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")

    token = path.read_text(encoding="utf-8").strip()

    if not token:
        raise ValueError("Token file is empty")

    return token

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = read_token("bot_token.txt")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Hello!")

async def handler(event: dict, context):
    body: str = event ["body"]

    update_data = json.loads(body) if body else {}

    await dp.feed_update(
        bot,
        Update.model_validate(update_data)
    )

    return {"statusCode": 200, 
            "body": ""}

@dp.message()
async def catch_all(message: Message):
    logging.info(
        "Got message: chat_id=%s type=%s text=%r",
        message.chat.id,
        message.content_type,
        message.text,
    )
    await message.answer("Got it. Type /start")

async def main():
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())