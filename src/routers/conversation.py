from src.app import app

from fastapi import HTTPException

from src.engine import handle_user_message
from src.models import crud, Conversation, Company, User

from fastapi.responses import JSONResponse

def get_company_by_token(token: str) -> Company:
    company = crud.get_company(token)
    if not company:
        raise HTTPException(status_code=403, detail={"status": "INVALID_API_TOKEN"})
    return company


@app.post("/new_conversation")
def new_conversation(token: str, user_id: int, initial_message: str):

    company = get_company_by_token(token)

    user = User.get_or_create(user_id, company.company_id)

    conversation = Conversation.create(user_id=user.user_id, company_id=company.company_id, last_user_message=initial_message, response_text="", response_buttons="[]")

    # Сгенерировать стаартовое сообщение от бота
    handle_user_message(conversation, initial_message)
    conversation.update_history_state()
    
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})
        

@app.get("/get_conversation")
def get_conversation(token: str, conversation_id: int):
    company = get_company_by_token(token)
    conversation = Conversation.get_or_none(Conversation.conversation_id == conversation_id)
    if not conversation or conversation.company_id != company.company_id:
        return JSONResponse(status_code=404, content={"status": "CONVERSATION_NOT_FOUND"})
    
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})


@app.get("/new_user_message", tags=["new_user_message"])
def new_user_message(token: str, user_id: int, conversation_id: int, text: str):

    get_company_by_token(token)

    user = User.get_or_none(User.user_id == user_id)
    if not user:
        return JSONResponse(status_code=404, content={"status": "USER_NOT_FOUND"})

    conversation = Conversation.get_or_none(Conversation.conversation_id == conversation_id)
    if not conversation:
        return JSONResponse(status_code=404, content={"status": "CONVERSATION_NOT_FOUND"})

    handle_user_message(conversation, text)
    conversation.update_history_state()

    # лимит ChatGPT достигнут
    # if not response:
        # return JSONResponse(status_code=500, content={"status": "INTERNAL_ERROR"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "conversation": conversation.to_dto()})


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

    response_message = "Благодарим за обратную связь! Ваша оценка помогает мне стать лучше!"

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "message": response_message})