"""Time Tool for LangChain.

This tool potential to convert to a MCP call

This module provides a tool to get current time information for cities.
"""

import requests
import datetime
import pytz
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool

# City to timezone mapping
CITY_TIMEZONES = {
    "new york": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "berlin": "Europe/Berlin",
    "beijing": "Asia/Shanghai",
    "moscow": "Europe/Moscow",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "toronto": "America/Toronto",
    "sao paulo": "America/Sao_Paulo",
    "mumbai": "Asia/Kolkata",
    "istanbul": "Europe/Istanbul",
    "rome": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam",
}

class TimeInput(BaseModel):
    """Input for the time tool."""
    city: str = Field(..., description="The city to get time for")

class TimeTool(BaseTool):
    """Tool that gets current time information for cities.
    """
    name: str = "time"
    description: str = "Useful for getting current time information for a specific city. Input should be a city name."
    args_schema: Type[BaseModel] = TimeInput
    
    def _get_timezone(self, city: str) -> Optional[str]:
        """Get timezone for a city."""
        city_lower = city.lower()
        return CITY_TIMEZONES.get(city_lower)
    
    def _run(self, city: str) -> Dict[str, Any]:
        """Run the time tool."""
        # Try to get timezone from our mapping
        timezone_str = self._get_timezone(city)
        
        if not timezone_str:
            # If not in our mapping, try to get from WorldTimeAPI
            try:
                response = requests.get(f"http://worldtimeapi.org/api/timezone/Etc/UTC")
                response.raise_for_status()
                utc_data = response.json()
                
                # Return UTC time with a note that city timezone is not available
                utc_datetime = datetime.datetime.fromisoformat(utc_data["datetime"].replace("Z", "+00:00"))
                
                return {
                    "city": city,
                    "timezone": "UTC",
                    "datetime": utc_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "note": f"Timezone for {city} not found. Showing UTC time instead."
                }
            except requests.exceptions.RequestException as e:
                return {"error": f"Error fetching time data: {str(e)}"}
        
        # Get time for the timezone
        try:
            timezone = pytz.timezone(timezone_str)
            now = datetime.datetime.now(timezone)
            
            time_data = {
                "city": city,
                "timezone": timezone_str,
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "day_of_year": now.strftime("%j"),
                "week_number": now.strftime("%U"),
                "is_dst": bool(now.dst()),
                "utc_offset": now.strftime("%z")
            }
            
            return time_data
        except Exception as e:
            return {"error": f"Error processing time data: {str(e)}"}
    
    async def _arun(self, city: str) -> Dict[str, Any]:
        """Run the time tool asynchronously."""
        # For simplicity, we're using the synchronous version
        return self._run(city)


@tool
def get_time(city: str) -> Dict[str, Any]:
    """Get current time information for a specific city.
    
    Args:
        city: The city to get time for
        
    Returns:
        Dict containing time information
    """
    time_tool = TimeTool()
    return time_tool._run(city)


@tool
def get_current_time(timezone: Optional[str] = None) -> str:
    """Get the current time, optionally in a specific timezone.
    
    Args:
        timezone: The timezone in TZ database format (e.g., 'America/New_York')
        
    Returns:
        Current time as a formatted string
    """
    if timezone:
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return f"Unknown timezone: {timezone}. Using UTC instead."
    else:
        tz = pytz.UTC
    
    now = datetime.datetime.now(tz)
    return now.strftime('%Y-%m-%d %H:%M:%S %Z')