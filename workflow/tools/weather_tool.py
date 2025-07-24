"""Weather Tool for LangChain.

This module provides a tool to get weather information using the WeatherAPI.com API.
"""

import os
import requests
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WeatherInput(BaseModel):
    """Input for the weather tool."""
    city: str = Field(..., description="The city to get weather for")
    country: Optional[str] = Field(None, description="The country code (optional)")

class WeatherTool(BaseTool):
    """Tool that gets weather data from WeatherAPI.com."""
    name: str = "weather"
    description: str = "Useful for getting current weather information for a specific city. Input should be a city name."
    args_schema: Type[BaseModel] = WeatherInput
    
    def _run(self, city: str, country: Optional[str] = None) -> Dict[str, Any]:
        """Run the weather tool."""
        api_key = os.getenv("WEATHERAPI_KEY")
        if not api_key:
            return {"error": "WeatherAPI.com API key not found. Please set the WEATHERAPI_KEY environment variable."}
        
        # Check if the API key is not valid
        if not api_key or api_key == "4c6e8f9c9c9e4a9c9c9c9c9c9c9c9c9c":
            return {"error": "Please set a valid WeatherAPI.com API key in your .env file. Sign up at https://www.weatherapi.com/my/ to get a free API key."}
        
        location = f"{city},{country}" if country else city
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Format the weather data
            weather_data = {
                "city": data["location"]["name"],
                "country": data["location"]["country"],
                "temperature": f"{data['current']['temp_c']:.1f}°C",
                "feels_like": f"{data['current']['feelslike_c']:.1f}°C",
                "humidity": f"{data['current']['humidity']}%",
                "pressure": f"{data['current']['pressure_mb']} hPa",
                "weather": data["current"]["condition"]["text"],
                "description": data["current"]["condition"]["text"],
                "wind_speed": f"{data['current']['wind_kph']} km/h"
            }
            
            return weather_data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return {"error": "Invalid WeatherAPI.com API key. Please check your API key and try again."}
            elif e.response.status_code == 403:
                return {"error": "Access to WeatherAPI.com is forbidden. Your API key may have exceeded its quota."}
            else:
                return {"error": f"HTTP error from WeatherAPI.com: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching weather data: {str(e)}"}
    
    async def _arun(self, city: str, country: Optional[str] = None) -> Dict[str, Any]:
        """Run the weather tool asynchronously."""
        # For simplicity, we're using the synchronous version
        return self._run(city, country)


@tool
def get_weather(city: str, country: Optional[str] = None) -> Dict[str, Any]:
    """Get current weather information for a specific city.
    
    Args:
        city: The city to get weather for
        country: The country code (optional)
        
    Returns:
        Dict containing weather information
    """
    weather_tool = WeatherTool()
    return weather_tool.invoke({"city": city, "country": country})