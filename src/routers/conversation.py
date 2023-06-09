import typing

from src.app import app

from pydantic import BaseModel
from fastapi import HTTPException

from src.data import config
from src.engine import generate, handle_user_message
from src.models import crud, Rule, Conversation, Company, User
import concurrent.futures

from fastapi.responses import JSONResponse, PlainTextResponse


class ResponseModel(BaseModel):
    status: str
    id_: typing.Optional[int]
    result: typing.Optional[str]
    variants: typing.Optional[list[str]]

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


def get_company_by_token(token: str) -> Company:
    company = crud.get_company(token)
    if not company:
        raise HTTPException(status_code=403, detail={"status": "INVALID_API_TOKEN"})
    return company


@app.post("/new_conversation")
def new_conversation(token: str, user_id: int):

    company = get_company_by_token(token)

    user = User.get_or_create(user_id, company.company_id)

    conversation = Conversation.create(user_id=user.user_id, company_id=company.company_id, last_user_message="", response_text="", response_buttons="[]")

    # Сгенерировать стаартовое сообщение от бота
    handle_user_message(conversation, "")
    
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})
        

@app.get("/get_conversation")
def get_conversation(token: str, conversation_id: int):
    company = get_company_by_token(token)
    conversation = Conversation.get_or_none(Conversation.conversation_id == conversation_id)
    if not conversation or conversation.company_id != company.company_id:
        return JSONResponse(status_code=404, content={"status": "CONVERSATION_NOT_FOUND"})
    
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})


@app.get("/new_user_message", tags=["new_user_message"], response_model=ResponseModel)
def new_user_message(token: str, user_id: int, conversation_id: int, text: str):

    get_company_by_token(token)

    user = User.get_or_none(User.user_id == user_id)
    if not user:
        return JSONResponse(status_code=404, content={"status": "USER_NOT_FOUND"})

    conversation = Conversation.get_or_none(Conversation.conversation_id == conversation_id)
    if not conversation:
        return JSONResponse(status_code=404, content={"status": "CONVERSATION_NOT_FOUND"})

    handle_user_message(conversation, text)

    crud.update_history_state(user_id, user.history_state)

    # лимит ChatGPT достигнут
    # if not response:
        # return JSONResponse(status_code=500, content={"status": "INTERNAL_ERROR"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})


@app.get("/g", include_in_schema=False)
async def g(prompt: str):
    # return JSONResponse(status_code=200, content=compress_article("Как правильно вести учёт суммированного рабочего времени?"))
    return PlainTextResponse(status_code=200, content=generate(prompt, lambda x,y: x))


@app.get("/reset_state", tags=["reset_state"])
async def reset_state_handler(user_id: int, token: str):

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
async def rate_chat_handler(token: str, conversation_id: int, rate: int):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # проставляем оценки
    conversations: int = crud.rate_conversation(conversation_id=conversation_id, rate=rate)

    # если нет активного флоу
    if conversations == 0:
        return JSONResponse(status_code=200, content={"status": "NOTHING_TO_RATE"})

    # вытягиваем результирующие вопросы ответы уже оцененные
    # conversations_list = crud.get_conversation(user_id)
    # собираем отдельные вопрос-ответы в одну сессию
    # crud.create_session(conversations_list)

    # деактивируем все вопрос-ответы (сбрасываем состояние сессии)
    # crud.deactivate_conversations(user_id)

    response_message = "Благодарим за обратную связь! Ваша оценка помогает доработать слабые стороны системы."

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "message": response_message})