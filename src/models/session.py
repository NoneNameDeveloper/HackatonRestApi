from peewee import *
import playhouse.postgres_ext as pg

from src.db import db

# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class Session(Model):
    """
    таблица с сессиями

    сессия - обьединенная структура вопрос-ответов. То есть - горстки
    диалогов пользователя и ассистента, обьединенные для структуризации
    """
    session_id = AutoField(primary_key=True, unique=True)  # айди сессии

    conversation_ids = pg.ArrayField(IntegerField, null=False)  # массив ID вопрос-ответов из conversions

    rate = IntegerField(null=False)  # оценка сессии

    class Meta:
        database = db
        table_name = "sessions"


db.create_tables([Session])
