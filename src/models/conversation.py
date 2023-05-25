import datetime

from peewee import *

from .company import Company
from src.db import db


class Conversation(Model):
    """
    таблица с диалогами
    """
    conversation_id = AutoField(primary_key=True, null=False)  # айдишник в бд (инкремент)

    user_id = BigIntegerField(null=False)  # айди пользователя, сделавшего запрос
    company_id = ForeignKeyField(Company, field=Company.company_id)  # айди компании, в которой состоит пользователь

    message_date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # время сообщения
    message_body = TextField(null=False)  # тело сообщения

    answer_body = TextField(null=False)  # тело ответа

    active = BooleanField(default=True)  # активно или сброшено

    rate = IntegerField(null=True)  # оценка ответу

    class Meta:
        database = db
        table_name = "conversations"


# db.drop_tables([Conversation])
db.create_tables([Conversation])