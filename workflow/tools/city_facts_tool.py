"""City Facts Tool for LangChain.

This module provides a tool to get facts about cities using the Wikipedia API.
"""

import wikipediaapi
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, tool

class CityFactsInput(BaseModel):
    """Input for the city facts tool."""
    city: str = Field(..., description="The city to get facts about")

class CityFactsTool(BaseTool):
    """Tool that gets facts about cities from Wikipedia."""
    name: str = "city_facts"
    description: str = "Useful for getting information and facts about a specific city. Input should be a city name."
    args_schema: Type[BaseModel] = CityFactsInput
    wiki: Any = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wiki = wikipediaapi.Wikipedia('SalesMakerAgent/1.0 (david@example.com)', 'en')
    
    def _run(self, city: str) -> Dict[str, Any]:
        """Run the city facts tool."""
        try:
            # Search for the city page
            page = self.wiki.page(f"{city}")
            
            # If page doesn't exist, try with 'city'
            if not page.exists():
                page = self.wiki.page(f"{city} city")
            
            # If still doesn't exist, return error
            if not page.exists():
                return {"error": f"Could not find Wikipedia page for {city}"}
            
            # Get the summary (first section)
            summary = page.summary[0:1500]  # Limit to 1500 chars
            
            # Format the city facts
            city_facts = {
                "title": page.title,
                "summary": summary,
                "url": page.fullurl,
                "categories": list(page.categories.keys())[0:5] if page.categories else []  # First 5 categories
            }
            
            return city_facts
        except Exception as e:
            return {"error": f"Error fetching city facts: {str(e)}"}
    
    async def _arun(self, city: str) -> Dict[str, Any]:
        """Run the city facts tool asynchronously."""
        # For simplicity, we're using the synchronous version
        return self._run(city)


@tool
def get_city_facts(city: str) -> Dict[str, Any]:
    """Get facts and information about a specific city from Wikipedia.
    
    Args:
        city: The city to get facts about
        
    Returns:
        Dict containing city information
    """
    city_facts_tool = CityFactsTool()
    return city_facts_tool._run(city)


# Alternative implementation using LangChain's built-in WikipediaQueryRun tool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic.
    
    Args:
        query: The search query
        
    Returns:
        String containing search results
    """
    wikipedia = WikipediaAPIWrapper(top_k_results=1)
    tool = WikipediaQueryRun(api_wrapper=wikipedia)
    return tool.run(query)