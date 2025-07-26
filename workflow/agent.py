from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
import os
import warnings
import datetime

# Suppress deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import the tools from the tools package
from .tools import tools, WeatherTool, TimeTool, CityFactsTool
from .prompts import Prompts
from .llm_factory import LLMFactory

class Agent:
    def __init__(self, provider="openai", model_name=None, temperature=0.7, buffer_size=8, summarization_threshold=6, **kwargs):
        """Initialize the Agent with a configurable LLM and RunnableWithMessageHistory.
        
        Args:
            provider: The LLM provider (openai, groq, google)
            model_name: The specific model name to use (defaults to provider's default)
            temperature: The temperature for the LLM
            buffer_size: Maximum number of messages to keep in buffer (default: 8)
            summarization_threshold: Trigger summarization when buffer exceeds this (default: 6)
            **kwargs: Additional arguments to pass to the LLM constructor
        """
        # Initialize the LLM using the factory
        self.llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            **kwargs
        )
        
        # Memory configuration
        self.buffer_size = buffer_size
        self.summarization_threshold = summarization_threshold
        
        # Memory statistics tracking
        self.memory_stats = {
            'total_messages': 0,
            'summarizations_count': 0,
            'buffer_size': buffer_size,
            'summarization_threshold': summarization_threshold,
            'last_summarization': None
        }
        
        # Initialize session-based message history storage
        self.session_histories = {}
        self.current_session_id = "default_session"
        
        # Initialize the default session history
        self.session_histories[self.current_session_id] = ChatMessageHistory()
        
        # Initialize tools
        self.tools = [
            WeatherTool(),
            TimeTool(),
            CityFactsTool()
        ]
        
        # Create the prompt template for the React agent using the Prompts class
        # Create a custom prompt that includes chat history
        react_template = Prompts.get_react_prompt()
        
        # Create a ChatPromptTemplate that works with ReAct format
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", react_template),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}\nThought:{agent_scratchpad}")
        ])
        
        # Create the React agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # Increased from 3 to 5 to allow more time for tool usage
            return_intermediate_steps=True
        )
        
        # Create RunnableWithMessageHistory for memory management
        self.agent_with_history = RunnableWithMessageHistory(
            self.agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    
    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create a ChatMessageHistory for the given session_id."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
        return self.session_histories[session_id]
    
    def save_context_with_stats(self, inputs, outputs, session_id: str = None):
        """Save context to message history and track memory statistics."""
        if session_id is None:
            session_id = self.current_session_id
            
        # Get the session history
        history = self.get_session_history(session_id)
        
        # Add messages to history
        history.add_user_message(inputs.get("input", ""))
        history.add_ai_message(outputs.get("output", ""))
        
        # Update memory statistics
        self.memory_stats['total_messages'] += 2  # human + ai message
        self.memory_stats['last_updated'] = datetime.datetime.now().isoformat()
        
        # Check if we need to summarize (simulate summarization logic)
        current_message_count = len(history.messages)
        if current_message_count > self.summarization_threshold * 2:  # *2 because each exchange is 2 messages
            self.memory_stats['summarizations_count'] += 1
            self.memory_stats['last_summarization'] = datetime.datetime.now().isoformat()
        
        return True
    

    def process_input(self, state, session_id: str = None):
        user_input = state.get("input", "") if isinstance(state, dict) else state
        
        if session_id is None:
            session_id = self.current_session_id
        
        try:
            # Use RunnableWithMessageHistory to process input with conversation context
            result = self.agent_with_history.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            
            # Update memory statistics
            self.save_context_with_stats(
                {"input": user_input},
                {"output": result.get("output", "")},
                session_id=session_id
            )
            

            
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
            error_str = str(e)
            
            # Enhanced error handling with multiple patterns
            import re
            patterns = [
                r'Could not parse LLM output: `([\s\S]+?)`',
                r'Stream error: "Could not parse LLM output: `([\s\S]+?)`',
                r'OUTPUT_PARSING_FAILURE[\s\S]*?`([\s\S]+?)`'
            ]
            
            extracted_content = None
            for pattern in patterns:
                match = re.search(pattern, error_str)
                if match:
                    extracted_content = match.group(1)
                    break
            
            if extracted_content:
                # Enhanced thinking extraction with multiple patterns
                thinking = ""
                response = extracted_content
                
                # Try different thinking tag patterns
                thinking_patterns = [
                    r'<think>([\s\S]*?)</think>',
                    r'<thinking>([\s\S]*?)</thinking>',
                    r'Thought:([\s\S]*?)(?=Action:|Final Answer:|$)'
                ]
                
                for think_pattern in thinking_patterns:
                    thinking_match = re.search(think_pattern, extracted_content, re.IGNORECASE)
                    if thinking_match:
                        thinking = thinking_match.group(1).strip()
                        # Remove thinking content from response
                        response = re.sub(think_pattern, '', extracted_content, flags=re.IGNORECASE).strip()
                        break
                
                # Clean up response content
                response = response.strip()
                if not response:
                    response = "I encountered a parsing error but was able to extract some content. Please try rephrasing your question."
                
                # Save to memory
                try:
                    self.save_context_with_stats({"input": user_input}, {"output": response})
                except Exception as save_error:
                    print(f"Error saving to memory: {save_error}")
                
                return {
                    "response": response,
                    "tool_calls": [],
                    "reasoning": thinking if thinking else "I've gathered information to answer your question.",
                    "function_calls": []
                }
            
            # For other types of errors
            return {
                "response": f"Error processing request: {error_str}",
                "tool_calls": [],
                "reasoning": f"Error occurred while processing: {user_input}"
            }
    
    def execute_tools(self, state):
        # This method is kept for compatibility but not used with React agent
        return state
    
    def set_max_token_limit(self, max_tokens):
        """Set the maximum token limit for the conversation memory.
        
        Args:
            max_tokens (int): Maximum number of tokens to keep in memory buffer
        """
        self.summarization_threshold = max_tokens
        self.memory_stats['summarization_threshold'] = max_tokens
    
    def get_conversation_summary(self, session_id: str = None):
        """Get the current conversation summary, recent messages, and memory statistics.
        
        Returns:
            dict: Dictionary containing summary, recent messages, and statistics
        """
        try:
            if session_id is None:
                session_id = self.current_session_id
                
            # Get the session history
            history = self.get_session_history(session_id)
            recent_messages = history.messages
            
            # Create a simple summary from recent messages (simulate summarization)
            summary = ""
            if len(recent_messages) > self.summarization_threshold:
                summary = f"Conversation with {len(recent_messages)//2} exchanges covering various topics."
            
            # Format history as string for compatibility
            history_str = ""
            for i, msg in enumerate(recent_messages):
                role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
                history_str += f"{role}: {msg.content}\n"
            
            # Update current buffer count in stats
            current_stats = self.memory_stats.copy()
            current_stats['current_buffer_count'] = len(recent_messages)
            current_stats['has_summary'] = bool(summary)
            
            return {
                'summary': summary,
                'recent_messages': recent_messages,
                'history': history_str,
                'buffer_messages': [{'role': 'human' if isinstance(msg, HumanMessage) else 'assistant', 
                                   'content': msg.content} for msg in recent_messages],
                'stats': current_stats
            }
        except Exception as e:
            print(f"Error getting conversation summary: {e}")
            return {
                'summary': '',
                'recent_messages': [],
                'history': '',
                'buffer_messages': [],
                'stats': self.memory_stats
            }
    
    def update_summary(self, session_id: str = None):
        """Manually trigger a summary update.
        
        Returns:
            str: The updated summary
        """
        try:
            if session_id is None:
                session_id = self.current_session_id
                
            # Get the session history
            history = self.get_session_history(session_id)
            
            # Create a summary if we have enough messages
            if len(history.messages) > self.summarization_threshold:
                # Simple summarization logic - in a real implementation, you might use an LLM
                message_count = len(history.messages) // 2  # Divide by 2 since each exchange is 2 messages
                summary = f"Conversation with {message_count} exchanges covering various topics and tool usage."
                
                # Update summarization stats
                self.memory_stats['summarizations_count'] += 1
                self.memory_stats['last_summarization'] = datetime.datetime.now().isoformat()
                
                return summary
            else:
                return "No summary needed yet - conversation is still short."
        except Exception as e:
             print(f"Error updating summary: {e}")
             return ''
    
    def clear_memory(self, session_id: str = None):
        """Clear the conversation memory for a specific session.
        
        Args:
            session_id: The session ID to clear. If None, clears the current session.
        """
        if session_id is None:
            session_id = self.current_session_id
            
        # Clear the session history
        if session_id in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
        
        # Reset memory statistics
        self.memory_stats = {
            'total_messages': 0,
            'summarizations_count': 0,
            'buffer_size': self.buffer_size,
            'summarization_threshold': self.summarization_threshold,
            'last_summarization': None
        }