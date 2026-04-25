import json
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.user_manager import get_user_data, update_user_balance, check_and_give_bonus
from utils.cards import get_random_card, calculate_score, format_cards
from utils.escape import escape_html

router = Router()

def get_bj_keyboard(game_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Взять карту", callback_data=f"bj_hit_{game_id}")
    builder.button(text="Хватит", callback_data=f"bj_stand_{game_id}")
    return builder.as_markup()

active_games = {}

@router.message(Command("bj"))
async def cmd_bj(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = escape_html(message.from_user.full_name)

    data = await get_user_data(chat_id, user_id, full_name)
    if data.get('is_banned', False):
        await message.answer("Вы забанены и не можете играть.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ставку: <code>/bj 100</code>")
        return

    try:
        bet = int(args[1])
        if bet < 100:
            await message.answer("Минимальная ставка — 100 сыроежек.")
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

    await update_user_balance(chat_id, user_id, -bet)

    game_id = f"{chat_id}_{user_id}_{message.message_id}"

    player_cards = [get_random_card(), get_random_card()]
    dealer_cards = [get_random_card()]

    player_score = calculate_score(player_cards)
    dealer_score = calculate_score(dealer_cards)

    if player_score == 21:
        profit = int(bet * 1.5)
        is_vip = data.get('is_vip', False)
        vip_bonus_text = ""
        if is_vip:
            vip_profit_bonus = int(profit * 0.1)
            profit += vip_profit_bonus
            vip_bonus_text = f" (👑 VIP бонус: +{vip_profit_bonus})"

        win_amount = bet + profit
        await update_user_balance(chat_id, user_id, win_amount)
        text = (
            f"{bonus_text}<b>БЛЭКДЖЕК!</b> Вы выиграли {profit} сыроежек{vip_bonus_text}.\n\n"
            f"Ваши карты: {format_cards(player_cards)} (21)\n"
            f"Карты дилера: {format_cards(dealer_cards)} ({dealer_score})"
        )
        await message.answer(text)
        return

    active_games[game_id] = {
        'user_id': user_id,
        'chat_id': chat_id,
        'full_name': full_name,
        'bet': bet,
        'player_cards': player_cards,
        'dealer_cards': dealer_cards
    }

    text = (
        f"{bonus_text}Играет: {full_name} | Ставка: {bet}\n\n"
        f"Ваши карты: {format_cards(player_cards)} ({player_score})\n"
        f"Карты дилера: {format_cards(dealer_cards)} и 🂠 (?)"
    )

    await message.answer(text, reply_markup=get_bj_keyboard(game_id))

@router.callback_query(F.data.startswith("bj_hit_"))
async def process_bj_hit(callback: types.CallbackQuery):
    game_id = callback.data.replace("bj_hit_", "")
    game = active_games.get(game_id)
    if not game:
        await callback.answer("Эта игра уже завершена или не найдена.", show_alert=True)
        return

    if callback.from_user.id != game['user_id']:
        await callback.answer("Это не ваша игра!", show_alert=True)
        return

    game['player_cards'].append(get_random_card())
    player_score = calculate_score(game['player_cards'])

    if player_score > 21:
        game = active_games.pop(game_id, None)
        if not game:
            await callback.answer()
            return
        text = (
            f"<b>Перебор!</b> Вы проиграли {game['bet']} сыроежек.\n\n"
            f"Игрок: {game['full_name']}\n"
            f"Ваши карты: {format_cards(game['player_cards'])} ({player_score})\n"
            f"Карты дилера: {format_cards(game['dealer_cards'])} ({calculate_score(game['dealer_cards'])})"
        )
        await callback.message.edit_text(text)
    elif player_score == 21:
        game = active_games.pop(game_id, None)
        if game:
            await finish_dealer_turn(callback, game)
    else:
        text = (
            f"Играет: {game['full_name']} | Ставка: {game['bet']}\n\n"
            f"Ваши карты: {format_cards(game['player_cards'])} ({player_score})\n"
            f"Карты дилера: {format_cards(game['dealer_cards'])} и 🂠 (?)"
        )
        await callback.message.edit_text(text, reply_markup=get_bj_keyboard(game_id))

    await callback.answer()

@router.callback_query(F.data.startswith("bj_stand_"))
async def process_bj_stand(callback: types.CallbackQuery):
    game_id = callback.data.replace("bj_stand_", "")
    game = active_games.get(game_id)
    if not game:
        await callback.answer("Эта игра уже завершена или не найдена.", show_alert=True)
        return

    if callback.from_user.id != game['user_id']:
        await callback.answer("Это не ваша игра!", show_alert=True)
        return

    game = active_games.pop(game_id, None)
    if game:
        await finish_dealer_turn(callback, game)

    await callback.answer()

async def finish_dealer_turn(callback: types.CallbackQuery, game: dict):
    player_score = calculate_score(game['player_cards'])
    dealer_cards = game['dealer_cards']

    while calculate_score(dealer_cards) <= 16:
        dealer_cards.append(get_random_card())

    dealer_score = calculate_score(dealer_cards)

    bet = game['bet']
    user_id = game['user_id']
    chat_id = game['chat_id']

    data = await get_user_data(chat_id, user_id)
    is_vip = data.get('is_vip', False)

    if dealer_score > 21 or player_score > dealer_score:
        profit = bet
        vip_bonus_text = ""
        if is_vip:
            vip_profit_bonus = int(profit * 0.1)
            profit += vip_profit_bonus
            vip_bonus_text = f" (👑 VIP бонус: +{vip_profit_bonus})"

        result = f"<b>Вы выиграли!</b> (+{profit} сыроежек){vip_bonus_text}"
        await update_user_balance(chat_id, user_id, bet + profit)
    elif player_score < dealer_score:
        result = f"<b>Вы проиграли!</b> (-{bet} сыроежек)"
    else:
        result = "<b>Ничья!</b> (Возврат ставки)"
        await update_user_balance(chat_id, user_id, bet)

    text = (
        f"{result}\n\n"
        f"Игрок: {game['full_name']}\n"
        f"Ваши карты: {format_cards(game['player_cards'])} ({player_score})\n"
        f"Карты дилера: {format_cards(dealer_cards)} ({dealer_score})"
    )

    await callback.message.edit_text(text)
