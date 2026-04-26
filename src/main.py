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

    # Сначала пытаемся запустить бота БЕЗ прокси
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.message.outer_middleware(WhitelistMiddleware())
    dp.callback_query.outer_middleware(WhitelistMiddleware())
    register_all_handlers(dp)

    print("Попытка запуска без прокси...")

    try:
        # Быстрая проверка токена, если упадет - значит нужен прокси
        await bot.get_me()
        print("Бот успешно запущен (без прокси)!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Запуск без прокси не удался ({e}). Пробуем через прокси PythonAnywhere...")
        await bot.session.close()

        # Пересоздаем бота с прокси
        proxy_url = "http://proxy.server:3128"
        session = AiohttpSession(proxy=proxy_url)
        bot_proxy = Bot(
            token=BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        print(f"Бот запущен через прокси: {proxy_url}")
        try:
            await dp.start_polling(bot_proxy)
        finally:
            await bot_proxy.session.close()
    finally:
        if bot:
            await bot.session.close()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
