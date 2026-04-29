import time
import secrets
from aiogram import Router, types, F, Bot
from db import get_db
from escape import escape_html
from user_manager import get_user_data, update_user_balance
from config import CREATOR_ID

router = Router()

@router.message(F.text.lower().startswith("украсть") | F.text.lower().startswith("/steal"))
async def cmd_steal(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        return await message.answer("Сделайте реплай на сообщение того, кого хотите ограбить.")

    chat_id = message.chat.id
    user_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id

    if user_id == target_id: return await message.answer("Вы не можете украсть у себя.")
    if message.reply_to_message.from_user.is_bot: return await message.answer("У бота денег нет.")

    # Check immunity
    if int(target_id) == int(CREATOR_ID):
        return await message.answer("Невозможно ограбить Создателя!")

    try:
        target_member = await bot.get_chat_member(chat_id, target_id)
        if target_member.status in ['administrator', 'creator']:
            return await message.answer("Невозможно ограбить Администратора!")
    except: pass

    data = await get_user_data(chat_id, user_id)
    last_steal = data.get('last_steal_time', 0)
    current_time = int(time.time())

    if current_time - last_steal < 3600: # 1 hour cooldown
        return await message.answer("Вы уже пытались воровать недавно. Залягте на дно (кулдаун 1 час).")

    from user_manager import update_user_field
    await update_user_field(chat_id, user_id, 'last_steal_time', current_time)

    target_data = await get_user_data(chat_id, target_id)
    target_balance = target_data.get('balance', 0)

    if target_balance <= 0:
        return await message.answer("У этого бедолаги пустые карманы, воровать нечего.")

    rand = secrets.SystemRandom()
    stealth_bonus = data.get('skills', {}).get('stealth', 0) * 0.05
    success_chance = 0.3 + stealth_bonus # Base 30%

    if rand.random() < success_chance:
        steal_amount = int(target_balance * rand.uniform(0.01, 0.05)) # Steal 1-5%
        if steal_amount == 0: steal_amount = 1

        await update_user_balance(chat_id, user_id, steal_amount)
        await update_user_balance(chat_id, target_id, -steal_amount)

        await message.answer(f"🥷 <b>Успех!</b>\nВы незаметно вытащили из кармана <b>{escape_html(message.reply_to_message.from_user.full_name)}</b> сумму в <b>{steal_amount}</b> сыроежек!")
    else:
        penalty = int(target_balance * 0.02) # Penalty 2%
        if penalty == 0: penalty = 50

        user_balance = data.get('balance', 0)
        if user_balance < penalty: penalty = user_balance

        await update_user_balance(chat_id, user_id, -penalty)
        await update_user_balance(chat_id, target_id, penalty)

        await message.answer(f"🚨 <b>Провал!</b>\nВас поймали за руку! В качестве компенсации вы отдаете <b>{penalty}</b> сыроежек жертве.")

# Anti-voice feature (added to group_management.py via next step)



@router.message(F.text.lower().startswith("диктор "))
async def cmd_dictor(message: types.Message):
    question = message.text[7:].strip()
    if not question:
        return

    responses = [
        "Духи говорят, что да.",
        "Шансы крайне малы.",
        "Бесспорно!",
        "Даже не надейся.",
        "Звезды складываются в твою пользу.",
        "Спроси позже, я занят.",
        "Конечно нет!",
        "Это предрешено.",
        "Мои источники говорят 'нет'.",
        "Весьма сомнительно."
    ]

    import secrets
    answer = secrets.choice(responses)
    await message.answer(f"🔮 <b>Диктор отвечает:</b>

{answer}")



# ЛОТЕРЕЯ
active_lotteries = {}

@router.message(Command("lottery"))
async def cmd_lottery(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status not in ['administrator', 'creator'] and int(user_id) != int(CREATOR_ID):
            return await message.answer("Только администраторы могут запускать лотереи.")
    except: return

    args = message.text.split()
    if len(args) < 4:
        return await message.answer("Использование: <code>/lottery [сумма] [кол-во победителей] [минуты]</code>")

    try:
        amount = int(args[1])
        winners_count = int(args[2])
        minutes = int(args[3])
        if amount <= 0 or winners_count <= 0 or minutes <= 0: return
    except: return

    data = await get_user_data(chat_id, user_id)
    if data.get('balance', 0) < amount:
        return await message.answer("У вас недостаточно сыроежек для проведения лотереи.")

    await update_user_balance(chat_id, user_id, -amount)

    import time
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    lottery_id = f"{chat_id}_{int(time.time())}"
    active_lotteries[lottery_id] = {
        'amount': amount,
        'winners_count': winners_count,
        'participants': []
    }

    builder = InlineKeyboardBuilder()
    builder.button(text="Участвовать 🎟", callback_data=f"lottery_join_{lottery_id}")

    msg = await message.answer(
        f"🎉 <b>НОВАЯ ЛОТЕРЕЯ!</b> 🎉

"
        f"Призовой фонд: <b>{amount}</b> сыроежек!
"
        f"Победителей: <b>{winners_count}</b>
"
        f"Итоги через: <b>{minutes}</b> мин.

"
        f"Жмите кнопку ниже, чтобы участвовать!",
        reply_markup=builder.as_markup()
    )

    import asyncio
    async def finish_lottery():
        await asyncio.sleep(minutes * 60)
        lottery_data = active_lotteries.pop(lottery_id, None)
        if not lottery_data: return

        participants = list(set(lottery_data['participants']))
        if not participants:
            await update_user_balance(chat_id, user_id, amount)
            await bot.send_message(chat_id, "😢 Никто не участвовал в лотерее. Деньги возвращены создателю.")
            return

        import secrets
        actual_winners = min(winners_count, len(participants))
        winners = secrets.SystemRandom().sample(participants, actual_winners)

        prize_per_winner = amount // actual_winners

        winners_names = []
        for winner in winners:
            await update_user_balance(chat_id, winner['id'], prize_per_winner)
            winners_names.append(f"<b>{escape_html(winner['name'])}</b>")

        await bot.send_message(
            chat_id,
            f"🎊 <b>ИТОГИ ЛОТЕРЕИ!</b> 🎊

"
            f"Призовой фонд <b>{amount}</b> был разделен между {actual_winners} счастливчиками!

"
            f"Победители:
" + "
".join(winners_names) + f"

"
            f"Каждый получил по <b>{prize_per_winner}</b> сыроежек!"
        )

    asyncio.create_task(finish_lottery())

@router.callback_query(F.data.startswith("lottery_join_"))
async def callback_lottery(callback: types.CallbackQuery):
    lottery_id = callback.data.replace("lottery_join_", "")

    if lottery_id not in active_lotteries:
        return await callback.answer("Эта лотерея уже завершена!", show_alert=True)

    participants = active_lotteries[lottery_id]['participants']

    for p in participants:
        if p['id'] == callback.from_user.id:
            return await callback.answer("Вы уже участвуете!", show_alert=True)

    participants.append({'id': callback.from_user.id, 'name': callback.from_user.full_name})
    await callback.answer("Вы успешно зарегистрировались в лотерее!", show_alert=True)

    # Update button text to show participants count
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Участвовать 🎟 ({len(participants)})", callback_data=f"lottery_join_{lottery_id}")

    try:
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except: pass
