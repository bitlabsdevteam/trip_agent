from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
import os

# Import the tools from the tools package
from .tools import tools

class Agent:
    def __init__(self):
        # Initialize the LLM with GPT-4o
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            output_key="output",  # Explicitly set output_key to resolve warning
            k=5,
            return_messages=True
        )
        
        # Create the prompt template for the React agent
        self.prompt = PromptTemplate.from_template(
            """You are a helpful assistant with access to tools. Use the following tools to answer questions about cities, weather, and local time:

{tools}

When a user asks about a city, you should use all available tools to provide comprehensive information about:
1. Facts about the city using CityFactsTool
2. Current weather in the city using WeatherTool
3. Local time in the city using TimeTool

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (just the city name)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Your final answer should combine all the information you've gathered into a concise, helpful response.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # Create the React agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=self.prompt
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # Increased from 3 to 5 to allow more time for tool usage
            return_intermediate_steps=True
        )
    
    def process_input(self, state):
        user_input = state.get("input", "")
        
        try:
            # Use the React agent to process the input
            result = self.agent_executor.invoke({"input": user_input})
            
            # Extract intermediate steps for transparency
            intermediate_steps = result.get("intermediate_steps", [])
            reasoning_steps = []
            function_calls = []
            
            # Extract the agent's thinking from the output
            output = result.get("output", "I couldn't process your request.")
            
            # Check if the output indicates the agent stopped due to iteration limit
            if output == "Agent stopped due to iteration limit or time limit.":
                # Create a better response by combining the tool observations
                city_facts = ""
                weather_info = ""
                time_info = ""
                
                # Extract information from the intermediate steps
                for step in intermediate_steps:
                    action = step[0]
                    observation = step[1]
                    
                    if action.tool == "CityFactsTool" and isinstance(observation, dict):
                        city_facts = observation.get("summary", "")
                    elif action.tool == "WeatherTool" and isinstance(observation, dict):
                        weather = observation
                        weather_info = f"Currently {weather.get('temperature', '')} and {weather.get('weather', '')}. "
                        weather_info += f"Humidity is {weather.get('humidity', '')} with wind speed of {weather.get('wind_speed', '')}." 
                    elif action.tool == "TimeTool" and isinstance(observation, dict):
                        time = observation
                        time_info = f"The local time is {time.get('datetime', '')} ({time.get('timezone', '')})." 
                
                # Combine all information into a comprehensive response
                if city_facts or weather_info or time_info:
                    output = f"{city_facts}\n\n{weather_info}\n\n{time_info}"
            
            thinking = ""
            
            # Extract the first thought from the agent's reasoning
            if intermediate_steps and hasattr(intermediate_steps[0][0], 'log'):
                thought_parts = intermediate_steps[0][0].log.split('\n')
                if thought_parts and thought_parts[0].startswith("Thought:"):
                    thinking = thought_parts[0].replace("Thought: ", "")
                else:
                    thinking = intermediate_steps[0][0].log
            else:
                thinking = "To help you with your request, I'll gather some relevant information."
            
            # Format the intermediate steps for better readability and extract function calls
            for step in intermediate_steps:
                action = step[0]
                observation = step[1]
                
                # Add to reasoning steps for backward compatibility
                reasoning_steps.append({
                    "thought": action.log,
                    "action": action.tool,
                    "action_input": action.tool_input,
                    "observation": observation
                })
                
                # Create function call in the expected format
                if action.tool in ["WeatherTool", "TimeTool", "CityFactsTool"]:
                    # Extract city from the input
                    city = action.tool_input
                    function_calls.append({
                        "tool": action.tool,
                        "parameters": {"city": city}
                    })
            
            return {
                "response": output,
                "tool_calls": reasoning_steps,
                "reasoning": thinking,
                "function_calls": function_calls
            }
        except Exception as e:
            return {
                "response": f"Error processing request: {str(e)}",
                "tool_calls": [],
                "reasoning": f"Error occurred while processing: {user_input}"
            }
    
    def execute_tools(self, state):
        # This method is kept for compatibility but not used with React agent
        return state