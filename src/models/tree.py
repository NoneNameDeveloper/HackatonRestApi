from peewee import *
import playhouse.postgres_ext as pg

from src.db.db import db


class Tree(Model):
    """
    таблица с деревом возможных действий и нажатий
    пользователя

    type: chapter, question, answer resultat

    text: выводится над сообшением вместе с дисклеймером
    """
    node_id = AutoField(primary_key=True, unique=True)  # ID ноды
    title = TextField(null=False)  # название ноды (текст на кнопке)

    type = TextField(null=False)  # тип ноды

    # текст, который будет над кнопкой
    text = TextField(null=True)

    parent_id = BigIntegerField(default=0, null=False)  # айди родителя

    condition_ids = pg.ArrayField(IntegerField, null=True)  # массив node_id, которые требуется пройти для получения этого результата

    class Meta:
        database = db
        table_name = "tree"


# db.drop_tables([User])
db.create_tables([Tree])
