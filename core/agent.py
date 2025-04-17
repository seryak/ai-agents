from typing import List, Optional
from langchain.agents import AgentExecutor, initialize_agent
from langchain.tools import Tool
from langchain_core.language_models import BaseLanguageModel
from services.history_service import HistoryService
from tools.file_tools import FileTool
from core.base_tool import BaseTool

class LangchainAgent:
    def __init__(
        self,
        llm: BaseLanguageModel,
        tools: List[BaseTool],
        history_service: Optional[HistoryService] = None
    ):
        self.llm = llm
        self.tools = tools
        self.history_service = history_service or HistoryService()
        
        # Convert tools to langchain format
        langchain_tools = [
            Tool(
                name=tool.name,
                func=lambda input, t=tool: t.execute(input).result,
                description=tool.description
            )
            for tool in tools
        ]
        
        self.agent = initialize_agent(
            langchain_tools,
            llm,
            agent="structured-chat-zero-shot-react-description",
            verbose=True,
            max_iterations=5
        )

    def run(self, query: str) -> str:
        """Execute agent with context from history"""
        context = self._get_context()
        full_query = f"{context}\n\nNew query: {query}" if context else query
        
        try:
            response = self.agent.run(full_query)
            self.history_service.save_message(query, response)
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def _get_context(self) -> str:
        """Get context from recent messages"""
        if not self.history_service:
            return ""
            
        messages = self.history_service.get_recent_messages(3)
        return "\n".join(
            f"User: {msg['query']}\nAI: {msg['response']}"
            for msg in messages
        )