import os
import traceback

import requests
import aiogram
from aiogram import types

import logging
from urllib.parse import quote

import base64

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

base_url = os.environ["TADA_API_BASE_URL"]
company_token = os.environ["TADA_API_COMPANY_TOKEN"]
token = os.environ['TELEGRAM_TOKEN']


bot = aiogram.Bot(token)

dp = aiogram.Dispatcher(bot)

user_database = {}

def create_user_kb(buttons: list[str]):
    keyboard = types.InlineKeyboardMarkup()

    for u in buttons:
        try:
            # print(f"tree_{encode_to_base64(u[:32])}")
            print(f"tree_{u[:30]}")
            keyboard.add(types.InlineKeyboardButton(u[:32], callback_data=f"tree_{u[:30]}"))
        except Exception as e:
            print(traceback.format_exc())
            pass

    return keyboard


@dp.message_handler(commands=["add_rule"])
async def add_rule_bot(message: types.Message):

    words = message.text.replace("/add_rule ", "")

    for word in words.split():
        response = requests.get(base_url + "/add_filter?token=" + company_token + "&filter=" + str(word).lower()).json()

        if response['status'] == "SUCCESS":
            await message.answer(f"Правило добавлено\nID: {response['rule_id']}")


@dp.message_handler(commands=["archive_rule"])
async def archive_filter_handler(message: types.Message):

    id_ = message.text.replace("/archive_rule ", "")

    if not id_.isdigit():
        return await message.answer("Это не целое число!")

    response = requests.get(base_url + "/archive_filter?token=" + company_token + "&rule_id=" + id_).json()

    if response['status'] == 'SUCCESS':
        return await message.answer("Правило удалено!")

    await message.answer("Ошибка!")


@dp.message_handler()
async def all_text_hander(message: types.Message):

    text = message.text
    user_id = message.chat.id
    global user_database

    state = user_database.get(user_id)
    response = None
    if not state or text.lower() in ["меню", "/start", "/reset", "/restart"]:
        url = f"{base_url}/new_conversation?user_id={user_id}&token={company_token}"
        print(url)
        response = requests.post(url).json()
        print(response)
        user_database[user_id] = {
            "conversation_id": response["conversation"]["conversation_id"]
        }
    else:
        response = requests.get(f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}").json()
        print(response)
    
    if response['status'] != "SUCCESS":
        message.answer(text="Произошла ошибка.")
        return
    conversation = response['conversation']
    answer = conversation['response_text']
    buttons = conversation['response_buttons']
    
    n = 3500
    
    [await message.answer(text=s, reply_markup=create_user_kb(buttons)) for s in [answer[i:i+n] for i in range(0, len(answer), n)]]


@dp.callback_query_handler(text_contains="tree_")
async def handle_tree_buttons_click_handler(call: types.CallbackQuery):

    data = call.data.split("_")  # example: ['tree', 'Экономика']

    print(call.message)

    # получаем название ноды из ветки вопрос-ответов
    node_title = data[1]

    user_id = call.message.chat.id

    response = requests.get(
        base_url + "/text_prompt?user_id=" + str(user_id) + "&token=" + company_token + "&text=" + quote(node_title)).json()

    if response['status'] != "SUCCESS":
        answer = "Ошибка: " + response['STATUS']
    else:
        answer = response['result']

    buttons = response['variants']
    n = 3500

    [await call.message.edit_text(text=s, reply_markup=create_user_kb(buttons)) for s in
     [answer[i:i + n] for i in range(0, len(answer), n)]]


def rate_keyboard_all():
    markup = types.InlineKeyboardMarkup(row_width=2)

    for i in range(6):
        markup.add(f"Оценить: {str(i)}", callback_data=f"rate_{i}")

    return markup



aiogram.executor.start_polling(dp, skip_updates=True)


