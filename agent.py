from langchain.tools import Tool
from langchain.agents import AgentExecutor, initialize_agent, BaseSingleActionAgent, AgentType
from langchain_deepseek import ChatDeepSeek
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List, Tuple, Any, Union
from langchain.schema import AgentAction, AgentFinish
from dotenv import load_dotenv
import os
import re

# Загрузка переменных окружения
load_dotenv()

# Инициализация поиска
search = DuckDuckGoSearchRun()

def validate_file_path(path: str) -> bool:
    """Проверка безопасности пути к файлу"""
    if not path or not isinstance(path, str):
        return False
    if re.search(r'\.\.|/etc/|/root|/var/|/usr/', path):
        return False
    return True

def read_file(file_path: str) -> str:
    """Безопасное чтение файла"""
    if not validate_file_path(file_path):
        return "Ошибка: Недопустимый путь к файлу"
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Ошибка чтения: {str(e)}"

from langchain.tools import StructuredTool, tool
from typing import Optional
import subprocess
import datetime

DANGEROUS_COMMANDS = ['rm', 'chmod', 'chown', 'dd', 'mv', '>', '>>']
SAFE_COMMANDS = ['ls', 'cat', 'grep', 'find', 'pwd', 'echo', 'mkdir']

# Строгие стоп-слова (точное совпадение)
STOP_WORDS_RU = ['стоп', 'прекрати', 'перестань', 'выход', 'заверши', 'остановись', 'хватит']
STOP_WORDS_EN = ['stop', 'exit', 'quit', 'end', 'abort', 'cancel']

def is_stop_command(text: str) -> bool:
    """Проверяет, является ли текст стоп-командой (точное совпадение без учета регистра)"""
    text = text.strip().lower()
    return text in STOP_WORDS_RU or text in STOP_WORDS_EN

def log_command(command: str, output: str):
    """Логирование выполнения команд"""
    with open('command_history.log', 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {command}\n{output}\n\n")

# Коды ошибок пакетных менеджеров
APT_ERRORS = {
    100: "Ошибка конфигурации apt",
    101: "Ошибка блокировки apt",
    102: "Недостаточно прав",
    103: "Сеть недоступна",
    104: "Пакет не найден"
}

SNAP_ERRORS = {
    1: "Ошибка snapd",
    2: "Пакет не найден",
    3: "Недостаточно прав"
}

def analyze_package_error(command: str, error: subprocess.CalledProcessError) -> str:
    """Анализирует ошибки пакетных менеджеров"""
    if 'apt' in command:
        if error.returncode in APT_ERRORS:
            return f"APT ошибка: {APT_ERRORS[error.returncode]}\n{error.stderr}"
        return f"Неизвестная ошибка APT (код {error.returncode}):\n{error.stderr}"
    elif 'snap' in command:
        if error.returncode in SNAP_ERRORS:
            return f"SNAP ошибка: {SNAP_ERRORS[error.returncode]}\n{error.stderr}"
        return f"Неизвестная ошибка SNAP (код {error.returncode}):\n{error.stderr}"
    return f"Ошибка выполнения: {str(error)}"

def request_sudo() -> bool:
    """Запрашивает sudo-права у пользователя"""
    from getpass import getpass
    try:
        password = getpass("Для выполнения команды требуются права sudo. Введите пароль: ")
        test_cmd = f"echo '{password}' | sudo -S true"
        subprocess.run(test_cmd, shell=True, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print("Неверный пароль sudo")
        return False

def execute_command(command: str, ask_for_confirmation: bool = False) -> str:
    """Безопасное выполнение команд с проверкой"""
    # Проверка опасных команд
    if any(cmd in command for cmd in DANGEROUS_COMMANDS):
        if ask_for_confirmation:
            return "Требуется подтверждение для опасной команды"
        human_response = input(f"Выполнить опасную команду: {command}? (y/n): ")
        if human_response.lower() != 'y':
            return "Команда отменена пользователем"
    
    # Проверка необходимости sudo
    if command.startswith('sudo ') and not request_sudo():
        return "Не удалось получить sudo-права"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout if result.stdout else result.stderr
        log_command(command, output)
        return output
    except subprocess.CalledProcessError as e:
        error_msg = analyze_package_error(command, e)
        log_command(command, error_msg)
        return error_msg

def write_file(file_path: str, content: str, create_dirs: bool = False) -> str:
    """Улучшенная запись в файл с созданием директорий"""
    if not validate_file_path(file_path):
        return "Ошибка: Недопустимый путь к файлу"
    
    try:
        if create_dirs:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Файл {file_path} успешно записан"
    except Exception as e:
        return f"Ошибка записи: {str(e)}"

from pydantic import BaseModel, Field

class CommandInput(BaseModel):
    command: str = Field(description="Команда для выполнения")
    ask_for_confirmation: bool = Field(default=False, description="Требовать подтверждение для опасных команд")

command_tool = StructuredTool.from_function(
    func=execute_command,
    name="command_executor",
    description="Выполнение терминальных команд. Опасные команды требуют подтверждения.",
    args_schema=CommandInput
)

write_file_tool = StructuredTool.from_function(
    func=write_file,
    name="write_file",
    description="Запись в файл с автоматическим созданием директорий. Принимает file_path, content и create_dirs."
)

class HelpSeekingAgent(BaseSingleActionAgent):
    def plan(self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs) -> Union[AgentAction, AgentFinish]:
        """Кастомная логика агента с запросом помощи"""
        if intermediate_steps:
            last_response = intermediate_steps[-1][1]
            if any(phrase in last_response.lower() for phrase in ["не уверен", "помогите", "не знаю"]):
                return AgentAction(
                    tool="ask_human",
                    tool_input={"input_text": "Нужна ваша помощь для продолжения!"},
                    log=""
                )
        return super().plan(intermediate_steps, **kwargs)

def ask_human(input_text: str) -> str:
    """Инструмент для запроса помощи у пользователя"""
    answer = input(f"\n🤖 Агент запрашивает помощь: {input_text}\n👉 Ваш ответ: ")
    return f"Пользователь сказал: {answer}"

# Инициализация компонентов
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.3,
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
tools = [
    Tool(
        name="ask_human",
        func=ask_human,
        description="Запрос помощи у человека при неопределенности"
    ),
    Tool(
        name="read_file",
        func=read_file,
        description="Чтение содержимого файла. Вход: путь к файлу."
    ),
    write_file_tool,
    command_tool,
    Tool(
        name="web_search",
        func=search.run,
        description="Поиск информации в интернете. Вход: поисковый запрос."
    )
]

# Создание агента
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=5
)

if __name__ == "__main__":
    print("🤖 ИИ-агент с deepseek готов к работе!")
    print("Введите 'выход' для завершения\n")
    
    while True:
        query = input("Ваш запрос: ")
        if is_stop_command(query):
            break
            
        try:
            response = agent.run(query)
            print(f"\nОтвет агента: {response}\n")
        except Exception as e:
            print(f"Ошибка: {e}")