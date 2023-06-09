from peewee import *

from src.db import db
from src.models import Company, Conversation

class User(Model):
    """
    таблица с пользователями

    таблица с минимальными статистическими данными
    о пользователе, для паросинга gorodraboot.ru
    """
    user_id = BigIntegerField(primary_key=True, unique=True)  # айди пользователя (в нашем случае Telegram ID)
    company_id = ForeignKeyField(Company, field=Company.company_id)  # айди компании, к которой привязан юзер (Telegram Chat ID) | только для личного чата с ботом
    active_conversation = IntegerField(null=True)

    class Meta:
        database = db
        table_name = "users"

    # def get_active_conversation(self) -> 'Conversation':
    #     if not self.active_conversation:
    #         return None
    #     return Conversation.get_or_none(Conversation.conversation_id == self.active_conversation)
    
    def get_or_create(user_id: int, company_id: int) -> 'User':
        return User.get_or_none(User.user_id == user_id) or User.create(
            user_id=user_id,
            company_id=company_id,
        )


# db.drop_tables([User])
db.create_tables([User])
