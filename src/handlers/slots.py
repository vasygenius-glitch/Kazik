import asyncio
import random
from aiogram import Router, types
from aiogram.filters import Command

from database.user_manager import get_user_data, update_user_balance, check_and_give_bonus
from utils.escape import escape_html

router = Router()

EMOJIS = ["🍒", "🍋", "🍉", "🍇", "🔔", "💎", "7️⃣"]

@router.message(Command("slots"))
async def cmd_slots(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        await message.answer("Вы забанены и не можете играть.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ставку: <code>/slots 100</code>")
        return

    try:
        bet = int(args[1])
        if bet < 10:
            await message.answer("Минимальная ставка — 10 сыроежек.")
            return
    except ValueError:
        await message.answer("Ставка должна быть числом.")
        return

    bonus_given, bonus_amount = await check_and_give_bonus(chat_id, user_id, full_name)
    bonus_text = f"🎁 Вы получили ежедневный бонус: {bonus_amount} сыроежек!\n" if bonus_given else ""

    # Re-fetch data after bonus check
    data = await get_user_data(chat_id, user_id, full_name)
    balance = data.get('balance', 0)

    if balance - bet < -5000:
        await message.answer(f"{bonus_text}Ваш кредитный лимит (-5000) исчерпан. Пополните баланс.")
        return

    # Deduct bet
    await update_user_balance(chat_id, user_id, -bet)

    # Initial message
    msg = await message.answer(f"{bonus_text}🎰 <b>Слоты крутятся...</b>\n\n[ ❓ | ❓ | ❓ ]")

    # Animation
    for _ in range(3):
        await asyncio.sleep(0.5)
        temp_slots = [random.choice(EMOJIS) for _ in range(3)]
        try:
            await msg.edit_text(f"{bonus_text}🎰 <b>Слоты крутятся...</b>\n\n[ {temp_slots[0]} | {temp_slots[1]} | {temp_slots[2]} ]")
        except:
            pass # Ignore edit errors if any

    await asyncio.sleep(0.5)

    # Final result
    final_slots = [
        random.choice(EMOJIS),
        random.choice(EMOJIS),
        random.choice(EMOJIS)
    ]

    profit = 0
    multiplier_text = ""

    # Logic
    if final_slots[0] == final_slots[1] == final_slots[2]:
        if final_slots[0] == "7️⃣":
            profit = bet * 10
            multiplier_text = "ДЖЕКПОТ! x10"
        else:
            profit = bet * 5
            multiplier_text = "Три в ряд! x5"
    elif final_slots[0] == final_slots[1] or final_slots[1] == final_slots[2] or final_slots[0] == final_slots[2]:
        profit = int(bet * 1.5)
        multiplier_text = "Пара! x1.5"

    result_text = ""
    is_vip = data.get('is_vip', False)
    vip_bonus_text = ""

    if profit > 0:
        if is_vip:
            vip_profit_bonus = int(profit * 0.1)
            profit += vip_profit_bonus
            vip_bonus_text = f" (👑 VIP бонус: +{vip_profit_bonus})"

        await update_user_balance(chat_id, user_id, bet + profit)
        result_text = f"<b>Вы выиграли {profit} сыроежек!</b> {multiplier_text}{vip_bonus_text}"
    else:
        result_text = f"<b>Вы проиграли {bet} сыроежек.</b>"

    final_text = (
        f"{bonus_text}"
        f"🎰 <b>Слоты остановились</b>\n\n"
        f"[ {final_slots[0]} | {final_slots[1]} | {final_slots[2]} ]\n\n"
        f"{result_text}"
    )

    try:
        await msg.edit_text(final_text)
    except:
        await message.answer(final_text)
