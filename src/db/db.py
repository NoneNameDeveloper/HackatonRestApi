from playhouse.pool import PooledPostgresqlDatabase
from src.data.config import *

# строка подключения к базе данных
db = PooledPostgresqlDatabase(POSTGRES_DATABASE, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
# print("Initialized db")
