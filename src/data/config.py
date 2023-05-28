import os
import dotenv
import yaml

# выгрузка переменных среды
env = dotenv.load_dotenv("config.env")

OPENAI_KEY = os.getenv("OPENAI_KEY")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

hints_config = None
with open('config.yml', 'r') as file:
    hints_config = yaml.safe_load(file)