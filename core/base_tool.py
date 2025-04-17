from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel

class ToolInput(BaseModel):
    """Base input model for all tools"""
    pass

class ToolOutput(BaseModel):
    """Base output model for all tools"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for agent"""
        pass
        
    @property
    @abstractmethod 
    def description(self) -> str:
        """Tool description for agent"""
        pass
        
    @abstractmethod
    def execute(self, input: ToolInput) -> ToolOutput:
        """Main execution method"""
        pass