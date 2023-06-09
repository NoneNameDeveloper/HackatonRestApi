<h1 align="center">Задание к Хакатону ЛЦТ</h1>
<hr>
<h2 align="center"><a href link="https://lk.leaders2023.innoagency.ru">Хакатон "Лидеры цифровой трансформации (ЛЦТ)"</a></h2>
<h3 align="center">Задача 03 - "Умный корпоративный ассистент для помощи в решении бизнес-задач"</h3>
<hr>
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
<h3>Запуск</h3>

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
<h3>Разработчики</h3>
<ul>
    <li><a href="https://t.me/delfikpro">Михаил Примаков</a></li>
    <li><a href="https://t.me/PontiyCoder">Дружинин Юрий</a></li>
    <li><a href="https://t.me/wasodert">Владислав Вержбитский</a></li>
    <li><a href="https://t.me/Polina_Busheva">Полина Бушева</a></li>
</ul>