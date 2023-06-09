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
    # история перемещений по дереву базы знаний
    history_state = TextField(null=True)

    # True, если ответ на последнее сообщение юзера финальный и больше не будет обновлятся
    response_finished = BooleanField(default=False)
    # Текущий ответ на сообщение, может меняться пока response_finished = False
    response_text = TextField(null=False)
    # JSON-список с кнопками, которые предлагаются в ответе
    response_buttons = TextField(null=False)

    # получал ли пользователь какой то ответ
    has_answers = BooleanField(null=False, default=False)

    rate = IntegerField(null=True)  # оценка разговора

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
            rate=self.rate,
            has_answers=self.has_answers
        )

    def update_history_state(self):
        Conversation.update(history_state=self.history_state) \
            .where(Conversation.conversation_id == self.conversation_id) \
            .execute()

    def set_rate(self, rate: int):
        Conversation.update(rate=rate) \
            .where(Conversation.conversation_id == self.conversation_id) \
            .execute()
        self.rate = rate


# db.drop_tables([Conversation])
db.create_tables([Conversation])
