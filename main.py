import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, FIREBASE_KEY_PATH
from db import init_db
from handlers_init import register_all_handlers
from whitelist_middleware import WhitelistMiddleware

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp = Dispatcher()

    try:
        init_db(FIREBASE_KEY_PATH)
    except Exception as e:
        print(f"Ошибка БД: {e}")

    # Hugging Face Spaces workaround: Force IPv4 to prevent ClientConnectorError
    import aiohttp
    import socket
    # Отключаем IPv6, заставляя TCPConnector использовать только IPv4.
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)

    # Создаем сессию с явным коннектором и таймаутом
    session = AiohttpSession()
    session._connector_type = aiohttp.TCPConnector
    session._connector_init = {"family": socket.AF_INET, "ssl": False}
    session._should_reset_connector = True
    session.timeout = 60 # Жесткий таймаут для Telegram API

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
        me = await bot.get_me()
        print(f"✅ Соединение с Telegram API установлено! Бот: @{me.username}")
        # Удаляем вебхуки, чтобы поллинг не конфликтовал (если они случайно были)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Начинаю слушать сообщения (polling)...")
    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")

    # Бесконечный цикл поллинга для защиты от падений сети на Hugging Face Spaces
    while True:
        try:
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"❌ Ошибка сети/поллинга (переподключение через 5с): {e}")
            await asyncio.sleep(5)

    await bot.session.close()

if __name__ == "__main__":
    # Flask сервер для keep-alive на Hugging Face Spaces (порт 7860)
    import threading
    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Бот работает круглосуточно на Hugging Face Spaces!"

    def run_flask():
        # Hugging Face Spaces требует чтобы приложение слушало 0.0.0.0:7860
        app.run(host="0.0.0.0", port=7860, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
