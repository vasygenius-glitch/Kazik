import asyncio
import logging
import sys

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN, FIREBASE_KEY_PATH
from database.db import init_db
from handlers import register_all_handlers
from handlers.whitelist_middleware import WhitelistMiddleware

async def main():
    # Настройка логов
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Инициализация диспетчера
    dp = Dispatcher()

    # Инициализация БД (если тут будет ошибка - пиши, настроим прокси и для базы)
    try:
        init_db(FIREBASE_KEY_PATH)
    except Exception as e:
        print(f"Ошибка БД: {e}")

    # Настройка прокси для PythonAnywhere
    proxy_url = "http://proxy.server:3128"
    session = AiohttpSession(proxy=proxy_url)

    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Подключаем middleware
    dp.message.outer_middleware(WhitelistMiddleware())
    dp.callback_query.outer_middleware(WhitelistMiddleware())

    # Регистрируем хендлеры
    register_all_handlers(dp)

    print(f"Бот запущен через прокси: {proxy_url}")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
