from src.app import app

from fastapi import Depends

from src.engine import handle_user_message
from src.models import ConversationDto, Conversation, Company, User

from fastapi.responses import JSONResponse
from pydantic import BaseModel
import typing

from src.utils.misc import AccessException, require_company, ConversationNotFoundException


class ConversationResponse(BaseModel):
    status: str
    conversation: typing.Optional[ConversationDto]


class RateResponse(BaseModel):
    conversation: typing.Optional[ConversationDto]
    message: str


@app.exception_handler(AccessException)
async def access_error_handler(request, exc: AccessException):
    return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})


@app.exception_handler(ConversationNotFoundException)
async def access_error_handler(request, exc: AccessException):
    return JSONResponse(status_code=403, content={"status": "CONVERSATION_NOT_FOUND"})


def require_conversation(conversation_id: int):
    conversation = Conversation.get_or_none(Conversation.conversation_id == conversation_id)
    if not conversation:
        raise ConversationNotFoundException()
    return conversation


@app.post("/new_conversation", tags=["Общение с чат-ботом"])
def new_conversation(user_id: int, initial_message: str, company: Company = Depends(require_company)) -> ConversationResponse:
    """
    Начинает новый диалог, отвечает на сообщение, переданное в параметр initial_message.
    """
    user = User.get_or_create(user_id, company.company_id)

    conversation: Conversation = Conversation.create(
        user_id=user.user_id,
        company_id=company.company_id,
        last_user_message=initial_message,
        response_text="",
        response_buttons="[]",
        current_chapter=""
    )

    # Сгенерировать стартовое сообщение от бота
    handle_user_message(conversation, initial_message)

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto().dict()})


@app.get("/get_conversation", tags=["Общение с чат-ботом"])
def get_conversation(
    conversation: Conversation = Depends(require_conversation),
    company: Company = Depends(require_company)
) -> ConversationResponse:
    """
    Возвращает диалог и его текущие значения.
    """
    # Кидаем 404 если диалог принадлежит не той компании, которая запрашивает
    if conversation.company_id != company.company_id:
        raise ConversationNotFoundException()
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto().dict()})


@app.post("/new_user_message", tags=["Общение с чат-ботом"])
def new_user_message(
    text: str,
    conversation: Conversation = Depends(require_conversation),
    company: Company = Depends(require_company)
) -> ConversationResponse:
    """
    Добавление запроса к пользователя к уже существующему диалогу.
    """
    handle_user_message(conversation, text)
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto().dict()})


@app.put("/rate_chat", tags=["Общение с чат-ботом"])
async def rate_chat_handler(
    rate: int,
    level: int = 1,
    conversation: Conversation = Depends(require_conversation),
    company: Company = Depends(require_company)
) -> RateResponse:
    """
    Оценка прошедшего диалога с чат-ботом.
    """
    conversation.set_rate(rate=rate, level=level)
    return JSONResponse(status_code=200, content={
        "status": "SUCCESS",
        "conversation": conversation.to_dto().dict(),
        "message": "Благодарим за обратную связь! Ваша оценка помогает нам стать лучше."
        }
    )
