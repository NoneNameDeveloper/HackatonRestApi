const codeExample = document.getElementById('code');
const languageSelect = document.getElementById('language');

const selectedLanguage = languageSelect.value;

if (selectedLanguage === 'javascript') {
  const code = `const url = 'https://api.example.com';
    
fetch(url)
.then(response => response.json())
.then(data => {
  console.log(data);
});`;

  codeExample.textContent = code;
  codeExample.className = "language-js"

} else if (selectedLanguage === 'python') {
  const code = `import requests

# ссылка на апи
host = "http://greed.implario.net:8081"


def ask(user_id: int, token: str, question: str) -> dict:
    """
    запрос на получение ответа от ассистента

    question: текст вашего вопроса
    """
    data = {
        "token": token,
        "user_id": user_id,
        "text": question
    }
    r = requests.get(url=host + "/text_prompt", params=data)

    # статус ответа - успешный
    if r.status_code == 200:
        return r.json()


def reset_state(user_id: int, token: str) -> bool:
    """
    сброс истории диалога (состояния флоу) 
    """
    data = {
        "token": token,
        "user_id": user_id
    }
    r = requests.get(host + "/reset_state", params=data)

    if r.status_code == 200:
        return True


def rate_chat(user_id: int, token: str, rate: int) -> bool:
    """
    сброс истории диалога (состояния флоу)

    rate: оценка, которую вы ставите сервису (1-5)
    """
    data = {
        "token": token,
        "user_id": user_id,
        "rate": rate
    }
    r = requests.get(host + "/rate_chat", params=data)

    if r.status_code == 200:
        return True


def main():
    # токен компании, к которой вы принадлежите
    token = "test"

    # ваш уникальный идентификатор в компании
    user_id = 2

    res_1 = ask(user_id, token, "Какая статья идет после 231 статьи УК РФ?")  # первый ответ
    res_2 = ask(user_id, token, "А после 198?")  # второй ответ, учитывая предыдущий

    reset_state(user_id, token)  # история сбросилась

    res_reseted = ask(user_id, token, "Какое право имеет жена на квартиру, купленную мужем?")  # первый ответ

    rate_chat(user_id, token, 5)  # оценка ассистента на 5 баллов

    print(res_1)
    print(res_2)
    print(res_reseted)

main()
`;

  codeExample.textContent = code;
  codeExample.className = "language-python"


} else if (selectedLanguage === 'ruby') {
    const code = `require 'net/http'
require 'json'

url = 'https://api.example.com'
uri = URI(url)
response = Net::HTTP.get(uri)
data = JSON.parse(response)
puts data`;

  codeExample.textContent = code;
  codeExample.className = "language-ruby"

} else {
  codeExample.textContent = '';
}

hljs.highlightAll();



languageSelect.addEventListener('change', () => {
  const selectedLanguage = languageSelect.value;

  if (selectedLanguage === 'javascript') {
    const code = `const url = 'https://api.example.com';
      
fetch(url)
  .then(response => response.json())
  .then(data => {
    console.log(data);
  });`;

    codeExample.textContent = code;
    codeExample.className = "language-js"

  } else if (selectedLanguage === 'python') {
    const code = `import requests

# ссылка на апи
host = "http://greed.implario.net:8081"


def ask(user_id: int, token: str, question: str) -> dict:
    """
    запрос на получение ответа от ассистента

    question: текст вашего вопроса
    """
    data = {
        "token": token,
        "user_id": user_id,
        "text": question
    }
    r = requests.get(url=host + "/text_prompt", params=data)

    # статус ответа - успешный
    if r.status_code == 200:
        return r.json()
`;

    codeExample.textContent = code;
    codeExample.className = "language-python"


  } else if (selectedLanguage === 'ruby') {
    const code = `require 'net/http'
require 'json'

url = 'https://api.example.com'
uri = URI(url)
response = Net::HTTP.get(uri)
data = JSON.parse(response)
puts data`;

    codeExample.textContent = code;
    codeExample.className = "language-ruby"

  } else {
    codeExample.textContent = '';
  }

  hljs.highlightAll();
});