import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command


def read_token(path: str | Path) -> str:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")

    token = path.read_text(encoding="utf-8").strip()

    if not token:
        raise ValueError("Token file is empty")

    return token

BOT_TOKEN = read_token("bot_token.txt")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Hello!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())