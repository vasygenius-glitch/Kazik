import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN, FIREBASE_KEY_PATH
from database.db import init_db
from handlers import register_all_handlers

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Инициализация БД
    init_db(FIREBASE_KEY_PATH)

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    register_all_handlers(dp)

    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
