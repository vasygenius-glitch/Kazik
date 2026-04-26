from aiogram import Router, F, types
from aiogram.filters import Command
from database.user_manager import get_user_data, update_user_balance, check_and_give_bonus, update_user_field, get_top_users
from utils.escape import escape_html
import time
import secrets

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    # Инициализируем данные пользователя (при первом запуске выдается стартовый баланс)
    await get_user_data(chat_id, user_id, full_name)

    text = (
        f"👋 <b>Привет, {full_name}!</b>\n\n"
        "Я бот для экономики и мини-игр! Твой стартовый баланс составляет <b>500</b> сыроежек.\n\n"
        "Пиши <code>/help</code> чтобы увидеть список всех команд."
    )
    await message.answer(text)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📜 <b>Список базовых команд:</b>\n\n"
        "💰 <b>Экономика:</b>\n"
        "<code>/balance</code> — Проверить свой баланс и статус.\n"
        "<code>/top</code> — Топ-10 богачей чата.\n"
        "<code>/shop</code> — Открыть магазин бизнесов.\n"
        "<code>/bonus</code> — Ежедневный бонус и пассивный доход.\n"
        "<code>/work</code> — Легальный заработок.\n"
        "<code>/crime</code> — Рискованный заработок (ограбление).\n"
        "<code>/pay &lt;сумма&gt; &lt;reply&gt;</code> — Перевод денег.\n\n"
        "🎰 <b>Игры:</b>\n"
        "<code>/slots &lt;ставка&gt;</code> — Игровые автоматы.\n"
        "<code>/blackjack &lt;ставка&gt;</code> — Игра в 21.\n"
        "<code>/roulette &lt;ставка&gt;</code> — Рулетка.\n"
        "<code>/cups &lt;ставка&gt;</code> — Наперстки.\n"
    )
    await message.answer(text)

@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    balance = data.get('balance', 0)
    is_vip = data.get('is_vip', False)

    vip_icon = " 👑 VIP" if is_vip else ""
    await message.answer(f"💰 Ваш баланс: <b>{balance}</b> сыроежек.{vip_icon}")

@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    chat_id = message.chat.id
    sender_id = message.from_user.id
    sender_name = escape_html(message.from_user.full_name)

    sender_data = await get_user_data(chat_id, sender_id, sender_name)
    if sender_data.get('is_banned', False):
        await message.answer("Вы забанены и не можете переводить деньги.")
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение человека, которому хотите перевести сыроежки.")
        return

    target_user = message.reply_to_message.from_user
    target_name = escape_html(target_user.full_name)
    if target_user.is_bot:
        await message.answer("Нельзя переводить деньги ботам.")
        return

    if target_user.id == message.from_user.id:
        await message.answer("Нельзя перевести деньги самому себе.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите сумму: <code>/pay 100</code>")
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            await message.answer("Сумма должна быть положительной.")
            return
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Сумма должна быть положительным числом.")
        return

    total_cost = int(amount * 1.1)
    commission = total_cost - amount

    if sender_data.get('balance', 0) < total_cost:
        await message.answer(f"Недостаточно средств. Для перевода {amount} нужно {total_cost} сыроежек (комиссия 10%).")
        return

    try:
        admins = await message.chat.get_administrators()
        human_admins = [admin.user.id for admin in admins if not admin.user.is_bot]
    except Exception as e:
        human_admins = []

    if not human_admins:
        human_admins = [sender_id]

    commission_per_admin = commission // len(human_admins)

    await update_user_balance(chat_id, sender_id, -total_cost)

    await get_user_data(chat_id, target_user.id, target_name)
    await update_user_balance(chat_id, target_user.id, amount)

    for admin_id in human_admins:
        await get_user_data(chat_id, admin_id)
        await update_user_balance(chat_id, admin_id, commission_per_admin)

    await message.answer(
        f"💸 Успешный перевод!\n"
        f"Отправлено: {amount} сыроежек пользователю {target_name}.\n"
        f"Комиссия: {commission} сыроежек (распределена между {len(human_admins)} администраторами)."
    )

@router.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    success, amount = await check_and_give_bonus(chat_id, user_id, full_name)
    if success:
        await message.answer(f"🎁 Вы успешно получили бонус и пассивный доход в размере <b>{amount}</b> сыроежек!")
    else:
        await message.answer("❌ Вы уже получали бонус за последние 24 часа. Приходите позже!")

@router.message(Command("work"))
async def cmd_work(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return await message.answer("Вы забанены и не можете работать.")

    last_work = data.get('last_work_time', 0)
    current_time = time.time()

    # 1 hour cooldown for work
    if current_time - last_work < 3600:
        remain = int(3600 - (current_time - last_work))
        mins, secs = divmod(remain, 60)
        return await message.answer(f"⏳ Вы устали. Отдохните еще {mins} минут и {secs} секунд.")

    rand = secrets.SystemRandom()
    earnings = rand.randint(50, 250)

    await update_user_field(chat_id, user_id, 'last_work_time', current_time)
    await update_user_balance(chat_id, user_id, earnings)

    jobs = [
        "убрали мусор на улице",
        "помогли бабушке перейти дорогу",
        "доставили посылку",
        "поработали на стройке",
        "помыли окна"
    ]
    job = rand.choice(jobs)

    await message.answer(f"💼 Вы <b>{job}</b> и заработали <b>{earnings}</b> сыроежек!")

@router.message(Command("crime"))
async def cmd_crime(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        return await message.answer("Вы забанены и не можете совершать преступления.")

    last_crime = data.get('last_crime_time', 0)
    current_time = time.time()

    # 2 hours cooldown for crime
    if current_time - last_crime < 7200:
        remain = int(7200 - (current_time - last_crime))
        mins, secs = divmod(remain, 60)
        hours, mins = divmod(mins, 60)
        return await message.answer(f"⏳ Полиция все еще ищет вас. Залягте на дно еще {hours} ч. {mins} мин.")

    await update_user_field(chat_id, user_id, 'last_crime_time', current_time)

    rand = secrets.SystemRandom()
    if rand.random() < 0.4: # 40% chance of success
        earnings = rand.randint(200, 800)
        await update_user_balance(chat_id, user_id, earnings)
        crimes = ["ограбили магазин", "угнали велосипед", "украли кошелек", "взломали банкомат"]
        crime = rand.choice(crimes)
        await message.answer(f"🥷 Вы успешно <b>{crime}</b> и получили <b>{earnings}</b> сыроежек!")
    else:
        fine = rand.randint(100, 300)
        balance = data.get('balance', 0)
        if balance < fine:
            fine = balance
        await update_user_balance(chat_id, user_id, -fine)
        await message.answer(f"🚔 Вас поймала полиция! Вы заплатили штраф в размере <b>{fine}</b> сыроежек.")

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    chat_id = message.chat.id
    top_users = await get_top_users(chat_id, limit=10)

    if not top_users:
        return await message.answer("🏆 Топ игроков пуст.")

    text = "🏆 <b>Топ-10 богачей чата:</b>\n\n"
    for i, user in enumerate(top_users, start=1):
        vip_icon = " 👑" if user.get('is_vip') else ""
        text += f"{i}. {escape_html(user.get('full_name', 'Unknown'))}{vip_icon} — <b>{user.get('balance', 0)}</b> сыроежек\n"

    await message.answer(text)
