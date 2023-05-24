import typing

from fastapi import HTTPException

from src.app import app

from pydantic import BaseModel

from src.data import config
from src.engine import complete
from src.models import crud

from fastapi.responses import JSONResponse


class ResponseModel(BaseModel):
    status: str
    id_: typing.Optional[int]
    result: typing.Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "status": "SUCCESS",
                "id_": 1,
                "result": "Начиная с 2017 года, президентом Зимбабве является Эммерсон Мнангагва."
            }
        }


class Status(BaseModel):
    status: str


@app.get("/text_prompt", tags=["text_prompt"], response_model=ResponseModel)
async def get_prompt_handler(user_id: int, text: str, token: str):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    conversations = crud.get_conversation(user_id=user_id)

    # chatGPT = ChatGPT(conversations)

    # получение ответа от чатжпт во вопросу
    response = complete(config.ADDITIONAL_PROMPT + text, conversations)

    # лимит ChatGPT достигнут
    if not response:
        return JSONResponse(status_code=500, content={"status": "INTERNAL_ERROR"})

    # добавление действия в бд
    conversation = crud.create_conversation(user_id, company.company_id, text, response)

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "id_": conversation.conversation_id, "result": response})


@app.get("/reset_state", tags=["reset_state"], response_model=ResponseModel)
async def get_prompt_handler(user_id: int, token: str):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # количество отредактированных ячеек
    res = crud.deactivate_conversations(user_id=user_id)
    # если редактировать было нечего
    if res == 0:
        return JSONResponse(status_code=200, content={"status": "NOTHING_TO_RESET"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS"})


@app.get("/rate_chat", tags=["rate_chat"])
async def rate_chat_handler(token: str, user_id: int, rate: int):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # проставлчем оценки
    res = crud.rate_conversation(user_id=user_id, rate=rate)
    # если нет активного флоу
    if res == 0:
        return JSONResponse(status_code=200, content={"status": "NOTHING_TO_RATE"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS"})