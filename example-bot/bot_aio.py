import os
import traceback

import requests
import aiogram
from aiogram import types

import logging
from urllib.parse import quote
import threading
import traceback
import base64
import time
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

base_url = os.environ["TADA_API_BASE_URL"]
company_token = os.environ["TADA_API_COMPANY_TOKEN"]
token = os.environ['TELEGRAM_TOKEN']


bot = aiogram.Bot(token)

dp = aiogram.Dispatcher(bot)

user_database = {}


def create_user_kb(buttons: list[str], conversation_id: int):
    """
    Создаем клавиатуру для пользователя, с переданным списком кнопок
    из АПИ, Обрезаем
    """
    keyboard = types.InlineKeyboardMarkup()

    i = 0
    for u in buttons or []:
        try:
            keyboard.add(types.InlineKeyboardButton(
                u, callback_data=f"tree_{conversation_id}_{i}"))
            i += 1
        except Exception as e:
            print(traceback.format_exc())
            pass

    return keyboard


@dp.message_handler(commands=["add_rule"])
async def add_rule_bot(message: types.Message):

    words = message.text.replace("/add_rule ", "")

    for word in words.split():
        response = requests.get(base_url + "/add_filter?token=" +
                                company_token + "&filter=" + str(word).lower()).json()

        if response['status'] == "SUCCESS":
            await message.answer(f"Правило добавлено\nID: {response['rule_id']}")


@dp.message_handler(commands=["archive_rule"])
async def archive_filter_handler(message: types.Message):

    id_ = message.text.replace("/archive_rule ", "")

    if not id_.isdigit():
        return await message.answer("Это не целое число!")

    response = requests.get(
        base_url + "/archive_filter?token=" + company_token + "&rule_id=" + id_).json()

    if response['status'] == 'SUCCESS':
        return await message.answer("Правило удалено!")

    await message.answer("Ошибка!")


@dp.message_handler()
async def all_text_hander(message: types.Message):

    text = message.text
    user_id = message.chat.id

    state = user_database.get(user_id)
    # response = None

    # если состояний нет или пользователь сбрасывает состояние
    if not state or text.lower() in ["меню", "/start", "/reset", "/restart"]:
        url = f"{base_url}/new_conversation?user_id={user_id}&token={company_token}"
        print(url)
        response = requests.post(url).json()
        print(response)

        # создаем текущее состояние пользователя в словаре user_database,
        # в котором будут находиться ID диалога (с АПИ) и кнопки пользователя
        state = user_database[user_id] = {
            "conversation_id": response["conversation"]["conversation_id"],
            "buttons": response["conversation"]["response_buttons"]
        }
    else:
        response = requests.get(
            f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()
        print(response)

    n = 3500
    state["active_message_id"] = None
    error, text, buttons = update_state(user_id, response)
    if error:
        message.answer(text="Произошла ошибка: " + error)
    else:
        last = [await message.answer(text=s, reply_markup=create_user_kb(buttons, state['conversation_id'])) for s in [text[i:i+n] for i in range(0, len(text), n)]][-1]
        state["active_message_id"] = last.message_id


@dp.callback_query_handler(text_contains="tree_")
async def handle_active_conversation_buttons(call: types.CallbackQuery):
    """
    нажатия на кнопки, переданные из апи с ветками дерева

    Вид: tree_conversaionId_...
    """
    user_id = call.message.chat.id
    print(f"User {user_id} pressed on button {call.data}")
    data = call.data.split("_")

    conv_id = int(data[1])  # ID диалога

    state = user_database.get(user_id)  # получаем состояние пользователя из БД
    if not state or state['conversation_id'] != conv_id:
        return

    print(state["buttons"])

    text = state["buttons"][int(data[2])]
    print(text)
    response = requests.get(
        f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()

    n = 3500
    error, text, buttons = update_state(user_id, response)
    if error:
        bot.answer_callback_query(
            call.id, "Произошла ошибка: " + error, show_alert=False)
    else:
        state["active_message_id"] = await edit_or_send_more(user_id, call.message.message_id, text, create_user_kb(buttons, conv_id))


async def edit_or_send_more(chat_id, message_id, text, markup) -> int:
    
    max_length = 3500
    print(f"editing message {message_id} to {text}, {markup}")

    multiple_messages = len(text) > max_length
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text[:max_length],
                                reply_markup=types.InlineKeyboardMarkup() if multiple_messages else markup)
    if multiple_messages:

        last_message_id = None
        text = text[max_length:]
        while len(text):
            piece = text[:max_length]
            text = text[max_length:]
            m = None if text else markup
            sent_message = await bot.send_message(chat_id=chat_id, text=piece, reply_markup=m)
            last_message_id = sent_message.message_id
        return last_message_id
    return message_id
            

def update_state(user_id, response):

    if response['status'] != 'SUCCESS':
        return response['status'], None, None
    conversation = response['conversation']
    state = user_database[user_id]
    state['conversation_id'] = conversation['conversation_id']
    state['buttons'] = conversation['response_buttons']
    state['finished'] = conversation['response_finished']
    return None, conversation['response_text'], conversation['response_buttons']


async def update_messages():
    global user_database
    while True:
        await asyncio.sleep(1)
        # print("Updating messages")
        for user_id in user_database.keys():
            try:
                state = user_database[user_id]
                if state.get('finished'):
                    continue
                msg_id = state.get('active_message_id')
                if not msg_id:
                    continue
                
                response = requests.get(
                    f"{base_url}/get_conversation?token={company_token}&conversation_id={state['conversation_id']}").json()
                
                error, text, buttons = update_state(user_id, response)
                print(text, buttons)
                await edit_or_send_more(user_id, msg_id, text or f"Произошла ошибка: {error}", create_user_kb(buttons, state['conversation_id']))
                # bot.edit_message_text(chat_id=user_id, message_id=state['active_message_id'], text=text or f"Произошла ошибка: {error}")
                # bot.edit_message_reply_markup(chat_id=user_id, message_id=state['active_message_id'], reply_markup=create_user_kb(buttons, state['conversation_id']))
            except Exception as e:
                traceback.print_exc()

async def on_startup(_):
    asyncio.create_task(update_messages())


def rate_keyboard_all():
    markup = types.InlineKeyboardMarkup(row_width=2)

    for i in range(6):
        markup.add(f"Оценить: {str(i)}", callback_data=f"rate_{i}")

    return markup


# threading.Thread(daemon=True, target=update_messages).start()
aiogram.executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
