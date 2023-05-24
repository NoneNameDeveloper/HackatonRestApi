from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from src.routers import *


tags_metadata = [
    {
        "name": "reset_state",
        "description": "Сбрасывание текущего состояния диалога в ноль, очистка истории сообщений",
    },
    {
        "name": "text_prompt",
        "description": "Запрос чат-боту бизнес-аналитику",
    },
]

app = FastAPI()

app = FastAPI(
    title="Умный Ассистент",
    description="Умный корпоративный ассистент для помощи в решении бизнес-задач",
    version="0.0.1",
    openapi_tags=tags_metadata,
)