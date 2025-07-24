from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FunctionCall(BaseModel):
    """Model for a function call made by the agent"""
    tool: str = Field(..., description="The name of the tool that was called")
    parameters: Dict[str, Any] = Field(..., description="The parameters passed to the tool")


class AgentResponse(BaseModel):
    """Model for the agent's response including reasoning and function calls"""
    thinking: str = Field(..., description="The agent's reasoning process")
    function_calls: List[FunctionCall] = Field(default_factory=list, description="List of function calls made by the agent")
    response: str = Field(..., description="The final response to the user")

    class Config:
        json_schema_extra = {
            "example": {
                "thinking": "To help you plan your visit to Paris, I'll first get some facts, then fetch the current weather and time.",
                "function_calls": [
                    {"tool": "CityFactsTool", "parameters": {"city": "Paris"}},
                    {"tool": "WeatherTool", "parameters": {"city": "Paris"}},
                    {"tool": "TimeTool", "parameters": {"city": "Paris"}}
                ],
                "response": "Paris is the capital of France. It's currently 23°C and clear skies. The local time is 2:45 PM."
            }
        }