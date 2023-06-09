import datetime

from peewee import *

from .company import Company
from src.db import db
import json


class Conversation(Model):
    """
    таблица с диалогами
    """
    conversation_id = AutoField(primary_key=True, null=False)  # айдишник в бд (инкремент)

    user_id = BigIntegerField(null=False)  # айди пользователя, сделавшего запрос

    company_id = IntegerField(null=False)  # айди компании, в которой состоит пользователь

    start_date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # время сообщения

    last_user_message = TextField(null=False)  # последнее сообщение от пользователя
    history_state = TextField(null=True)  # история перемещений по дереву базы знаний

    response_finished = BooleanField(default=False)  # True, если ответ на последнее сообщение юзера финальный и больше не будет обновлятся
    response_text = TextField(null=False)  # Текущий ответ на сообщение, может меняться пока response_finished = False
    response_buttons = TextField(null=False)  # JSON-список с кнопками, которые предлагаются в ответе

    has_answers = BooleanField(null=False, default=False)  # получал ли пользователь какой то ответ

    rate = IntegerField(null=True)  # оценка разговора

    class Meta:
        database = db
        table_name = "conversations"

    # def get_active_conversation(user_id: int) -> 'Conversation':
    #     Conversation.select(Conversation.user_id == user_id, Conversation.active == true)

    def set_has_answers(self):
        Conversation.update(has_answers=True).where(Conversation.conversation_id == self.conversation_id).execute()
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

    def to_dto(self: 'Conversation'):
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'start_date': str(self.start_date),
            'last_user_message': self.last_user_message,
            'response_finished': self.response_finished,
            'response_text': self.response_text,
            'response_buttons': json.loads(self.response_buttons),
            'rate': self.rate
        }
    
    def update_history_state(self):
        Conversation.update(
            history_state=self.history_state
        ).where(
            Conversation.conversation_id == self.conversation_id
        ).execute()


# db.drop_tables([Conversation])
db.create_tables([Conversation])
