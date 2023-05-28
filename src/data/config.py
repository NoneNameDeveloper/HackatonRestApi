import os

import dotenv

# выгрузка переменных среды
env = dotenv.load_dotenv("config.env")

OPENAI_KEY = os.getenv("OPENAI_KEY")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

# доп промпт к чатжпт в каждом запросе
ADDITIONAL_PROMPT = """"""