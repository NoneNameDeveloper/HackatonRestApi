import uuid
from .gpt import complete_custom
from .google import search_links
from src.data.config import hints_config
import re
from newspaper import Article
from src.models import User, Conversation, Company, Rule
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
import traceback

LINKS_AMOUNT_PER_QUERY = 10
# LINKS_AMOUNT_TOTAL = 3
LINKS_AMOUNT_TOTAL = 4

executor = ThreadPoolExecutor(4)


class HintsTree:
    nodes = {}
    results = []

    def parse(section):
        text = section.get('text')

        chapter_name = section.get('chapter')
        if chapter_name != "" and not chapter_name:
            raise Exception("Chapter doesn't have a name! " + str(section))
        children = section.get('children')
        prompt_frame = section.get('prompt_frame')
        disclaimer = section.get('prompt_frame')
        children = [HintsTree.parse(c) for c in children or []]

        chapter = {
            'chapter_name': chapter_name,
            'text': text,
            'prompt_frame': prompt_frame,
            'disclaimer': disclaimer,
            'children': children,
        }

        for child in children:
            child['parent_chapter'] = chapter
        HintsTree.nodes[chapter_name.lower()] = chapter
        return chapter


HintsTree.parse(hints_config)

Responder = Callable[[str, list[str], bool], None]


# print(HintsTree.nodes)


def check_rule_violations(conversation: Conversation, message: str):
    # выборка активных правил фильтрации
    rules = Rule.select(Rule.filter_text).where((Rule.company_id == conversation.company_id) & (Rule.archived == False))

    for rule in rules:
        for word in rule.filter_text.split(" "):
            if word.lower() in message.lower():
                conversation.update_response(
                    f"В вопросе содержится недопустимое слово: {word.lower()}.\nПожалуйста, задайте вопрос иначе.", [],
                    True)
                return True
    return False


def handle_user_message(conversation: Conversation, message: str):

    menu_chapter = HintsTree.nodes[""]

    if check_rule_violations(conversation, message):
        return

    chapter_name = conversation.current_chapter or ""
    # print("current chapter is " + chapter_name)
    chapter = HintsTree.nodes.get(chapter_name.lower())
    if not chapter:
        chapter = menu_chapter
        conversation.update_chapter(chapter["chapter_name"])
    
    handled = False

    if message.lower() == 'назад':
        chapter = chapter.get("parent_chapter") or menu_chapter
        conversation.update_current_chapter(chapter['chapter_name'])
        handled = True
    elif message.lower() in ["", "меню", "/start", "отмена"]:
        chapter = menu_chapter
        conversation.update_current_chapter(chapter['chapter_name'])
        handled = True

    for chapter_variant in chapter['children']:
        if chapter_variant['chapter_name'] == message:
            chapter = chapter_variant
            conversation.set_has_answers()
            conversation.update_current_chapter(chapter['chapter_name'])
            handled = True
            break

    if not handled:
        conversation.set_has_answers()
        conversation.update_response("Читаю вопрос...", ["Отмена"], False)
        executor.submit(lambda: generate(message, conversation.update_response, conversation))
        return
    
    chapter_name = chapter['chapter_name']
    chapter_text = chapter.get('text') or ""
    response = (("База знаний tada.team / " + chapter_name + ":\n") if chapter_name else "") + chapter_text
    
    child_chapters = chapter['children'] or []

    # Кнопки - имена глав, на которые можно опуститься
    buttons = [chapter['chapter_name'] for chapter in child_chapters]

    # Добавляем кнопку "Назад" если можно вернуться назад
    if chapter.get('parent_chapter'):
        buttons.append('Назад')

    conversation.update_response(response, buttons, True)
    


# if user.history_state != json.dumps(state):
#     state['previous_state'] = json.loads(user.history_state)
# user.history_state = json.dumps(state)
# return "???", []


# print(hints_config)

def is_valid_question(prompt: str) -> bool:
    return "да" in complete_custom("Отвечай одним словом \"Да\" или \"Нет\"", [
    "Является ли данное предложение адекватным вопросом от клиента к специалисту?\nПредложение: " + prompt]).lower()


def generate(prompt: str, responder: Responder, conversation: Conversation):
    try:
        # print("GPTing prompt: " + prompt)
        # if prompt[0] != "Я":
        #     return "..."
        responder("Читаю вопрос...", ["Отмена"], False)
        if not is_valid_question(prompt):
            responder("Извините, я вас не совсем понял. Пожалуйста, задайте вопрос по-другому или нажмите 'Меню'", ["Меню"],
                    True)
            return
        
        responder("Ищу ответ в базе знаний...", ["Отмена"], False)
        chapters = complete_custom("Отвечай только названия подходящих статей через точку с запятой, ничего больше. Если подходящих статей нет - отвечай \"missing\"", [
            "Есть справочник со следующим списком статей:\n" + "\n".join(HintsTree.nodes.keys()) \
            + "\n\nКакие три статьи из этого справочника пригодятся, чтобы ответить на вопрос:\n" + prompt + "\n\nЕсли подходящих статей нет - ответь \"missing\""])
        
        # print("Подходящие главы: " + chapters)
        
        source_texts = {}
        if not ('missing' in chapters.lower()):
            knowledge_base_text = "\n\n".join([a for a in [(HintsTree.nodes.get(chapter_name.strip().lower()) or {"text":""})["text"] for chapter_name in chapters.split(";")] if a][:3])
            source_texts['База знаний tada.team'] = knowledge_base_text

        # if conversation.context:
        #     source_texts['Предыдущий ответ'] = conversation.context

        responder("Размышляю над вопросом...", ["Отмена"], False)
        # print("Getting search queries...")
        search_queries = get_search_queries(prompt)
        responder("Ищу нужную информацию в интернете...", ["Отмена"], False)

        # print("Searching google...")
        links_black_list = Company.get_by_id(conversation.company_id).url_black_list
        links = [link for s in [search_links(query)[:LINKS_AMOUNT_PER_QUERY] for query in search_queries] for link in s]
        # фильтруем заблокированные
        links = [link for link in links if not next((True for blocked in links_black_list if blocked in link), False)]

        # links = links[:LINKS_AMOUNT_TOTAL]
        # print("Found links:\n" + "\n".join([str(link) for link in links]))
        # print("Reading articles...")
        responder("Выбираю релевантные статьи...", ["Отмена"], False)
        # source_texts = [get_article_text(link) for link in links]
        # source_texts = [text for text in source_texts if text]
        for link in links:
            text = get_article_text(link) or ""
            if len(text) < 10:
                continue
            source_texts[link] = text
            if len(source_texts) >= LINKS_AMOUNT_TOTAL:
                break

        def pl(n, one, two, five):
            t = n % 10
            h = n % 100
            return one if t == 1 and h != 11 else two if n >= 2 and n <= 4 and h // 10 != 1 else five

        # print("Compressing articles")
        responder(f"Читаю {len(source_texts)} {pl(len(source_texts), 'статью', 'статьи', 'статей')}...",
                ["Отмена"], False)

        compression_prompts = []
        for link in source_texts:
            for page in get_compression_prompts(source_texts[link], prompt):
                compression_prompts.append((link, page))

        def compress(p):
            # print("START COMPRESSING " + p[0])
            try:
                rr = complete_custom(p[1]["system"], p[1]["prompt"])
                p[1]["summary"] = "" if "missing" in rr.lower() else rr
            except Exception as e:
                print(e)
            # print("FINISHED COMPRESSING " + p[0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(compress, p) for p in compression_prompts]
            concurrent.futures.wait(futures)

        # summaries = {}
        # for link in source_texts:
        #     summaries[link] = compress_article(source_texts[link], prompt)

        responder("Пишу ответ...", ["Отмена"], False)
        
        final_prompt = "Даны источники информации:"

        sources = []
        i = len(sources)
        current_source_text = ""
        current_url = None
        for p in compression_prompts:
            
            url = p[0]
            if url != current_url:
                if current_url:
                    i += 1
                    sources.append({'url': current_url, 'text': current_source_text, 'number': i})
                current_url = url
                current_source_text = "Текст статьи из интернета.\n"

            current_source_text += "\n" + p[1]["summary"]
        
        sources.append({'url': current_url, 'text': current_source_text, 'number': i + 1})

        final_prompt = "\nДаны источники информации:\n\n" + "\n\n".join([f"ИСТОЧНИК {source['number']}:\n{source['text']}" for source in sources]) +\
            "Ответь на вопрос:\n" + prompt +\
            "\nВ своём ответе указывай ссылки на источники после каждого предложения в формате [1],[2] и т.д"

        # print("Final prompt:\n\n" + final_prompt)

        final_response = complete_custom(
            # "Ты юрист-помощник, вежливо и весело отвечаешь на все вопросы клиентов, сохраняя фактическую точность",
            "Кратко ответь на вопрос.\n\n\nНе начинай фразы с \"В источнике\", \"В тексте\"\nИспользуй все источники, но не перечисляй их по порядку, твои ответы должны быть единым целым.",
            [final_prompt]
        )
        conversation.context = final_response

        final_response += "\n\nИсточники:\n" + "\n".join([str(source["number"]) + ". " + source["url"] for source in sources])


        responder(final_response + "\n\nПридумываю интересные вопросы...", ["Отмена"], False)
        
        suggestions_prompt = "Клиент задал вопрос: \n" + prompt + "\n\nОтвет специалиста:\n" + final_response + "\n\nКакие еще несколько дополнительных вопросов можно создать исходя из данного ответа?" 
        suggestions_response = complete_custom("", [suggestions_prompt])
        suggestions = [re.sub(r'^\d+\.\s+', '', suggestion) for suggestion in suggestions_response.split("\n")]

        responder(final_response + "\n\nВам также может быть интересно:", suggestions, True)
    except Exception as e:
        pass
        # print(traceback.format_exc())

# status_callback(summary, True)
# return summary


def get_compression_prompts(article: str, user_prompt: str) -> str:
    lines = [x for x in article.split("\n") if x.strip()]

    prompts = []

    while lines:
        prompt1 = ""
        i = 0
        for line in lines:
            if len(prompt1) + len(line) > 4000:
                break
            i += 1
            prompt1 += "\n" + line

        prompt1 += "\n\nМожешь вытащить из этого текста информацию, нужную для ответа на вопрос (если релевантная информация отсутствует - ответь \"missing\"): " + user_prompt
        # print(prompt1)
        prompts.append({
            "system": "You are a text summarizer, you keep all the important details. Do not respond any additional words or phrases, only the summary. You respond a single word 'missing' if no relevant information is found",
            "prompt": [prompt1]})
        lines = lines[i:]
    return prompts


def compress_article(input: str, prompt: str) -> str:
    lines = [x for x in input.split("\n") if x.strip()]

    summary = ""

    while lines:
        prompt1 = ""
        i = 0
        for line in lines:
            if len(prompt1) + len(line) > 4000:
                break
            i += 1
            prompt1 += "\n" + line

        prompt1 += "\n\nМожешь вытащить из этого текста информацию, нужную для ответа на вопрос (если релевантная информация отсутствует - ответь \"missing\"): " + prompt

        # n = 1500
        # chunks = [input[i:i+n] for i in range(0, len(input), n)]

        # print(prompt1)

        a = complete_custom(
            "You are a text summarizer, you keep all the important details. Do not respond any additional words or phrases, only the summary. You respond a single word 'missing' if no relevant information is found",
            [prompt1]
        ).replace("missing", "").replace("Missing.", "")
        # print("PARTIAL: " + a)
        summary += "\n" + a
        lines = lines[i:]
    # print("COMPLETED: " + summary)
    return summary


def get_article_text(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        # print("Text of " + url + ": \n" + article.text)
        return article.text
    except Exception as e:
        print(f"Exception parsing article {url}: ", e)
        return None


def get_search_queries(prompt: str) -> str:
    gpt_search_queries = complete_custom(
        "В ответе должен содержаться только список запросов, никакого дополнительного текста. " +
        "Каждый запрос должен быть в фигурных скобках",
        ["Составь от одного до трёх поисковых запросов для поиска источников " +
         "с информацией, необходимых, чтобы отчётливо ответить на следующий вопрос: " + prompt])
    search_queries = re.findall(r'\{([^}]+)\}', gpt_search_queries)
    # print("Search queries: " + str(search_queries))
    return search_queries
