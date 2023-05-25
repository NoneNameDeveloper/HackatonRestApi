import datetime

from peewee import *

from src.models import Company
from src.db import db

# db = PostgresqlDatabase('hackatonrestdb', user='postgres', password='159326', host='195.201.170.94', port=5432)


class Rule(Model):
    """
    таблица с правилами-фильтрами
    """
    rule_id = AutoField(primary_key=True, unique=True)  # айди правила
    company_id = ForeignKeyField(Company, field=Company.company_id)  # айди компании, создавшей правило

    filter_text = TextField(null=False)  # текст фильтра
    filter_description = TextField(null=False)  # описание фильтра

    date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.datetime.now)  # дата-время создания фильтра

    archived = BooleanField(default=False)  # заархивирован/незаархивирован фильтр
    archive_date = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])  # дата архивации

    class Meta:
        database = db
        table_name = "rules"


db.create_tables([Rule])