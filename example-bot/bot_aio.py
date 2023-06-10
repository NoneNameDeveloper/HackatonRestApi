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

bot = aiogram.Bot(token, parse_mode="html")

dp = aiogram.Dispatcher(bot)

user_database = {}  # база состояний пользователя

telegram_limit_value = 4000  # ограничение телеграма на кол-во символов в одном сообшении


def create_user_kb(buttons: list[str], conversation_id: int):
	"""
	Создаем клавиатуру для пользователя, с переданным списком кнопок
	из АПИ
	"""
	keyboard = types.InlineKeyboardMarkup()

	i = 0
	for u in buttons or []:
		try:
			keyboard.add(types.InlineKeyboardButton(u, callback_data=f"tree_{conversation_id}_{i}"))
			i += 1
		except:
			print(traceback.format_exc())

	return keyboard


def rate_keyboard_all(conversation_id: int):
	"""
	создание клавиатуры с оценкой

	:conversation_id: ID диалога
	"""
	markup = types.InlineKeyboardMarkup(row_width=5)

	for rate_value in range(1, 6):
		markup.insert(
			types.InlineKeyboardButton("😢🙁😐🙂😄"[rate_value - 1], callback_data=f"rate_{rate_value}_{conversation_id}")
		)

	return markup


def user_menu_keyboard():
	"""
	клавиатура для упрощения взаимодействия с ботом
	"""
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

	markup.row("Меню")

	return markup


@dp.message_handler(commands=["add_rule"])
async def add_rule_bot(message: types.Message):
	"""
	Добавление фильтра (стоп-слов)
	"""
	words = message.text.replace("/add_rule ", "")  # отделяем текст, который требуется поместить в стоп слова

	# список
	rules_list: list[str] = []

	# пробегаемся по стоп-словам и передаем их в АПИ по одному
	for word in words.split():
		response = requests.post(
			base_url + "/add_filter?token=" + company_token + "&filter=" + str(word).lower()
		).json()

		if response['status'] == "SUCCESS":
			rules_list.append(str(response['filter_text']))

	await message.answer(f"✅ Правила добавлены\n<i>{','.join(rules_list)}</i>")


@dp.message_handler(commands=["archive_rule"])
async def archive_rule_handler(message: types.Message):
	"""
	Архвация фильтра (стоп-слова)
	"""
	rules_texts = message.text.replace("/archive_rule ", "")  # получаем текста правил на архивацию

	# текст по статусу удаления каждого правила
	status_text = ""

	# бежим по переданным в сообщении айдишникам
	for text in rules_texts.split():

		# архивация правила
		response = requests.get(
			base_url + "/archive_filter?token=" + company_token + "&rule_text=" + text).json()

		# успех
		if response['status'] == 'SUCCESS':
			status_text += f"✅ Фильтр <i>{response['filter_text']}</i> был успешно удалён!\n"
		# фильтр уже удален / не существует
		else:
			status_text += f"❌ Фильтр <i>{text}</i> не был удален!\n"

	return await message.answer(status_text)


@dp.message_handler(commands=["block_url"])
async def block_url_handler(message: types.Message):
	"""
	Помещение ссылки в черный список
	"""
	urls = message.text.replace("/block_url", "")  # отделяем текст, который требуется поместить в стоп слова
	print(urls)
	if not urls:
		return await message.answer("Неверный формат ввода.")

	# список
	urls_list: list[str] = []

	# пробегаемся по стоп-словам и передаем их в АПИ по одному
	for url in urls.split():
		response = requests.post(
			base_url + "/block_url?token=" + company_token + "&uri=" + str(url).lower()
		).json()

		if response['status'] == "SUCCESS":
			urls_list.append(str(response['uri']))

	await message.answer(f"✅ URL добавлены в черный список\n<i>{','.join(urls_list)}</i>")


@dp.message_handler(commands=["unblock_url"])
async def unblock_url_handler(message: types.Message):
	"""
	Удаление ссылки из черного списка
	"""
	urls = message.text.replace("/unblock_url", "")  # получаем текста правил на архивацию

	if not urls:
		return await message.answer("Неверный форамат ввода.")

	# текст по статусу удаления каждого правила
	status_text = ""

	# бежим по переданным в сообщении айдишникам
	for url in urls.split():

		# архивация правила
		response = requests.post(
			base_url + "/unblock_url?token=" + company_token + "&uri=" + url).json()

		# успех
		if response['status'] == 'SUCCESS':
			status_text += f"✅ Ресурс <i>{response['uri']}</i> был успешно удалён из черного списка!\n"
		# ссылка уже удалена / не существует
		else:
			status_text += f"❌ Ресурс <i>{url}</i> не был удален!\n"

	return await message.answer(status_text)


@dp.message_handler()
async def all_text_hander(message: types.Message):
	"""
	Обработка все текстовых сообщение, отправленных в бота
	"""
	# текст пользователя
	text = message.text
	# ID пользователя
	user_id = message.chat.id

	# получае состояние пользователя по user_id из базы
	state = user_database.get(user_id)

	# пользователь первый раз начинает диалог
	new_user = not state

	print("Состояние пользователя: " + str(state) + ", сообщение: " + text)

	# если состояний нет или пользователь сбрасывает состояние
	if not state or text.lower() in ["меню", "/start", "/reset", "/restart"]:

		# если в диалоге было общение
		if state and state['has_answers']:
			# сообщение с предложением об оценке диалога
			await message.answer(
				"Оцените, как прошёл диалог.",
				reply_markup=rate_keyboard_all(state['conversation_id'])
			)

		# создание нового диалога
		url = f"{base_url}/new_conversation?user_id={user_id}&token={company_token}&initial_message={quote(text)}"
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
		response = requests.post(
			f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()
		print(response)

	# обнуляем активное сообщения пользователя для редактирования
	state["active_message_id"] = None

	# обновляем состояния пользователя в бд
	error, text, buttons = update_state(user_id, response)

	if error:
		await message.answer(text="Произошла ошибка: " + error)
	else:
		# ответ пользователю на его вопрос с дроблением сообщения по лимитам Telegram Bot Api
		for answer_part in range(0, len(text), telegram_limit_value):
			for cropped_text in [text[answer_part:answer_part + telegram_limit_value]]:
				if new_user:
					# отправка сообщения для появления реплай клавиатуры
					await message.answer("👋", reply_markup=user_menu_keyboard())

				last_message = await message.answer(
					text=cropped_text,
					reply_markup=create_user_kb(buttons, state['conversation_id']),
					disable_web_page_preview=True
				)

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

	# получаем данные из кнопки, разделяя по символу
	data = call.data.split("_")

	conv_id = int(data[1])  # ID диалога (conversation_id)

	state = user_database.get(user_id)  # получаем состояние пользователя из БД
	if not state or state['conversation_id'] != conv_id:
		return

	text = state["buttons"][int(data[2])]

	response = None

	# обрабатываем пользовательское нажатие на дереве
	try:
		response = requests.post(
			f"{base_url}/new_user_message?user_id={user_id}&token={company_token}&conversation_id={state['conversation_id']}&text={quote(text)}").json()
	except Exception:
		traceback.print_exc()

	# обновляем состояние
	error, text, buttons = update_state(user_id, response)

	# возникла ошибка
	if error:
		await bot.answer_callback_query(
			call.id, "Произошла ошибка: " + error, show_alert=False)
	else:
		# обновляем активное сообщение пользователя
		state["active_message_id"] = await edit_or_send_more(
			chat_id=user_id,
			message_id=call.message.message_id,
			text=text,
			markup=create_user_kb(buttons, conv_id)
		)


@dp.callback_query_handler(text_contains="rate_")
async def get_rate_value_handler(call: types.CallbackQuery):
	"""
	Оценка диалога по пятибальной шкале
	"""
	await call.answer()

	# разделение callback_data ля получения параметров
	data = call.data.split("_")

	# получаем значение оценки от пользователя (1-5)
	rate_value = data[1]
	# получаем айди диалога
	conversation_id = data[2]

	# запрос на выставление оценки
	response = requests.put(
		f"{base_url}/rate_chat?token={company_token}&conversation_id={conversation_id}&rate={rate_value}"
	).json()
	if response["status"] == "SUCCESS":
		await call.message.edit_text(text='Спасибо за оценку! Благодаря вам мы становимся лучше!')


async def edit_or_send_more(chat_id: int, message_id: int, text: str, markup) -> int:
	"""
	Обновление статуса сообщения путем редактирования сообщения / вывод ответа на вопрос
	"""
	print(f"editing message {message_id} to {text}, {markup}")

	# флаг для разделения сообщения на части из-за лимита
	multiple_messages = len(text) > telegram_limit_value

	# обработка ошибки (текст сообщения не изменился)
	try:
		# отправка действия от бота "печатает..."
		await bot.send_chat_action(chat_id, "typing")

		# редактирование сообщения
		await bot.edit_message_text(
			chat_id=chat_id, message_id=message_id, text=text[:telegram_limit_value],
			reply_markup=types.InlineKeyboardMarkup() if multiple_messages else markup, disable_web_page_preview=True
		)
	except aiogram.utils.exceptions.MessageNotModified:
		print("Статус не изменился")

	# если сообщение требуется поделить по частям
	if multiple_messages:
		# ID последнего сообщения
		last_message_id = None
		# обрезанный текст
		text = text[telegram_limit_value:]
		# пока в тексте есть символы - отправляем его по частям
		while len(text):
			piece = text[:telegram_limit_value]
			text = text[telegram_limit_value:]

			m = None if text else markup

			sent_message = await bot.send_message(chat_id=chat_id, text=piece, reply_markup=m, disable_web_page_preview=True)
			last_message_id = sent_message.message_id

		return last_message_id

	return message_id


def update_state(user_id, response):
	"""
	Обновление состояния пользователя в 'базе данных'
	"""
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
	state['has_answers'] = conversation['has_answers']

	return None, conversation['response_text'], conversation['response_buttons']


async def update_messages():
	"""
	Обновление сообщений для конкретного пользователя (ожидание ответа)
	"""

	while True:
		await asyncio.sleep(1)
		for user_id in user_database.keys():
			print("Updating messages")
			try:
				# получения текущего состояния пользователя в БД
				state = user_database[user_id]

				# если бот прислал finished, то обновлений текущего ответа больше не будет
				if state.get('finished'):
					continue

				# получаем ID редактируемого сообщения
				msg_id = state.get('active_message_id')
				
				# если активное сообщение ещё не отправилось - его пока не выйдет отредактировать
				if not msg_id:
					continue

				# получаем текущее состояние ответа в диалоге
				response = requests.get(
					f"{base_url}/get_conversation?token={company_token}&conversation_id={state['conversation_id']}").json()

				# обновляем состояние ползовтеля в соответствии с ответом от АПИ
				error, text, buttons = update_state(user_id, response)

				# редактирование состояния / ответ на вопрос
				await edit_or_send_more(
					chat_id=user_id,
					message_id=msg_id,
					text=text or f"Произошла ошибка: {error}",
					markup=create_user_kb(buttons, state['conversation_id']))
				if error:
					state['active_message_id'] = None

			except Exception as e:
				traceback.print_exc()

async def on_startup(_):
	# запуск обновления сообщений для пользователей
	asyncio.create_task(update_messages())

# запуск бота
aiogram.executor.start_polling(dp, on_startup=on_startup)
