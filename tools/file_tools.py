from typing import Optional
from pydantic import BaseModel, Field
import os
import re
from pathlib import Path
from core.base_tool import BaseTool, ToolInput, ToolOutput

class FileReadRequest(ToolInput):
    path: str = Field(..., description="Path to file for reading")
    max_size: Optional[int] = Field(1024*1024, description="Maximum allowed file size in bytes")

class FileWriteRequest(ToolInput):
    path: str = Field(..., description="Path to file for writing")
    content: str = Field(..., description="Content to write")
    create_dirs: bool = Field(False, description="Create directories if not exists")

class FileResponse(ToolOutput):
    content: Optional[str] = None

class FileTool(BaseTool):
    name = "file_operations"
    description = "Tool for reading and writing files with security checks"
    ALLOWED_DIRS = ["./data", "/tmp"]
    BANNED_PATHS = [r'\.\.', '/etc/', '/root', '/var/', '/usr/']
    MAX_FILE_SIZE = 1024 * 1024  # 1MB

    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate file path security"""
        if not path or not isinstance(path, str):
            return False
            
        abs_path = os.path.abspath(path)
        if any(re.search(pattern, abs_path) for pattern in FileTool.BANNED_PATHS):
            return False
            
        return True

    def execute(self, input: ToolInput) -> ToolOutput:
        """Route input to appropriate method"""
        if isinstance(input, FileReadRequest):
            return self.read_file(input)
        elif isinstance(input, FileWriteRequest):
            return self.write_file(input)
        return ToolOutput(success=False, error="Invalid input type")

    def read_file(self, request: FileReadRequest) -> FileResponse:
        """Safely read file with validation"""
        if not FileTool.validate_path(request.path):
            return FileResponse(success=False, error="Invalid file path")
            
        try:
            if os.path.getsize(request.path) > request.max_size:
                return FileResponse(success=False, error="File too large")
                
            with open(request.path, 'r', encoding='utf-8') as f:
                content = f.read()
                return FileResponse(success=True, content=content)
        except Exception as e:
            return FileResponse(success=False, error=str(e))

    def write_file(self, request: FileWriteRequest) -> FileResponse:
        """Safely write file with validation"""
        if not FileTool.validate_path(request.path):
            return FileResponse(success=False, error="Invalid file path")
            
        abs_path = os.path.abspath(request.path)
        if not any(abs_path.startswith(os.path.abspath(d)) for d in FileTool.ALLOWED_DIRS):
            return FileResponse(success=False, error="Not allowed directory")
            
        try:
            if request.create_dirs:
                os.makedirs(os.path.dirname(request.path), exist_ok=True)
                
            with open(request.path, 'w', encoding='utf-8') as f:
                f.write(request.content)
                return FileResponse(success=True)
        except Exception as e:
            return FileResponse(success=False, error=str(e))