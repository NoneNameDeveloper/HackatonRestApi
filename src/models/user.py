from peewee import *

from src.db import db
from src.models import Company


# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class User(Model):
    """
    таблица с пользователями

    таблица с минимальными статистическими данными
    о пользователе, для паросинга gorodraboot.ru
    """
    user_id = BigIntegerField(primary_key=True, unique=True)  # айди пользователя (в нашем случае Telegram ID)

    company_id = ForeignKeyField(Company, field=Company.company_id)  # айди компании, к которой привязан юзер (Telegram Chat ID) | только для личного чата с ботом

    city = TextField(null=True)  # город пользователя

    industry = TextField(null=True)  # индустрия работы пользователя

    history_state = TextField(null=True)  # история нод/вопросов пользователя

    class Meta:
        database = db
        table_name = "users"


# db.drop_tables([User])
db.create_tables([User])
