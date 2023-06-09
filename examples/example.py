import time

import requests

# ссылка на апи
host = "http://greed.implario.net:8095"


def new_conversation(user_id: int, initial_message: str, token: str):
    """
    Создание нового диалога с чат-ботом, ответ на сообщение с текстом initial_message
    """
    payload_data = {
        "user_id": user_id,
        "initial_message": initial_message,
        "token": token
    }

    r = requests.post(
        url=host + "/new_conversation", params=payload_data
    )

    if r.status_code == 200:
        return r.json()


def get_conversation(conversation_id: int, token: str):
    """
    Получение информации о текущем диалоге, о состоянии ответа в частности
    """
    payload_data = {
        "conversation_id": conversation_id,
        "token": token
    }

    r = requests.get(
        url=host + "/get_conversation", params=payload_data
    )

    if r.status_code == 200:
        return r.json()


def rate_chat(conversation_id: int, token: str, rate: int) -> bool:
    """
    Оценивание диалога с чат-ботом по пятибальной шкале
    """
    data = {
        "token": token,
        "conversation_id": conversation_id,
        "rate": rate
    }
    r = requests.put(host + "/rate_chat", params=data)

    if r.status_code == 200:
        return True


def main():
    # токен компании, к которой вы принадлежите
    token = "companitoken"

    # ваш уникальный идентификатор в компании
    user_id = 2

    # создание диалога и вопрос чат-боту произвольный
    conversation = new_conversation(user_id, "Какой максимальный срок лишения свободы в РФ?", token)

    # получение ID диалога
    conversation_id = conversation["conversation"]["conversation_id"]

    # флаг для определения того, сформирован ответ или нет
    answered = False

    # цикл для проверки статуса ответа от чат-бота (сгенерирован/не сгенерирован)
    while not answered:
        # запрос на получение статуса ответа
        conversation_data = get_conversation(conversation_id, token)

        # ответ сгенерировался
        if conversation_data['conversation']['response_finished']:
            answered = True

        # вывод статуса генерации
        # print(conversation_data["conversation"]["response_text"])

        # пауза 2 секунды между обновлениями статуса
        time.sleep(2)

    # текст вопроса
    question = conversation_data["conversation"]["last_user_message"]
    # текст ответа на вопрос от чат-бота
    answer = conversation_data["conversation"]["response_text"]

    print("Question: " + question)
    print("\nAnswer: " + answer)

    # оценка чат-бота по пятибальной шкале
    rate_chat(conversation_id, token, 5)


main()
