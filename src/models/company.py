import datetime

from peewee import *
from src.db import db

import hashlib

# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class Company(Model):
    """
    таблица с компаниями
    """
    company_id = BigIntegerField(primary_key=True, unique=True)  # айди компании (Telegram Chat ID)
    company_name = TextField(null=True)  # название компании (если есть) (Название чата Telegram)

    token_hash = CharField(unique=True)  # храним хэш токена

    date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # дата-время регистрации компании

    class Meta:
        database = db
        table_name = "companies"


    def get_by_token(token: str) -> 'Company':
        token_hash = hashlib.sha256(token.encode()).hexdigest()  # хешируем токен обратно для поиска в бд
        return Company.get_or_none(Company.token_hash == token_hash)


# db.drop_tables([Company])
db.create_tables([Company])
