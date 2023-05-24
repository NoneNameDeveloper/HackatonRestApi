import hashlib
import secrets
import datetime
import typing

from peewee import *
from src.db import db

# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class Company(Model):
    """
    таблица с компаниями
    """
    company_id = AutoField(primary_key=True, unique=True)  # айди компании
    company_name = TextField(null=True)  # название компании (если есть)

    token_hash = CharField(unique=True)  # храним хэш токена

    date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # дата-время регистрации компании

    class Meta:
        database = db
        table_name = "companies"


db.create_tables([Company])
