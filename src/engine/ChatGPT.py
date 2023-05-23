import aiohttp

from src.data import config


class ChatGPT:
    def __init__(self):
        self.api_key = config.OPENAI_KEY

        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def process(self, prompt: str):
        """
        отправка на ChatGPT и получение результата
        :param prompt:
        :type prompt:
        :return:
        :rtype:
        """

        params = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=self.headers, json=params) as response:

                res = await response.json()

                return res["choices"][0]["message"]["content"]