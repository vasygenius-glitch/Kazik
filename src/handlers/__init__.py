from aiogram import Dispatcher
from .economy import router as economy_router
from .blackjack import router as blackjack_router
from .roulette import router as roulette_router
from .shop import router as shop_router
from .creator import router as creator_router
from .slots import router as slots_router
from .cups import router as cups_router

from aiogram import Router
from aiogram.types import Message
from utils.logger import log_message

catch_all_router = Router()
@catch_all_router.message()
async def catch_all(message: Message):
    if message.chat.type in ["group", "supergroup"]:
        text = message.text or message.caption or ""
        media_type = ""
        if message.photo: media_type = "[Фото] "
        elif message.video: media_type = "[Видео] "
        elif message.sticker: media_type = "[Стикер] "
        elif message.voice: media_type = "[Голосовое] "
        elif message.document: media_type = "[Файл] "

        full_text = f"{media_type}{text}"
        if full_text.strip():
            log_message(message.chat.id, message.chat.title or "Unknown", message.from_user.id, message.from_user.full_name, full_text)

def register_all_handlers(dp: Dispatcher):

    dp.include_router(economy_router)
    dp.include_router(blackjack_router)
    dp.include_router(roulette_router)
    dp.include_router(shop_router)
    dp.include_router(creator_router)
    dp.include_router(slots_router)
    dp.include_router(cups_router)
    dp.include_router(catch_all_router)
