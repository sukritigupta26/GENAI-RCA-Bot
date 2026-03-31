from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RCAInput(BaseModel):
    source: str
    logs: str
    context: Dict[str, Any] = {}

class AgentMessage(BaseModel):
    role: str
    content: str

class RCAResult(BaseModel):
    rca_summary: str
    actions_taken: List[str]
    status: str  # "resolved" or "needs_human"