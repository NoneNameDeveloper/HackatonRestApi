import datetime
import hashlib
import secrets
import typing

from . import Conversation, Rule, User
from . import Company


# CONVERSATION
def get_conversation(user_id: int) -> 'typing.Union[list[Conversation], None]':
    """
    получение истории запросов с сортировкой
    по дате сообщений
    """
    conversations = Conversation.get_or_none((Conversation.user_id == user_id) & (Conversation.active == True))

    if conversations is None:
        return conversations

    return Conversation.select().where(Conversation.user_id == user_id).order_by(Conversation.message_date)


def create_conversation(user_id: int, company_id: int, message_body: str, answer_body: str) -> Conversation:
    """
    запись диалога в базу
    """
    return Conversation.create(
        user_id=user_id,
        company_id=company_id,
        message_body=message_body,
        answer_body=answer_body
    )


def deactivate_conversations(user_id: int) -> int:
    """
    деактивация истории переписки
    сброс стейта
    """
    q = Conversation.update({Conversation.active: False}).where(
        (Conversation.user_id == user_id) & (Conversation.active == True))
    res = q.execute()
    return res


# COMPANY
def create_company(company_name: typing.Union[str, None], company_id: int):
    """
    создаем компанию (название компании - не обязательно)
    """
    token = secrets.token_urlsafe(16)  # генерируем 16 значный токен
    token_hash = hashlib.sha256(token.encode()).hexdigest()  # хешируем его
    return Company.create(company_id=company_id, token_hash=token_hash, company_name=company_name), token


def get_company(token: str):
    """
    возвращаем модель компании по токену
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()  # хешируем токен обратно для поиска в бд

    return Company.get_or_none(Company.token_hash == token_hash)


def get_company_by_id(company_id: int) -> typing.Optional[Company]:
    """
    получение данных о компании по ID
    """
    return Company.get_or_none(Company.company_id == company_id)


def delete_company(company_id: int):
    """
    удаляем компанию
    """
    q = Company.delete().where(Company.company_id == company_id)
    q.execute()


# RULES
def create_rule(company_id: int, filter_text: str) -> Rule:
    """
    добавляем правило для компании
    """
    return Rule.create(
        company_id=company_id,
        filter_text=filter_text
    )


def archive_rule(filter_text: str) -> str:
    """
    архивирование правила

    возвращается текст заархиввированного правила
    """
    rule = Rule.get_or_none(Rule.filter_text == filter_text)

    # правило уже заархивировано
    if not rule or rule.archived:
        return "already"

    rule.archived = True
    rule.archive_date = datetime.datetime.now()

    rule.save()

    return rule.filter_text


# URL BLACKLIST
def block_url(uri: str, company_id: int):
    """
    добавление ссылки в черный список компании
    """
    company = Company.get_or_none(Company.company_id == company_id)

    if not company:
        return "COMPANY_DOESNT_EXiSTS"

    company.url_black_list.append(uri)
    company.save()

    return "success"


def unblock_url(uri: str, company_id: int):
    """
    добавление ссылки в черный список компании
    """
    company = Company.get_or_none(Company.company_id == company_id)

    if not company:
        return "error"

    if not uri in company.url_black_list:
        return "error"

    company.url_black_list.remove(uri)
    company.save()

    return "success"


# USERS
def add_user(
        user_id: int,
        company_id: int,
        city: typing.Optional[str],
        industry: typing.Optional[str]
):
    """
    создание пользователя

    пользователь создается после первого
    сообщения в телеграм чате компании - ID компании = ID чата телеграм
    """
    return User.create(
        user_id=user_id,
        company_id=company_id,
        city=city,
        industry=industry
    )


def get_user(user_id: int) -> typing.Union[User, None]:
    """
    получение пользователя из базы
    """
    return User.get_or_none(User.user_id == user_id)


def create_user(user_id: int, token: str):
    """
    создание пользователя и привязка его к компании
    """
    company = get_company(token)

    return User.create(
        user_id=user_id,
        company_id=company.company_id,
    )


def update_history_state(user_id: int, history_state):
    """
    обновление состояния пользователя
    """
    User.update(
        history_state=history_state
    ).where(
        User.user_id == user_id
    ).execute()


def set_status(conversation_id: int, status: str):
    """
    обновление статуса диалога
    """
    # print("Setting status " + status)
    Conversation.update(status=status).where(Conversation.conversation_id == conversation_id).execute()