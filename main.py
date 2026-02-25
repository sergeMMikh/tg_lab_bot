import asyncio
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command

from config import read_env_var, read_env_var_optional
from llm_adapter import LLMAdapter

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

try:
    LLM_API_KEY = read_env_var("OPENAI_API_KEY")
except (KeyError, ValueError, FileNotFoundError) as exc:
    LLM_API_KEY = None
    logging.warning("OPENAI_API_KEY is not configured: %s", exc)

llm_adapter = (
    LLMAdapter(
        api_key=LLM_API_KEY,
        model=read_env_var_optional("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
        base_url=read_env_var_optional("OPENAI_BASE_URL", "https://api.openai.com/v1")
        or "https://api.openai.com/v1",
        system_prompt=read_env_var_optional("LLM_SYSTEM_PROMPT"),
        memory_size=int(read_env_var_optional("LLM_MEMORY_SIZE", "8") or "8"),
        rate_limit_max_requests=int(
            read_env_var_optional("LLM_RATE_LIMIT_MAX_REQUESTS", "5") or "5"
        ),
        rate_limit_window_seconds=int(
            read_env_var_optional("LLM_RATE_LIMIT_WINDOW_SECONDS", "60") or "60"
        ),
        max_input_chars=int(read_env_var_optional("LLM_MAX_INPUT_CHARS", "1500") or "1500"),
        max_output_chars=int(
            read_env_var_optional("LLM_MAX_OUTPUT_CHARS", "1200") or "1200"
        ),
    )
    if LLM_API_KEY
    else None
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shutdown_requested = asyncio.Event()



@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Привет! Напиши сообщение, и я отвечу через LLM.")


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
    if not message.text:
        await message.answer("Я пока поддерживаю только текстовые сообщения.")
        return

    if llm_adapter is None:
        await message.answer("LLM не настроен. Добавьте OPENAI_API_KEY в .env")
        return

    user_id = message.from_user.id if message.from_user else message.chat.id
    reply_text = await asyncio.to_thread(llm_adapter.reply, user_id, message.text)
    await message.answer(reply_text)

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
