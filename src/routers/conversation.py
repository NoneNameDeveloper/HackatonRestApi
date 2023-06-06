import typing

from src.app import app

from pydantic import BaseModel

from src.data import config
from src.engine import complete, generate, handle_user_message
from src.models import crud, Rule, Conversation

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

@app.get("/conversation")
async def get_conversation(id: int):
    return Conversation.get_by_id(id)
    

@app.get("/text_prompt", tags=["text_prompt"], response_model=ResponseModel)
async def get_prompt_handler(user_id: int, text: str, token: str):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # проверка пользователя, если не существует - создаем
    if not crud.get_user(user_id):
        crud.create_user(user_id, token)

    rules = Rule.select(Rule.filter_text).where(Rule.company_id == company.company_id)

    response = ""
    btns = ["Меню"]

    for rule in rules:
        for word in rule.filter_text.split(" "):
            if word.lower() in text.lower():
                response = "В вопросе содержатся недопустимые слова.\n" + rule.filter_text
                break

    conversations = crud.get_conversation(user_id=user_id)
    user = crud.get_user(user_id)

    if not response:
        response, btns = handle_user_message(user, text, conversations)
    # response += "\nВарианты ответа:\n" + "\n".join(btns)
    crud.update_history_state(user_id, user.history_state)

    # лимит ChatGPT достигнут
    if not response:
        return JSONResponse(status_code=500, content={"status": "INTERNAL_ERROR"})

    # добавление действия в бд
    conversation = crud.create_conversation(user_id, company.company_id, text, response)

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "id_": conversation.conversation_id, "result": response, "variants": btns})

@app.get("/g")
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
async def rate_chat_handler(token: str, user_id: int, rate: int):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # проставляем оценки
    conversations: int = crud.rate_conversation(user_id=user_id, rate=rate)

    # если нет активного флоу
    if conversations == 0:
        return JSONResponse(status_code=200, content={"status": "NOTHING_TO_RATE"})

    # вытягиваем результирующие вопросы ответы уже оцененные
    conversations_list = crud.get_conversation(user_id)
    # собираем отдельные вопрос-ответы в одну сессию
    crud.create_session(conversations_list)

    # деактивируем все вопрос-ответы (сбрасываем состояние сессии)
    crud.deactivate_conversations(user_id)

    return JSONResponse(status_code=200, content={"status": "SUCCESS"})