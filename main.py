from dotenv import load_dotenv
import os
from langchain_deepseek import ChatDeepSeek
from core.agent import LangchainAgent
from tools.file_tools import FileTool
from services.history_service import HistoryService
from langchain_community.tools import DuckDuckGoSearchRun

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.3,
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    # Create tools
    file_tool = FileTool()
    search = DuckDuckGoSearchRun()
    
    # Initialize agent
    agent = LangchainAgent(
        llm=llm,
        tools=[file_tool],
        history_service=HistoryService()
    )
    
    print("🤖 ИИ-агент с deepseek готов к работе!")
    print("Введите 'выход' для завершения\n")
    
    while True:
        query = input("Ваш запрос: ")
        if query.lower() in ['выход', 'exit', 'quit']:
            break
            
        response = agent.run(query)
        print(f"\nОтвет агента: {response}\n")

if __name__ == "__main__":
    main()