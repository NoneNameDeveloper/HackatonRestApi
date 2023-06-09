<h1 align="center">Задание к Хакатону ЛЦТ</h1>

<hr>

<h2 align="center"><a href link="https://lk.leaders2023.innoagency.ru">Хакатон "Лидеры цифровой трансформации (ЛЦТ)"</a></h2>
<h3 align="center">Задача 03 - "Умный корпоративный ассистент для помощи в решении бизнес-задач"</h3>

<hr>

<h3>Overview</h3>

<b>Rest API</b> для ведения диалога с чат-ботом "Бизнес консультантом".

Стек технологий:
<ul>
    <li><a href="https://fastapi.tiangolo.com/">FastAPI</a></li>
    <li><a href="https://docs.pydantic.dev/latest/">Pydantic</a></li>
    <li><a href="https://docs.peewee-orm.com/en/latest/">Peewee (PostgreSQL ORM)</a></li>
    <li><a href="https://newspaper.readthedocs.io/en/latest/">Newspaper3k</a></li>
    <li><a href="https://github.com/googleapis/google-api-python-client/blob/main/docs/README.md">Google API Client</a></li>
    <li><a href="https://openai.com/">GPT-3.5</a></li>
</ul>

<hr>
<a name="run"><h3>Запуск</h3></a>

Для запуска требуется python 3.10+
```bash
git clone https://github.com/NoneNameDeveloper/HackatonRestApi
pip install -r requirements.txt
```
Создать config.env (по образцу из config.env.example) и наполнить данными
```bash
cp config.env.example config.env
```
Запуск апи:
```bash
python main.py
```

Запуск тестового бота (предлагается поменять токены):
```bash
cd example-bot
sh start-bot.sh
```
<hr>

<h3><a href="http://greed.implario.net:8095/docs">Документация</a></h3>
![](https://i.ibb.co/2KDjZ9G/image.png)


<hr>

<h3><a href="http://greed.implario.net:8095/docs/example">Пример использования</a></h3>
```python
import time

import requests

# ссылка на апи
host = "http://greed.implario.net:8095"

def new_conversation(user_id: int, initial_message: str, token: str):
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
    token = "company_token"

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
```

<hr>

<h3>Разработчики</h3>
<ul>
    <li><a href="https://t.me/delfikpro">Михаил Примаков</a></li>
    <li><a href="https://t.me/PontiyCoder">Дружинин Юрий</a></li>
    <li><a href="https://t.me/wasodert">Владислав Вержбитский</a></li>
    <li><a href="https://t.me/Polina_Busheva">Полина Бушева</a></li>
</ul>