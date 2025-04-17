import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel

class ChatMessage(BaseModel):
    timestamp: str
    query: str
    response: str

class HistoryService:
    def __init__(self, storage_path: str = "chat_history.json"):
        self.storage_path = Path(storage_path)
        self.history: List[ChatMessage] = self._load_history()

    def _load_history(self) -> List[ChatMessage]:
        """Load chat history from file"""
        if not self.storage_path.exists():
            return []
            
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [ChatMessage(**item) for item in data]

    def save_message(self, query: str, response: str) -> None:
        """Save new chat message"""
        new_message = ChatMessage(
            timestamp=datetime.now().isoformat(),
            query=query,
            response=response
        )
        self.history.append(new_message)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump([msg.dict() for msg in self.history], f, indent=2, ensure_ascii=False)

    def get_recent_messages(self, count: int = 3) -> List[Dict]:
        """Get recent messages as dictionaries"""
        return [msg.dict() for msg in self.history[-count:]]

    def clear_history(self) -> None:
        """Clear chat history"""
        self.history = []
        if self.storage_path.exists():
            self.storage_path.unlink()