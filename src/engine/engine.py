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
LINKS_AMOUNT_TOTAL = 3

executor = ThreadPoolExecutor(4)


class HintsTree:
    nodes = {}
    results = []

    def parse(section):
        text = section.get('text')

        chapter = section.get('chapter')
        question = section.get('question')
        answer = section.get('answer')

        children = section.get('children')
        id = section.get('id')
        children = [HintsTree.parse(c) for c in children or []]

        hint = {
            'text': text,
            'id': id,
            'children': children,
            'chapter': chapter,
            'answer': answer,
            'question': question
        }
        HintsTree.nodes[id] = hint
        return hint

    def parse_results(root):
        HintsTree.results = root['results']


HintsTree.parse(hints_config)
HintsTree.parse_results(hints_config)

Responder = Callable[[str, list[str], bool], None]


# print(HintsTree.nodes)


def check_rule_violations(conversation: Conversation, message: str):
    rules = Rule.select(Rule.filter_text).where(Rule.company_id == conversation.company_id)

    for rule in rules:
        for word in rule.filter_text.split(" "):
            if word.lower() in message.lower():
                conversation.update_response(
                    f"В вопросе содержится недопустимое слово: {word.lower()}.\nПожалуйста, задайте вопрос иначе.", [],
                    True)
                return True
    return False


def handle_user_message(conversation: Conversation, message: str):
    if check_rule_violations(conversation, message):
        return

    state = json.loads(conversation.history_state) if conversation.history_state else {
        'future_questions': [],
        'current_question': None,
        'current_chapter': 0,
        'previous_state': None,
        'visited_nodes': []
    }
    conversation.history_state = json.dumps(state)

    handled = False

    if message.lower() == 'назад' and state['previous_state']:
        print("Going back from " + str(state) + " to " + str(state['previous_state']))
        state = state['previous_state']
        handled = True
    elif message.lower() in ["", "меню", "/start"]:
        state = {'future_questions': [], 'current_question': None, 'current_chapter': 0, 'previous_state': None,
                 'visited_nodes': []}
        handled = True

    chapter = state['current_chapter']
    chapter = HintsTree.nodes.get(chapter)
    if not chapter:
        chapter = HintsTree.nodes[0]

    print("Current chapter: ", chapter['id'])
    print("User state: ", state)

    if 'current_question' in state and state['current_question']:
        question = HintsTree.nodes[state['current_question']]
        answer = None
        for answer_variant in question['children']:
            if answer_variant['answer'] == message:
                answer = answer_variant
                break
        if answer:
            state['visited_nodes'] += [answer['id']]
            state['current_question'] = None
            state['future_questions'] = [question['id'] for question in answer['children']] + state['future_questions']
            handled = True

    for chapter_variant in chapter['children']:
        if 'chapter' in chapter_variant and chapter_variant['chapter'] == message:
            chapter = chapter_variant
            state['current_chapter'] = chapter['id']
            handled = True

            question_ids = [a['id'] for a in (chapter['children'] or []) if a.get('question')]
            state['future_questions'] = [qid for qid in question_ids] + state['future_questions']
            state['visited_nodes'] += [chapter['id']]

            print("New current chapter: ", chapter['id'])
            break

    chapter_name = chapter['chapter']
    chapter_text = chapter.get('text') or ""
    response = chapter_name + "\n" + chapter_text

    if state['current_question'] or state['future_questions']:

        if state['future_questions'] and not state['current_question']:
            state['current_question'] = state['future_questions'][0]
            state['future_questions'] = state['future_questions'][1:]
        print("Went into question branch")
        question_node = HintsTree.nodes.get(state['current_question'])

        if conversation.history_state != json.dumps(state):
            state['previous_state'] = json.loads(conversation.history_state)
            conversation.history_state = json.dumps(state)

        conversation.update_response(response + "\n" + question_node['question'], [answer['answer'] for answer in
                                                                                   question_node['children']] + (
                                         ['Назад'] if chapter['id'] else []), True)
        return

    next_chapters = [a for a in (chapter['children'] or []) if a.get('chapter')]

    if not handled and chapter['id'] == 0:
        conversation.update_response("Читаю вопрос...", ["Отмена"], False)
        executor.submit(lambda: generate(message, conversation.update_response))
        return
    # todo respong chapter_name and chapter_text in questions
    if next_chapters:

        if conversation.history_state and conversation.history_state != json.dumps(state):
            state['previous_state'] = json.loads(conversation.history_state)
            conversation.history_state = json.dumps(state)

        conversation.update_response(response,
                                     [n['chapter'] for n in next_chapters] + (['Назад'] if chapter['id'] else []), True)
        return

    print("Handled: " + str(handled))
    print("user history 2: " + str(conversation.history_state))
    print("userstate: " + str(state))

    if conversation.history_state != json.dumps(state):
        state['previous_state'] = json.loads(conversation.history_state)
        conversation.history_state = json.dumps(state)
    print("visited: " + str(state['visited_nodes']))

    results = [r['text'] for r in HintsTree.results if set(r['nodes']).issubset(set(state['visited_nodes']))]
    conversation.update_response("Информация в базе знаний tada.team: \n" + "\n".join(results), ['Назад'], True)


# if user.history_state != json.dumps(state):
#     state['previous_state'] = json.loads(user.history_state)
# user.history_state = json.dumps(state)
# return "???", []


# print(hints_config)

def is_valid_question(prompt: str) -> bool:
    return "да" in complete_custom("Отвечай одним словом \"Да\" или \"Нет\"", [
    "Является ли данное предложение адекватным вопросом от клиента к специалисту?\nПредложение: " + prompt]).lower()


def generate(prompt: str, responder: Responder):
    try:
        print("GPTing prompt: " + prompt)
        # if prompt[0] != "Я":
        #     return "..."
        responder("Читаю вопрос...", ["Отмена"], False)
        if not is_valid_question(prompt):
            responder("Извините, я вас не совсем понял. Пожалуйста, задайте вопрос по-другому или нажмите 'Меню'", ["Меню"],
                    True)
            return
        responder("Размышляю над вопросом...", ["Отмена"], False)
        print("Getting search queries...")
        search_queries = get_search_queries(prompt)
        responder("Ищу нужную информацию в интернете...", ["Отмена"], False)
        print("Searching google...")
        links = [link for s in [search_links(query)[:LINKS_AMOUNT_PER_QUERY] for query in search_queries] for link in s]
        # links = links[:LINKS_AMOUNT_TOTAL]
        print("Found links:\n" + "\n".join([str(link) for link in links]))
        print("Reading articles...")
        responder("Выбираю релевантные статьи...", ["Отмена"], False)
        # source_texts = [get_article_text(link) for link in links]
        # source_texts = [text for text in source_texts if text]
        source_texts = {}
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

        print("Compressing articles")
        responder(f"Читаю {len(source_texts)} {pl(len(source_texts), 'статью', 'статьи', 'статей')}...",
                ["Отмена"], False)

        compression_prompts = []
        for link in source_texts:
            for page in get_compression_prompts(source_texts[link], prompt):
                compression_prompts.append((link, page))

        def compress(p):
            print("START COMPRESSING " + p[0])
            try:
                p[1]["summary"] = complete_custom(p[1]["system"], p[1]["prompt"]).replace("missing", "")
            except Exception as e:
                print(e)
            print("FINISHED")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(compress, p) for p in compression_prompts]
            concurrent.futures.wait(futures)

        # summaries = {}
        # for link in source_texts:
        #     summaries[link] = compress_article(source_texts[link], prompt)

        responder("Пишу ответ...", ["Отмена"], False)
        
        sources = []
        final_prompt = "Даны источники информации:"

        i = 1
        current_source_text = ""
        current_url = None
        for p in compression_prompts:
            
            url = p[0]
            if url != current_url:
                if current_url:
                    sources.append({'url': current_url, 'text': current_source_text, 'number': i})
                    i += 1
                current_url = url
                current_source_text = "Текст статьи из интернета.\n"

            current_source_text += "\n" + p[1]["summary"]
        
        sources.append({'url': current_url, 'text': current_source_text, 'number': i})

        final_prompt = "\nОтветь на вопрос:\n" + "\n\n".join([f"ИСТОЧНИК {source['number']}:\n{source['text']}" for source in sources]) +\
            "\nВ своём ответе указывай ссылки на источники после каждого предложения в формате [1],[2] и т.д"

        # final_prompt = "\n\n".join(
        #     [p[1]["summary"] + "\nИсточник: " + p[0] for p in compression_prompts if (p[1]["summary"] or "").strip()])

        final_response = complete_custom(
            # "Ты юрист-помощник, вежливо и весело отвечаешь на все вопросы клиентов, сохраняя фактическую точность",
            "Ты юрист",
            [final_prompt]
        )

        final_response += "\n\nИсточники:\n" + "\n".join([str(source["number"]) + ". " + source["url"] for source in sources])
        responder(final_response, ["точно?"], True)
    except Exception as e:
        print(traceback.format_exc())

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
    print("Search queries: " + str(search_queries))
    return search_queries
