"""Tools module for LangChain.

This tool potential to convert to a MCP call
"""

from langchain.agents import Tool

# Import the tools from the individual tool files
from .weather_tool import get_weather, WeatherTool
from .time_tool import get_time, TimeTool
from .city_facts_tool import get_city_facts, CityFactsTool

# Create tool instances using the imported classes
weather_tool = WeatherTool()
time_tool = TimeTool()
city_facts_tool = CityFactsTool()

# Define tools as Tool instances for the agent
weather_tool_for_agent = Tool(
    name="WeatherTool",
    description="Get weather information for a specific city. Input should be a city name.",
    func=lambda city: get_weather(city)
)

time_tool_for_agent = Tool(
    name="TimeTool",
    description="Get current time information for a specific city. Input should be a city name.",
    func=lambda city: get_time(city)
)

city_facts_tool_for_agent = Tool(
    name="CityFactsTool",
    description="Get interesting facts and information about a city. Input should be a city name.",
    func=lambda city: get_city_facts(city)
)

# List of tools available to the agent
tools = [weather_tool_for_agent, time_tool_for_agent, city_facts_tool_for_agent]