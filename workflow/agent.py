from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
import os

# Import the tools from the tools package
from .tools import tools
from .prompts import Prompts
from .llm_factory import LLMFactory

class Agent:
    def __init__(self, provider="openai", model_name=None, temperature=0.7, **kwargs):
        """Initialize the Agent with a configurable LLM.
        
        Args:
            provider: The LLM provider (openai, groq, google)
            model_name: The specific model name to use (defaults to provider's default)
            temperature: The temperature for the LLM
            **kwargs: Additional arguments to pass to the LLM constructor
        """
        # Initialize the LLM using the factory
        self.llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            **kwargs
        )
        
        # Initialize memory with summary buffer to remember conversation history
        # This combines buffer memory with summarization for better long-term retention
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,  # Use the same LLM for summarization
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            max_token_limit=2000  # Adjust token limit based on your needs
        )
        
        # Create the prompt template for the React agent using the Prompts class
        self.prompt = PromptTemplate.from_template(Prompts.get_react_prompt())
        
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
            
            # Explicitly save the context to ensure the summary is updated
            # This is redundant for the current interaction (already saved by invoke)
            # but ensures the summary is properly maintained
            output = result.get("output", "I couldn't process your request.")
            self.memory.save_context({"input": user_input}, {"output": output})
            
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
    
    def update_summary(self):
        """Manually update the conversation summary.
        
        This method forces the memory to generate a new summary based on the current
        conversation history. This can be useful for debugging or for explicitly
        updating the summary at specific points.
        
        Returns:
            str: The new summary
        """

        try:
            # Get the current messages from chat history
            messages = self.memory.chat_memory.messages
            
            # Get the current summary
            previous_summary = self.memory.moving_summary_buffer
            
            # Predict a new summary
            new_summary = self.memory.predict_new_summary(messages, previous_summary)
            
            # Update the moving summary buffer
            self.memory.moving_summary_buffer = new_summary
            
            return new_summary
        except Exception as e:
            return f"Error updating summary: {str(e)}"
    
    def set_max_token_limit(self, max_token_limit):
        """Set the maximum token limit for the conversation buffer.
        
        This controls how many tokens from recent conversations are kept in full detail
        before being summarized. A higher limit means more detailed context but uses more tokens.
        
        Args:
            max_token_limit (int): The maximum number of tokens to keep in the buffer
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.memory.max_token_limit = max_token_limit
            # Force a pruning of the buffer to apply the new limit
            self.memory.prune()
            return True
        except Exception as e:
            print(f"Error setting max token limit: {str(e)}")
            return False
        
    def get_conversation_summary(self):
        """Get the current summary of the conversation history.
        
        Returns:
            dict: A dictionary containing the conversation summary and/or recent messages
        """

        try:
            # Load memory variables which will contain the summary and recent messages
            memory_vars = self.memory.load_memory_variables({})
            
            # If using return_messages=True, we'll get a list of message objects
            if self.memory.return_messages:
                # Extract the conversation summary from the moving_summary_buffer
                summary = self.memory.moving_summary_buffer
                
                # Get the recent messages that haven't been summarized yet
                recent_messages = memory_vars.get("chat_history", [])
                
                return {
                    "summary": summary,
                    "recent_messages": recent_messages
                }
            else:
                # If not using message objects, just return the history string
                return {"history": memory_vars.get("chat_history", "")}
        except Exception as e:
            return {"error": f"Error retrieving conversation summary: {str(e)}"}