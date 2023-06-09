import os

import requests
import aiogram
from aiogram import types

import logging
from urllib.parse import quote
import traceback
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

base_url = os.environ["TADA_API_BASE_URL"]  # Ссылка на АПИ
company_token = os.environ["TADA_API_COMPANY_TOKEN"]  # токен компании, являющейся клиентом в TADA
token = os.environ['TELEGRAM_TOKEN']  # Токен телеграм бот для демонстрации работы АПИ


bot = aiogram.Bot(token)

dp = aiogram.Dispatcher(bot)

user_database = {}  # база состояний пользователя


def create_user_kb(buttons: list[str], conversation_id: int):
    """
    Создаем клавиатуру для пользователя, с переданным списком кнопок
    из АПИ
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


def rate_keyboard_all(conversation_id: int):
    """
    создание клавиатуры с оценкой

    :conversation_id: ID диалога
    """
    markup = types.InlineKeyboardMarkup(row_width=3)

    for rate_value in range(6):
        markup.insert(
            types.InlineKeyboardButton(f"{str(rate_value)}", callback_data=f"rate_{rate_value}_{conversation_id}")
        )

    return markup


@dp.message_handler(commands=["add_rule"])
async def add_rule_bot(message: types.Message):

    words = message.text.replace("/add_rule ", "")  # отделяем текст, который требуется поместить в стоп слова

    # пробегаемся по стоп-словам и передаем их в АПИ по одному
    for word in words.split():
        response = requests.get(base_url + "/add_filter?token=" +
                                company_token + "&filter=" + str(word).lower()).json()

        if response['status'] == "SUCCESS":
            await message.answer(f"Правило добавлено\nID: {response['rule_id']}")


@dp.message_handler(commands=["archive_rule"])
async def archive_rule_handler(message: types.Message):

    id_ = message.text.replace("/archive_rule ", "")  # отделяем ID правила от команды

    # проверка на то, что ID правила - целое число
    if not id_.isdigit():
        return await message.answer("Это не целое число!")

    # архивация правила
    response = requests.get(
        base_url + "/archive_filter?token=" + company_token + "&rule_id=" + id_).json()

    if response['status'] == 'SUCCESS':
        return await message.answer("Правило удалено!")

    return await message.answer("Ошибка!")


@dp.message_handler()
async def all_text_hander(message: types.Message):

    text = message.text
    user_id = message.chat.id

    # получае состояние пользователя по user_id из базы
    state = user_database.get(user_id)
    print("Состояние пользователя: " + str(state))
    # если состояний нет или пользователь сбрасывает состояние
    if not state or text.lower() in ["меню", "/start", "/reset", "/restart"]:

        # если в диалоге было общение
        if state:
            # сообщение с предложением об оценке диалога
            await message.answer("Оцените, как прошёл диалог.", reply_markup=rate_keyboard_all(state['conversation_id']))

        # создание нового диалога
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
    # диалог уже был начат, сообщение в текущем диалоге
    else:
        # обработка нового сообщения в уже имеющемся диалоге
        response = requests.get(
            f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()
        print(response)

    # ограничение для срезания сообшения по символам
    telegram_limit_value = 3500

    # обнуляем активное сообщения пользователя для редактирования
    state["active_message_id"] = None

    # обновляем состояния пользователя в бд
    error, text, buttons = update_state(user_id, response)

    if error:
        message.answer(text="Произошла ошибка: " + error)
    else:
        # ответ пользователю на его вопрос с дроблением сообщения по лимитам Telegram Bot Api
        for answer_part in range(0, len(text), telegram_limit_value):
            for cropped_text in [text[answer_part:answer_part + telegram_limit_value]]:
                last_message = await message.answer(text=cropped_text, reply_markup=create_user_kb(buttons, state['conversation_id']))

        # запоминаем ID последнего сообщения
        state["active_message_id"] = last_message.message_id


@dp.callback_query_handler(text_contains="tree_")
async def handle_active_conversation_buttons(call: types.CallbackQuery):
    """
    нажатия на кнопки, переданные из апи с ветками дерева

    Вид: tree_conversaionId_...TextIDX
    """
    user_id = call.message.chat.id

    print(f"User {user_id} pressed on button {call.data}")

    data = call.data.split("_")

    conv_id = int(data[1])  # ID диалога (conversation_id)

    state = user_database.get(user_id)  # получаем состояние пользователя из БД
    if not state or state['conversation_id'] != conv_id:
        return

    text = state["buttons"][int(data[2])]

    # обрабатываем пользовательское нажатие на дереве
    response = requests.get(
        f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()

    # обновляем состояние
    error, text, buttons = update_state(user_id, response)

    if error:
        await bot.answer_callback_query(
            call.id, "Произошла ошибка: " + error, show_alert=False)
    else:
        # обновляем активное сообщение пользователя
        state["active_message_id"] = await edit_or_send_more(user_id, call.message.message_id, text, create_user_kb(buttons, conv_id))


@dp.callback_query_handler(text_contains="rate_")
async def get_rate_value_handler(call: types.CallbackQuery):

    await call.answer()

    data = call.data.split("_")

    # получаем значение оценки от пользователя (1-5)
    rate_value = data[1]
    # получаем айди диалога
    conversation_id = data[2]

    response = requests.get(
        f"{base_url}/rate_chat?token={company_token}&conversation_id={conversation_id}&rate={rate_value}"
    ).json()
    print(response)
    if response["status"] == "SUCCESS":
        await call.message.answer("Спасибо за Вашу оценку!")


async def edit_or_send_more(chat_id, message_id, text, markup) -> int:
    
    max_length = 3500
    print(f"editing message {message_id} to {text}, {markup}")

    multiple_messages = len(text) > max_length

    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text[:max_length],
                            reply_markup=types.InlineKeyboardMarkup() if multiple_messages else markup)
    except aiogram.utils.exceptions.MessageNotModified:
        print("Статус не изменился")

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

    # АПИ вернуло ошибку
    if response['status'] != 'SUCCESS':
        return response['status'], None, None

    conversation = response['conversation']

    # получаем текущее состояние пользователя из бд
    state = user_database[user_id]
    # обновляем состояние
    state['conversation_id'] = conversation['conversation_id']
    state['buttons'] = conversation['response_buttons']
    state['finished'] = conversation['response_finished']

    return None, conversation['response_text'], conversation['response_buttons']


async def update_messages():

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

            except Exception as e:
                traceback.print_exc()


async def on_startup(_):
    """
    функция, запускающаяся при старте бота
    """
    # запуск обновления сообщений для пользователей
    asyncio.create_task(update_messages())


# def rate_keyboard_all():
#     markup = types.InlineKeyboardMarkup(row_width=2)
#
#     for i in range(6):
#         markup.add(f"Оценить: {str(i)}", callback_data=f"rate_{i}")
#
#     return markup


# threading.Thread(daemon=True, target=update_messages).start()

# запуск бота
aiogram.executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
