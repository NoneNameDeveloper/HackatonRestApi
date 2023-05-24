import typing

from fastapi import HTTPException
from pydantic import BaseModel

from src.data import config
from src.engine import ChatGPT
from src.models import crud, Conversation

from src.app import app


@app.get("/company/create", include_in_schema=False)
async def start_conversation_handler():
    """
    создание компании (ТЕСТ)
    """
    company = crud.create_company("ООО Тестирование")
    return {"status": "SUCCESS", "company_token": company[1]}
