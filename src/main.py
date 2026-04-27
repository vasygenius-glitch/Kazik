import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from bot.config import BOT_TOKEN, FIREBASE_KEY_PATH
from database.db import init_db
from handlers import register_all_handlers
from handlers.whitelist_middleware import WhitelistMiddleware

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp = Dispatcher()

    try:
        await init_db()
    except Exception as e:
        print(f"Ошибка БД: {e}")

    # Стандартная сессия без прокси. Hugging Face Spaces разрешает любые запросы.
    session = AiohttpSession()

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp.message.outer_middleware(WhitelistMiddleware())
    dp.callback_query.outer_middleware(WhitelistMiddleware())
    register_all_handlers(dp)

    print("Бот запускается на Hugging Face Spaces...")

    try:
        await bot.get_me()
        print("✅ Соединение с Telegram API установлено!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка соединения: {e}")
    finally:
        await bot.session.close()
        from database.db import close_db
        await close_db()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
