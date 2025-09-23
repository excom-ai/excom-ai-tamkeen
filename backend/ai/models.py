from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str