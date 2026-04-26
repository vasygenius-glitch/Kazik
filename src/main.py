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
        init_db(FIREBASE_KEY_PATH)
    except Exception as e:
        print(f"Ошибка БД: {e}")

    # Настройка прокси для PythonAnywhere через переменные окружения
    # Это заставит aiohttp использовать нативный прокси, минуя глючные SOCKS коннекторы
    os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
    os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"

    # Используем trust_env=True, чтобы aiohttp подхватил настройки из os.environ
    from aiohttp import ClientSession, TCPConnector

    # Отключаем ssl проверку, так как прокси PA иногда ругается на сертификаты
    connector = TCPConnector(ssl=False)
    client_session = ClientSession(connector=connector, trust_env=True)
    session = AiohttpSession(session=client_session)

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp.message.outer_middleware(WhitelistMiddleware())
    dp.callback_query.outer_middleware(WhitelistMiddleware())
    register_all_handlers(dp)

    print("Бот запускается через системный прокси PythonAnywhere...")

    try:
        await bot.get_me()
        print("✅ Соединение с Telegram API установлено!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка соединения: {e}")
    finally:
        await bot.session.close()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
