import os

import requests
import aiogram
from aiogram import types

import logging
from urllib.parse import quote


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

base_url = os.environ["TADA_API_BASE_URL"]
company_token = os.environ["TADA_API_COMPANY_TOKEN"]
token = os.environ['TELEGRAM_TOKEN']


bot = aiogram.Bot(token)

dp = aiogram.Dispatcher(bot)


reset_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
reset_kb.add("/reset")


def create_user_kb(buttons: list[str]):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for u in buttons:
        markup.add(u)

    return markup


@dp.message_handler(commands=["start", "restart", "reset"])
async def reset_state_handler(message: types.Message):
    user_id = message.chat.id

    response = requests.get(base_url + "/reset_state?user_id=" + str(user_id) + "&token=" + company_token).json()

    await message.answer(str(response), reply_markup=reset_kb)


@dp.message_handler(commands=["add_rule"])
async def add_rule_bot(message: types.Message):

    words = message.text.replace("/add_rule ", "")
    print(base_url + "/add_filter?token=" + company_token + "&filter=" + str(words))
    for word in words:
        response = requests.get(base_url + "/add_filter?token=" + company_token + "&filter=" + str(word)).json()
        print(response)

        if response['status_code'] == 200:
            await message.answer(f"Правило добавлено\nID: {response['rule_id']}")


@dp.message_handler(commands=["archive_rule"])
async def archive_filter_handler(message: types.Message):

    id_ = message.text.replace("/add_rule ", "")

    response = requests.get(base_url + "/archive_filter?token=" + company_token + "&filter=" + str(id_))
    print(response.text)



@dp.message_handler()
async def all_text_hander(message: types.Message):

    text = message.text
    user_id = message.chat.id

    response = requests.get(base_url + "/text_prompt?user_id=" + str(user_id) + "&token=" + company_token + "&text=" + quote(text)).json()
    print(response)

    if response['status'] != "SUCCESS":
        answer = "Ошибка: " + response['STATUS']
    else:
        answer = response['result']

    buttons = [[variant] for variant in response['variants']]
    n = 400

    [await message.answer(text=s, reply_markup=create_user_kb(buttons)) for s in [answer[i:i+n] for i in range(0, len(answer), n)]]




aiogram.executor.start_polling(dp)


