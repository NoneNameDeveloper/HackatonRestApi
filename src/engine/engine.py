import uuid
from .gpt import complete_custom
from .google import search_links
from src.data.config import hints_config
import re
from newspaper import Article
from src.models import User, Conversation, Tree
import json
import concurrent.futures
from typing import Callable

LINKS_AMOUNT_PER_QUERY = 10
LINKS_AMOUNT_TOTAL = 3

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
# print(HintsTree.nodes)

def handle_user_message(user: User, message: str, history: list[Conversation]):

    state = json.loads(user.history_state) if user.history_state else {'future_questions': [], 'current_question': None, 'current_chapter': 0, 'previous_state': None, 'visited_nodes': []}
    user.history_state = json.dumps(state)

    handled = False

    if message.lower() == 'назад' and state['previous_state']:
        print("Going back from " + str(state) + " to " + str(state['previous_state']))
        state = state['previous_state']
        handled = True
    elif message.lower() in ["меню", "/start"]:
        state = {'future_questions': [], 'current_question': None, 'current_chapter': 0, 'previous_state': None, 'visited_nodes': []}
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

        if user.history_state != json.dumps(state):
            state['previous_state'] = json.loads(user.history_state)
            user.history_state = json.dumps(state)

        return response + "\n" + question_node['question'], [answer['answer'] for answer in question_node['children']] + (['Назад'] if chapter['id'] else [])
    
    next_chapters = [a for a in (chapter['children'] or []) if a.get('chapter')]


    if not handled and chapter['id'] == 0:
        return generate(message, lambda x: x), ["Меню"]
    #todo respong chapter_name and chapter_text in questions
    if next_chapters:

        if user.history_state and user.history_state != json.dumps(state):
            state['previous_state'] = json.loads(user.history_state)
            user.history_state = json.dumps(state)

        return response, [n['chapter'] for n in next_chapters] + (['Назад'] if chapter['id'] else [])
    
    print("Handled: " + str(handled))
    print("user history 2: " + str(user.history_state))
    print("userstate: " + str(state))

    if user.history_state != json.dumps(state):
        state['previous_state'] = json.loads(user.history_state)
        user.history_state = json.dumps(state)
    print("visited: " + str(state['visited_nodes']))

    results = [r['text'] for r in HintsTree.results if set(r['nodes']).issubset(set(state['visited_nodes']))]
    return "Результаты: \n" + "\n".join(results), ['Назад', 'Меню']


    # if user.history_state != json.dumps(state):
    #     state['previous_state'] = json.loads(user.history_state)
    # user.history_state = json.dumps(state)
    # return "???", []
    
    

# print(hints_config)

def is_valid_question(prompt: str) -> bool:
    return complete_custom("Отвечай одним словом \"Да\" или \"Нет\"", ["""
    Является ли данное предложение адекватным вопросом от клиента к специалисту?
    Предложение:
    """ + prompt]).lower().includes("да")


def generate(prompt: str, status_callback: Callable[[str, bool], None]) -> str:
    # if prompt[0] != "Я":
    #     return "..."
    status_callback("Читаю вопрос", False)
    if not is_valid_question(prompt):
        status_callback("Извините, я вас не совсем понял. Пожалуйста, задайте вопрос или нажмите 'Меню'", True)
        return
    status_callback("Размышляю над вопросом")
    print("Getting search queries...")
    search_queries = get_search_queries(prompt)
    status_callback("Ищу информацию")
    print("Searching google...")
    links = [link for s in [search_links(query)[:LINKS_AMOUNT_PER_QUERY] for query in search_queries] for link in s]
    # links = links[:LINKS_AMOUNT_TOTAL]
    print("Found links:\n" + "\n".join([str(link) for link in links]))
    print("Reading articles...")
    status_callback("Читаю статьи")
    # source_texts = [get_article_text(link) for link in links]
    # source_texts = [text for text in source_texts if text]
    source_texts = {}
    for link in links:
        text = get_article_text(link)
        if not text or not text.strip():
            continue
        source_texts[link] = text
        if len(source_texts) >= LINKS_AMOUNT_TOTAL:
            break

    print("Compressing articles")
    status_callback("Размышляю над прочитанным")

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

    status_callback("Пишу ответ")
    summary = "\n\n".join([p[1]["summary"] + "\nИсточник: " + p[0] for p in compression_prompts if (p[1]["summary"] or "").strip()])

    # summary = "\n".join(summaries)
    # summary = ""

    # for s in summaries:
    #     summary += summaries[s] + "\nИсточник: " + s 

    # final_response = complete_custom("Ты юрист-помощник, вежливо и весело отвечаешь на все вопросы клиентов, сохраняя фактическую точность", 
    #                                  [summary + "\n\Используя информацию выше, ответь на следующий вопрос: " + prompt]
    #                                  )
    # return final_response
    status_callback(summary, True)
    return summary

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
        print(prompt1)
        prompts.append({"system": "You are a text summarizer, you keep all the important details. Do not respond any additional words or phrases, only the summary. You respond a single word 'missing' if no relevant information is found", "prompt": [prompt1]})
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

        print(prompt1)

        a = complete_custom("You are a text summarizer, you keep all the important details. Do not respond any additional words or phrases, only the summary. You respond a single word 'missing' if no relevant information is found", [prompt1]
                            ).replace("missing", "").replace("Missing.", "")
        print("PARTIAL: " + a)
        summary += "\n" + a
        lines = lines[i:]
    print("COMPLETED: " + summary)
    return summary

def get_article_text(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        print("Text of " + url + ": \n" + article.text)
        return article.text
    except Exception as e:
        print(f"Exception parsing article {url}: ", e)
        return None


def get_search_queries(prompt: str) -> str:
    gpt_search_queries = complete_custom("В ответе должен содержаться только список запросов, никакого дополнительного текста. " +
                                         "Каждый запрос должен быть в фигурных скобках",
                                         ["Составь от одного до трёх поисковых запросов для поиска источников " +
                                         "с информацией, необходимых, чтобы отчётливо ответить на следующий вопрос: " + prompt])
    search_queries = re.findall( r'\{([^}]+)\}', gpt_search_queries)
    print("Search queries: " + str(search_queries))
    return search_queries



# active_tasks = {}

# class Task:
#     self(task_id):
#         self.task_id = task_id


# def create_task(input: str) -> 'Task':
#     task_id = uuid.uuid4()
#     task = Task(task_id)
#     task.status = 'understanding'
#     active_tasks[task_id] = task
#     return task
