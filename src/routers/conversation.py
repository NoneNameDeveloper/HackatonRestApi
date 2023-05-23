import typing

from fastapi import HTTPException
from pydantic import BaseModel

from src.data import config
from src.engine import ChatGPT
from src.models import crud, Conversation, ConversationStart

from src.app import app


class ConversationStartedModel(BaseModel):
    """
    возврат айди чата, по которому можно продолжить общение
    с ботом
    """
    id_: str


@app.get("/conversation/start", response_model=ConversationStartedModel)
async def start_conversation_handler():
    """
    Начинает диалог с ассиснентом. Возвращается id_, который будет служить идентификатором текущего диалога.
    """

    conversation = ConversationStart()
    started_conv: ConversationStart = conversation.create()

    return ConversationStartedModel(id_=str(started_conv.conversation_id))


class ConversationResponse(BaseModel):
    id_: str
    response_body: str


@app.get("/conversation/ask", response_model=ConversationResponse)
async def ask_handler(id_: str, message: str):

    # проверка на существование такого чата
    conversation: ConversationStart = crud.get_conversation(id_)

    if conversation is None:
        return HTTPException(status_code=403, detail="wrong conversation id")

    # получение ответа от чатжпт во вопросу
    chat_gpt = ChatGPT()
    response = await chat_gpt.process(message + config.ADDITIONAL_PROMPT)

    # добавление действия в бд
    Conversation.create(
        conversation_id=conversation.conversation_id,
        message_body=message,
        answer_body=response
    )

    return ConversationResponse(
        id_=str(conversation.conversation_id),
        response_body=response
    )

