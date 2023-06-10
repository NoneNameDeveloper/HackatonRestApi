import datetime

from peewee import *

from src.db import db
import json
import pydantic
import typing


class ConversationDto(pydantic.BaseModel):
	conversation_id: int
	user_id: int
	company_id: int
	start_date: str
	last_user_message: str
	response_finished: bool
	response_text: str
	response_buttons: list[str]
	has_answers: bool
	rate: typing.Optional[int]
	rate_1: typing.Optional[int]
	rate_2: typing.Optional[int]


class Conversation(Model):
	"""
	таблица с диалогами
	"""
	conversation_id = AutoField(
		primary_key=True, null=False)  # айдишник в бд (инкремент)

	# айди пользователя, сделавшего запрос
	user_id = BigIntegerField(null=False)

	# айди компании, в которой состоит пользователь
	company_id = IntegerField(null=False)

	start_date = DateTimeField(constraints=[SQL(
		'DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # время сообщения

	# последнее сообщение от пользователя
	last_user_message = TextField(null=False)
	
	# Дата последнего нового сообщения от бота
	# last_bot_message_date = DateTimeField(constraints=[SQL(
	# 	'DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)
	# история перемещений по дереву базы знаний
	current_chapter = TextField(null=False)

	# True, если ответ на последнее сообщение юзера финальный и больше не будет обновлятся
	response_finished = BooleanField(default=False)
	# Текущий ответ на сообщение, может меняться пока response_finished = False
	response_text = TextField(null=False)
	# JSON-список с кнопками, которые предлагаются в ответе
	response_buttons = TextField(null=False)

	# получал ли пользователь какой то ответ
	has_answers = BooleanField(null=False, default=False)

	rate_1 = IntegerField(null=True)  # оценка диалога первая
	rate_2 = IntegerField(null=True)  # оценка диалога вторая
	rate_3 = IntegerField(null=True)  # оценка диалога третья
	rate_4 = IntegerField(null=True)  # оценка диалога четвертая
	class Meta:
		database = db
		table_name = "conversations"

	def set_has_answers(self):
		Conversation.update(has_answers=True).where(
			Conversation.conversation_id == self.conversation_id).execute()
		self.has_answers = True

	def update_response(self, text: str, buttons: list[str], finished: bool):
		print(f"updating response: {text}, {buttons}")
		Conversation.update(
			response_text=text,
			response_buttons=json.dumps(buttons),
			response_finished=finished
		).where(
			Conversation.conversation_id == self.conversation_id
		).execute()
		self.response_text = text
		self.response_buttons = json.dumps(buttons)
		self.response_finished = finished

	def to_dto(self: 'Conversation') -> ConversationDto:
		return ConversationDto(
			conversation_id=self.conversation_id,
			user_id=self.user_id,
			company_id=self.company_id,
			start_date=str(self.start_date),
			last_user_message=self.last_user_message,
			response_finished=self.response_finished,
			response_text=self.response_text,
			response_buttons=json.loads(self.response_buttons),
			rate_1=self.rate_1,
			rate_2=self.rate_2,
			rate_3=self.rate_3,
			rate_4=self.rate_4,
			has_answers=self.has_answers
		)

	def update_current_chapter(self, chapter: str):
		Conversation.update(current_chapter=chapter) \
			.where(Conversation.conversation_id == self.conversation_id) \
			.execute()
		self.current_chapter = chapter

	def set_rate(self, rate: int, level: int):
		"""
		выставление оценки на уровне level
		"""
		if level == 1:
			Conversation.update(rate_1=rate) \
				.where(Conversation.conversation_id == self.conversation_id) \
				.execute()
			self.rate_1 = rate
		if level == 2:
			Conversation.update(rate_2=rate) \
				.where(Conversation.conversation_id == self.conversation_id) \
				.execute()
			self.rate_2 = rate

		if level == 3:
			Conversation.update(rate_3=rate) \
				.where(Conversation.conversation_id == self.conversation_id) \
				.execute()
			self.rate_3 = rate

		if level == 4:
			Conversation.update(rate_4=rate) \
				.where(Conversation.conversation_id == self.conversation_id) \
				.execute()
			self.rate_4 = rate

	# def update_last_bot_message_date(self):
	# 	now = datetime.now()	
	# 	Conversation.update(last_bot_message_date=now) \
	# 		.where(Conversation.conversation_id == self.conversation_id) \
	# 		.execute()
	# 	self.last_bot_message_date = now


# db.drop_tables([Conversation])
db.create_tables([Conversation])
