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


# reset_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
# reset_kb.add("/reset")

def encode_to_base64(string) -> str:
    """
    кодируем строку в base64
    """
    encoded_string = base64.b64encode(string.encode('utf-8'))
    return encoded_string.decode('utf-8')


def decode_from_base64(encoded_string) -> str:
    """
    декодируем строку из base64
    """
    decoded_string = base64.b64decode(encoded_string).decode('utf-8')
    return decoded_string


def create_user_kb(buttons: list[str]):
    keyboard = types.InlineKeyboardMarkup()

    for u in buttons:
        try:
            keyboard.add(types.InlineKeyboardButton(u, callback_data=f"tree_{encode_to_base64(u[:32])}"))
        except Exception as e:
            print(traceback.format_exc())
            pass

    return keyboard

# @dp.message_handler(commands=["start", "restart", "reset"])
# async def reset_state_handler(message: types.Message):
#     user_id = message.chat.id

#     response = requests.get(base_url + "/reset_state?user_id=" + str(user_id) + "&token=" + company_token).json()

#     await message.answer(str(response), reply_markup=reset_kb)


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


@dp.message_handler(commands=["start", "restart", "reset"])
@dp.message_handler()
async def all_text_hander(message: types.Message):

    text = message.text
    user_id = message.chat.id

    try:
        response_f = requests.get(base_url + "/get_filter?user_id=" + str(user_id) + "&token=" + company_token, timeout=3).json()

        if message.text.lower() in response_f['content']:
            return await message.answer("Не допустимый вашей компанией запрос!")
    except:
        pass

    print(base_url + "/text_prompt?user_id=" + str(user_id) + "&token=" + company_token + "&text=" + quote(text))

    response = requests.get(base_url + "/text_prompt?user_id=" + str(user_id) + "&token=" + company_token + "&text=" + quote(text)).json()

    if response['status'] != "SUCCESS":
        answer = "Ошибка: " + response['STATUS']
    else:
        answer = response['result']

    buttons = response['variants']
    n = 3500
    print("тут")
    [await message.answer(text=s, reply_markup=create_user_kb(buttons)) for s in [answer[i:i+n] for i in range(0, len(answer), n)]]


@dp.callback_query_handler(text_contains="tree_")
async def handle_tree_buttons_click_handler(call: types.CallbackQuery):

    data = call.data.split("_")  # example: ['tree', 'Экономика']

    # получаем название ноды из ветки вопрос-ответов
    node_title = decode_from_base64(data[1])

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

aiogram.executor.start_polling(dp, skip_updates=True)


