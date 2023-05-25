from fastapi import FastAPI

from src.middlewares import *
from src.routers import *


tags_metadata = [
    {
        "name": "reset_state",
        "description": "Сбрасывание текущего состояния диалога с чат-ботом, очистка истории сообщений",
    },
    {
        "name": "text_prompt",
        "description": "Запрос чат-боту бизнес-аналитику",
    },
    {
        "name": "rate_chat",
        "description": "Оценка диалога с чат-ботом"
    }
]

app = FastAPI()

app = FastAPI(
    title="Умный Ассистент",
    description="""
Умный корпоративный ассистент для помощи в решении бизнес-задач.\n\n<a href='/docs/example/'>Check Example</a>
""",
    version="0.0.2",
    openapi_tags=tags_metadata
)
