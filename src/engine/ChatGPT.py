import aiohttp

from src.data import config
from src.models import Conversation
import openai

openai.api_key = config.OPENAI_KEY
# print(openai.Model.list())

def complete(prompt: str, conversations: 'list[Conversation]') -> str:
    messages = [
        {"role": "system", "content": "Ты робот-помощник, старающийся ответить на вопросы с максимальной точностью. Твои знания о большинсте правовых актов устарели, опирайся только на присланные тебе мною"}
    ]
    if conversations is not None:
        for conversation in conversations:
            messages.append({"role": "user", "content": conversation.message_body})
            messages.append({"role": "assistant", "content": conversation.answer_body})

    messages.append({"role": "user", "content": prompt})

    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

    response = chat_completion.choices[0].message.content
    # response = openai.Completion.create(model="text-davinci-003", prompt="Вопрос: Что нужно, чтобы уволить сотрудника по инициативе компании?\n\nОтвет: ").choices[0].text
    print("openai: ", response)
    return response

def google():
    pass
