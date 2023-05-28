
from src.data import config
from src.models import Conversation
import openai



openai_keys = [
    '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',
    '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',
    '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'
]

openai_key_index = 0

def complete_chat(prompt: str, conversations: 'list[Conversation]') -> str:
    global openai_key_index
    global openai_keys
    openai_key_index += 1
    if openai_key_index >= len(openai_keys):
        openai_key_index = 0
    openai.api_key = openai_keys[openai_key_index]
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
    print("openai: ", response)
    return response

def complete_custom(system: str, prompt: list[str]) -> str:
    global openai_key_index
    global openai_keys

    openai_key_index += 1
    if openai_key_index >= len(openai_keys):
        openai_key_index = 0
    openai.api_key = openai_keys[openai_key_index]
    
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=
        [{"role":"system","content":system}] + [{"role":"user","content":p} for p in prompt]
    )

    response = chat_completion.choices[0].message.content
    print("openai: ", response)
    return response