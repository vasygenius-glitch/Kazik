import asyncio
import logging
import sys
import os

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

    # Важно: Чтобы избежать ошибки 503 от aiohttp_socks, мы отключаем SSL проверку
    # и используем встроенный параметр proxy.

    proxy_url = "http://proxy.server:3128"

    # Мы создаем AiohttpSession с явным прокси. Aiogram сам подхватит его.
    # Но мы должны передать аргументы для aiohttp.TCPConnector, чтобы отключить SSL.
    from aiohttp import BasicAuth

    # Проверка на PythonAnywhere:
    if "PYTHONANYWHERE_SITE" in os.environ or "Goga22doga" in __file__:
        print(f"Запуск на PythonAnywhere, настраиваю прокси: {proxy_url}")

        # Monkey patch для aiogram, чтобы он НЕ использовал aiohttp_socks
        import aiogram.client.session.aiohttp as aiohttp_session_module
        aiohttp_session_module.aiohttp_socks = None

        session = AiohttpSession(proxy=proxy_url)
    else:
        session = AiohttpSession()

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp.message.outer_middleware(WhitelistMiddleware())
    dp.callback_query.outer_middleware(WhitelistMiddleware())
    register_all_handlers(dp)

    print("Бот запускается...")

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
