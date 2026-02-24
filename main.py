import asyncio
import logging
import json
from pprint import pprint
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command

from config import read_env_var

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

BOT_TOKEN = read_env_var("BOT_TOKEN")
try:
    ADMIN_ID = int(read_env_var("ADMIN_ID"))
except (KeyError, ValueError, FileNotFoundError) as exc:
    ADMIN_ID = None
    logging.warning("ADMIN_ID is not configured correctly: %s", exc)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shutdown_requested = asyncio.Event()



@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Hello!")


@dp.message(Command("stop"))
async def handle_stop(message: Message):
    if ADMIN_ID is None:
        await message.answer("ADMIN_ID is not configured.")
        return

    if not message.from_user or message.from_user.id != ADMIN_ID:
        await message.answer("Access denied.")
        return

    logging.info("Shutdown requested by admin_id=%s", message.from_user.id)
    await message.answer("Stopping bot...")
    shutdown_requested.set()


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
    # await message.answer("Got it. Type /start")
    await message.answer(message.text)

async def main():
    logging.info("Bot started")
    polling_task = asyncio.create_task(dp.start_polling(bot))
    shutdown_task = asyncio.create_task(shutdown_requested.wait())

    done, pending = await asyncio.wait(
        {polling_task, shutdown_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    if shutdown_task in done and not polling_task.done():
        logging.info("Stopping polling")
        await dp.stop_polling()

    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    await polling_task

if __name__ == "__main__":
    asyncio.run(main())
