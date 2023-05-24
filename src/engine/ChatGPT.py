import aiohttp

from src.data import config
from src.models import Conversation


class ChatGPT:
    def __init__(self, conversations: list[Conversation]):
        self.api_key = config.OPENAI_KEY

        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        # история сообщений юзера и ассистента из базы
        self.messages = []

        # если какой то диалог велся - восстанавливаем его
        if conversations is not None:
            for conversation in conversations:
                user_message = {"role": "user", "content": conversation.message_body}
                assistant_message = {"role": "assistant", "content": conversation.answer_body}

                self.messages.append(user_message)
                self.messages.append(assistant_message)

    async def process(self, prompt: str) -> str:
        """
        отправка на ChatGPT и получение результата
        :param prompt:
        :type prompt:
        :return:
        :rtype:
        """

        self.messages.append({"role": "user", "content": prompt})

        params = {
            "model": "gpt-3.5-turbo",
            "messages": self.messages
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=self.headers, json=params) as response:

                res = await response.json()

                # лимит чатжпт достингун (сейчас - 3/min)
                if "error" in res.keys():
                    return False


                return res["choices"][0]["message"]["content"]
