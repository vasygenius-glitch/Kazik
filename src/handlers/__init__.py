from aiogram import Dispatcher
from .economy import router as economy_router
from .blackjack import router as blackjack_router
from .roulette import router as roulette_router
from .shop import router as shop_router
from .creator import router as creator_router
from .slots import router as slots_router
from .cups import router as cups_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(economy_router)
    dp.include_router(blackjack_router)
    dp.include_router(roulette_router)
    dp.include_router(shop_router)
    dp.include_router(creator_router)
    dp.include_router(slots_router)
    dp.include_router(cups_router)
