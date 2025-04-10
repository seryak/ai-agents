Добавим агенту инструменты для работы с файлами и поиска в интернете. Вот модифицированный план:
Шаг 1: Установка дополнительных зависимостей
bash
Copy

pip install duckduckgo-search langchain-community python-dotenv

Шаг 2: Создание инструментов для работы с файлами
2.1. Чтение файлов
python
Copy

from langchain.tools import tool
from pydantic import BaseModel, Field
import os

class ReadFileInput(BaseModel):
    file_path: str = Field(description="Полный путь к файлу")

@tool(args_schema=ReadFileInput, return_direct=False)
def read_file(file_path: str) -> str:
    """Чтение содержимого файла с диска"""
    try:
        if not os.path.exists(file_path):
            return "Файл не существует"
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Ошибка: {str(e)}"

2.2. Запись файлов
python
Copy

class WriteFileInput(BaseModel):
    file_path: str = Field(description="Полный путь к файлу")
    content: str = Field(description="Текст для записи")

@tool(args_schema=WriteFileInput, return_direct=False)
def write_file(file_path: str, content: str) -> str:
    """Запись текста в файл"""
    try:
        # Ограничиваем запись только в разрешенные директории
        allowed_dirs = ["./data", "/tmp"]
        if not any(os.path.abspath(file_path).startswith(os.path.abspath(d)) for d in allowed_dirs):
            return "Нет прав на запись в эту директорию"
            
        with open(file_path, "w") as f:
            f.write(content)
        return "Файл успешно записан"
    except Exception as e:
        return f"Ошибка: {str(e)}"

Шаг 3: Добавление поиска в интернете
3.1. DuckDuckGo (бесплатный, не требует API-ключа)
python
Copy

from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()

3.2. ИЛИ Google Search (через SerpAPI, требует API-ключ)
bash
Copy

pip install google-search-results

python
Copy

from langchain_community.tools import SerpAPIWrapper

search = SerpAPIWrapper(serpapi_api_key="ваш_ключ")

Шаг 4: Собираем все инструменты вместе
python
Copy

tools = [
    read_file,
    write_file,
    Tool(
        name="web_search",
        func=search.run,
        description="Полезен для поиска актуальной информации в интернете"
    ),
    # Ранее созданный инструмент ask_human
    Tool(
        name="ask_human",
        func=ask_human,
        description="Используйте, когда требуется помощь человека"
    )
]

Шаг 5: Настройка агента с новыми инструментами
python
Copy

from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, initialize_agent

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)

Шаг 6: Примеры использования
Чтение + запись файлов:
python
Copy

result = agent.run(
    "Создай файл report.txt в директории ./data с текстом 'Hello World', "
    "затем прочитай его содержимое и скажи, сколько в нем слов"
)
print(result)

Поиск в интернете:
python
Copy

result = agent.run(
    "Найди последние новости о SpaceX и напиши краткий отчет в файл spacex_news.txt"
)
print(result)

Шаг 7: Безопасность и ограничения

    Сэндбокс для файлов:
    python
    Copy

    # В функции write_file добавьте проверку:
    allowed_dirs = ["./data", "/tmp"]  # Только эти директории доступны для записи

    Лимиты на размер файлов:
    python
    Copy

    MAX_FILE_SIZE = 1024 * 1024  # 1 MB
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        return "Файл слишком большой"

    Фильтрация опасных операций:
    python
    Copy

    BANNED_KEYWORDS = ["rm ", "del ", "format "]
    if any(kw in query.lower() for kw in BANNED_KEYWORDS):
        return "Запрещенная операция"


Рекомендации:

    Для продакшн-использования замените ChatOpenAI на локальную модель через LlamaCpp.

    Добавьте аутентификацию в Gradio-интерфейс.

    Используйте векторные базы данных (Chroma, FAISS) для работы с прочитанными файлами.

Этот агент теперь умеет:

    📁 Читать/писать файлы (с ограничениями)

    🌐 Искать в интернете

    🤖 Запрашивать помощь у пользователя

    💬 Отвечать на сложные запросы, комбинируя все возможности!