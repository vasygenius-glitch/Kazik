from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from database.whitelist import get_whitelist, log_unauthorized_chat
from bot.config import CREATOR_ID

class WhitelistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        chat = event.message.chat if isinstance(event, CallbackQuery) else event.chat

        # Разрешить личные сообщения с ботом (для админа и т.д.)
        if chat.type == "private":
            return await handler(event, data)

        whitelist = await get_whitelist()

        if chat.id not in whitelist:
            # Логируем попытку использования
            is_new = await log_unauthorized_chat(chat.id, chat.title or "Unknown")

            # Если это первое использование в этом чате, отправляем уведомление админу
            if is_new and CREATOR_ID and CREATOR_ID != 0:
                try:
                    await event.bot.send_message(
                        chat_id=CREATOR_ID,
                        text=(
                            f"⚠️ <b>Бот добавлен или использован в неразрешенной группе!</b>\n\n"
                            f"Название: <b>{chat.title}</b>\n"
                            f"ID группы: <code>{chat.id}</code>\n\n"
                            f"<i>Бот игнорирует команды в этом чате. Чтобы разрешить, введите:</i>\n"
                            f"<code>/allow {chat.id}</code>"
                        )
                    )
                except Exception:
                    pass

            # Блокируем дальнейшую обработку
            return

        return await handler(event, data)
