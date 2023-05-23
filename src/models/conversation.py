import uuid
import datetime

from peewee import *


db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class ConversationStart(Model):
    """
    таблица с временами начала диалога
    """
    conversation_id = UUIDField(default=uuid.uuid4, unique=True)  # айди диалога

    date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # время начала диалога

    class Meta:
        database = db
        db_table = "conversation_start"


class Conversation(Model):
    """
    таблица с диалогами
    """
    id = AutoField(primary_key=True, null=False)  # айдишник в бд (инкремент)

    conversation_id = ForeignKeyField(ConversationStart, field=ConversationStart.conversation_id)  # айди диалога

    message_date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # время сообщения
    message_body = TextField(null=False)  # тело сообщения

    answer_body = TextField(null=False)  # тело ответа

    class Meta:
        database = db
        db_table = "conversation"


# db.drop_tables([Conversation, ConversationStart])
db.create_tables([Conversation, ConversationStart])