import os

import dotenv

# выгрузка переменных среды
env = dotenv.load_dotenv("config.env")

OPENAI_KEY = os.getenv("OPENAI_KEY")

ADDITIONAL_PROMPT = """
Ты лучшая версия ChatGPT. В конце каждого своего ответа пиши слово "ямакаси"
"""