from peewee import *

from src.db import db

# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class User(Model):
    """
    таблица с пользователями

    таблица с минимальными статистическими данными
    о пользователе, для паросинга gorodraboot.ru
    """
    user_id = BigIntegerField(primary_key=True, unique=True)  # айди пользователя

    city = TextField(null=True)  # город пользователя

    industry = TextField(null=True)  # индустрия работы пользователя

    class Meta:
        database = db
        table_name = "users"


db.create_tables([User])
