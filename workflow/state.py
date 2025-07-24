from pydantic import BaseModel
from typing import List, Dict

class AgentState(BaseModel):
    user_input: str
    conversation_history: List[Dict[str, str]] = []
    tool_outputs: List[Dict] = []
    final_response: str = ""