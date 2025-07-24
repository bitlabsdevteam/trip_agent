from langchain.agents import Tool
import datetime
import requests

def get_weather(location: str) -> str:
    """Get weather information for a location"""
    # Placeholder implementation
    return f"The weather in {location} is sunny with 22°C"

def get_time(timezone: str = "UTC") -> str:
    """Get current time for a timezone"""
    current_time = datetime.datetime.now()
    return f"Current time in {timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

def get_city_facts(city: str) -> str:
    """Get interesting facts about a city"""
    # Placeholder implementation
    return f"{city} is a wonderful city with rich history and culture."

# Define tools as Tool instances
weather_tool = Tool(
    name="weather",
    description="Get weather information for a specific location. Input should be a city name.",
    func=get_weather
)

time_tool = Tool(
    name="time",
    description="Get current time for a specific timezone. Input should be a timezone (default: UTC).",
    func=get_time
)

city_facts_tool = Tool(
    name="city_facts",
    description="Get interesting facts about a city. Input should be a city name.",
    func=get_city_facts
)

tools = [weather_tool, time_tool, city_facts_tool]