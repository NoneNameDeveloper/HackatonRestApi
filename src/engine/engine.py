import uuid
from .gpt import complete_custom
from .google import search_links
import re
from newspaper import Article


LINKS_AMOUNT_PER_QUERY = 10
LINKS_AMOUNT_TOTAL = 3

def generate(prompt: str, status_callback) -> str:
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
    summaries = {}
    for link in source_texts:
        summaries[link] = compress_article(source_texts[link], prompt)

    status_callback("Пишу ответ")

    summary = "\n".join(summaries)
    summary = ""

    for s in summaries:
        summary += summaries[s] + "\nИсточник: " + s 

    # final_response = complete_custom("Ты юрист-помощник, вежливо и весело отвечаешь на все вопросы клиентов, сохраняя фактическую точность", 
    #                                  [summary + "\n\Используя информацию выше, ответь на следующий вопрос: " + prompt]
    #                                  )
    # return final_response
    return summary

def compress_article(input: str, prompt: str) -> str:
    # input = """
    # Суммированный учет рабочего времени вводят в организациях из-за специфики деятельности. Разберем, когда его можно ввести, как установить учетный период и оформить процедуру без ошибок
    # Правило 1. Суммированный учет рабочего времени вводят в строго определенных случаях
    # Суммированный учет рабочего времени вводят, когда по условиям производства, работы при выполнении отдельных видов работ не может быть соблюдена установленная для работников ежедневная или еженедельная продолжительность рабочего времени (ст. 104 ТК РФ). Сотрудники, занятые на работах с вредными или опасными условиями труда, — не исключение. Правило касается организаций и индивидуальных предпринимателей.
    # Суммированный учет рабочего времени надо вводить, если:
    # работа круглосуточная;
    # применяется междусменный режим работы;
    # есть работники, которым установлено гибкое рабочее время;
    # при вахтовом методе работы — в этом случае суммированный учет обязателен.
    # Суммированный учет вводят в целом по организации или для определенных категорий работников. Например, проводникам, продавцам, охранникам и др.
    # Некоторым работникам суммированный учет рабочего времени устанавливают на основании нормативных правовых актов органов исполнительной власти. Например, водителям автомобилей устанавливают суммированный учет с учетным периодом в месяц, если им невозможно соблюдать нормы ежедневной или еженедельной продолжительности рабочего времени (п. 8 Приказа Минтранса России от 20.08.2004 № 15).
    # Правило 2. Надо установить учетный период
    # Допускается вводить суммированный учет рабочего времени с тем, чтобы продолжительность рабочего времени за учетный период (месяц, квартал и другие периоды) не превышала нормального числа рабочих часов (ст. 140 ТК РФ). Учетный период не может превышать один год, а для учета рабочего времени работников, занятых на работах с вредными или опасными условиями труда, — трех месяцев.
    # В общем случае учетный период может быть один месяц, два месяца, три месяца и пр. То есть минимальный учетный период составляет один месяц, максимальный — один год.
    # Какой учетный период наиболее оптимальный?
    # Совет: составьте график сменности (см. правило 5) на более длительный период, например на год. И станет видно, за какое количество месяцев общее число рабочих часов наиболее близко к норме, установленной производственным календарем. Этот период целесообразно принять за учетный.
    # Продолжительность учетного периода утверждает руководитель организации.
    # Если в компании вредные или опасные условия труда...
    # Если речь идет о работниках, которые заняты на работах с вредными или опасными условиями труда, учетный период не может превышать трех месяцев. Его можно увеличить до года из-за сезонных или технологических причин. Условие об увеличении должно быть предусмотрено коллективным договором или локальным нормативным актом организации.
    # В конце статьи есть шпаргалка
    # Почему при ведении суммированного учета рабочего времени целесообразно устанавливать не оклад, а часовые тарифные ставки?
    # Комментирует преподаватель Контур.Школы Юлия Бусыгина:
    # Хотите знать больше? Записывайтесь на курс повышения квалификации «Суммированный учет рабочего времени. Коды А, Е. 40 ак. часов». В программе курса: алгоритм установления режимов рабочего времени,
    # порядок введения суммированного учета рабочего времени,
    # оплата труда при суммированном учете,
    # особенности вахтового метода работы. Полная программа курса
    # Правило 3. Продолжительность рабочего времени за учетный период не должна превышать нормальное число рабочих часов
    # Это правило является одним из самых важных при суммированном учете рабочего времени.
    # Из ст. 104 ТК РФ следует, что нормальное число рабочих часов за учетный период определяют из установленной для данной категории работников еженедельной продолжительности рабочего времени.
    # Нормальная продолжительность рабочего времени не может превышать 40 часов в неделю (ст. 91 ТК РФ).
    # рабочего времени не может превышать 40 часов в неделю (ст. 91 ТК РФ). Другую продолжительность рабочего времени в неделю можно установить отдельным категориям работников. Пример: работникам, занятым на работах с вредными и опасными условиями труда, — 36 часов в неделю.
    # За несоблюдение еженедельной нормальной продолжительности рабочего времени компанию могут оштрафовать на сумму от 30 000 руб. до 50 000 руб. Разрабатывая график работы при суммированном учете, учитывайте ограничения, приведенные в ст. 91 ТК РФ. Порядок исчисления нормы рабочего времени на определенные календарные периоды (месяц, квартал, год) в зависимости от установленной продолжительности рабочего времени в неделю утвержден Приказом Минздравсоцразвития России от 13.08.2009 № 588н.
    # При подсчете нормы рабочего времени исключаются периоды, когда работник фактически не работал. Например, был в отпуске, на больничном, в командировке, проходил профессиональное обучение и пр.
    # Если работник в учетном периоде отработал все дни по графику (не был в отпуске, на больничном, в командировке и т.д.), то норма часов за учетный период будет соответствовать норме часов за месяцы этого периода по производственному календарю.
    # Онлайн-курс для кадровика Суммированный учет рабочего времени. Повышение квалификации Посмотреть программу
    # Пример
    # В ООО «Прогресс» работает Алексей Сушкин. Ему установлен суммированный учет рабочего времени. Учетный период — месяц. Этот сотрудник занят на работах с вредными условиями труда. Продолжительность рабочей недели для Алексея не может составлять более 36 часов в неделю.
    # Определим норму рабочего времени в январе 2023 года, если с 9 по 13 января работник был в отпуске:
    # 1. Определяем норму часов на январь. Норма рабочего времени конкретного месяца рассчитывается так: продолжительность рабочей недели (40, 39, 36, 30, 24 и пр.) делится на 5, умножается на количество рабочих дней по календарю пятидневной рабочей недели конкретного месяца. Из полученного количества часов вычитается количество часов, на которое производится сокращение рабочего времени накануне нерабочих праздничных дней (Приказ Минздравсоцразвития России от 13.08.2009 № 588н).
    # 36/5 х 17 рабочих дней = 122,4 ч. — эта цифра совпадает с указанной в производственном календаре.
    # 17 — количество рабочих дней в январе по календарю пятидневной рабочей недели.
    # 2. Определяем норму рабочего времени на январь с учетом времени отпуска. На период отпуска с 9 по 13 января приходится 5 рабочих дней. Норма времени для Алексея Сушкина на январь:
    # 122,4 – (36 / 5 х 5 рабочих дней) = 122,4 — 36 = 86,4 часа.
    # Если учетный период состоит из нескольких месяцев, сначала определяют норму рабочих часов за каждый месяц, а затем полученные результаты складывают. Для работников, работающих неполный рабочий день (смену) или неполную рабочую неделю, нормальное число рабочих часов за учетный период соответственно уменьшается.
    # Правило 4. Правильно оформляйте процедуру
    # Суммированный учет вводится приказом руководителя и фиксируется в правилах внутреннего трудового распорядка. Если в организации есть профсоюз, то важно его мнение о данном режиме рабочего времени.
    # Работников надо обязательно ознакомить с приказом о введении суммированного учета.
    # Правило 5. График работ должен быть обязательно
    # Работники должны знать свой график работы, поэтому наличие такого документа, как график работ, обязательно.
    # Если суммированный учет устанавливается работникам со сменным графиком (то есть предполагается выполнение работы несколькими работниками), то в обязательном порядке должен быть составлен график сменности.
    # График работ и график сменности — разные понятия.
    # Сменная работа — это работа в две, три или четыре смены. Вводится в тех случаях, когда длительность производственного процесса превышает допустимую продолжительность ежедневной работы, а также в целях более эффективного использования оборудования, увеличения объема выпускаемой продукции или оказываемых услуг (ст. 103 ТК РФ). При сменной работе каждая группа сотрудников должна производить работу в течение установленной продолжительности рабочего времени в соответствии с графиком сменности.
    # — это работа в две, три или четыре смены. Вводится в тех случаях, когда длительность производственного процесса превышает допустимую продолжительность ежедневной работы, а также в целях более эффективного использования оборудования, увеличения объема выпускаемой продукции или оказываемых услуг (ст. 103 ТК РФ). При сменной работе каждая группа сотрудников должна производить работу в течение установленной продолжительности рабочего времени в соответствии с графиком сменности. Графики сменности, как правило, являются приложением к коллективному договору. Графики сменности доводятся до сведения работников не позднее чем за один месяц до введения их в действие. То есть если в организации составляется график сменности на июль 2023 года, то не позднее 31 мая 2023 года работников необходимо с ним ознакомить.
    # А вот порядок ознакомления с графиком работ законодательно не установлен, поэтому правилами внутреннего трудового распорядка следует его установить. Следует помнить, что работа в течение двух смен подряд запрещается.
    # """

    #"В организациях вводят суммированный учет рабочего времени в строго определенных случаях, когда по условиям производства не может 
    # быть соблюдена установленная для работников продолжительность рабочего времени. Суммированный учет вводят в целом по организации 
    # или для определенных категорий работников. Учетный период должен быть не менее одного и не более одного года, а для рабочих с вредными 
    # или опасными условиями труда — не более трех месяцев. Продолжительность рабочего времени за учетный период не должна превышать нормальное число 
    # рабочих часов, которое для большинства работников не может превышать 40 часов в неделю. Чтобы установить оптимальный учетный период, необходимо 
    # оставить график сменности на более длительный период, например на год. В ведении суммированного учета рабочего времени целесообразно устанавливать не оклад, 
    # а часовые тарифные ставки."

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
                            ).replace("missing", "")
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
