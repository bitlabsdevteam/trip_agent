from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import os
import warnings

# Suppress deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
        
        # Initialize modern chat message history
        self.chat_history = ChatMessageHistory()
        self.conversation_summary = ""
        self.max_messages = 10  # Keep last 10 messages before summarizing
        
        # Create a simple memory interface for backward compatibility
        class MemoryInterface:
            def __init__(self, agent_instance):
                self.agent = agent_instance
                
            def load_memory_variables(self, inputs):
                # Return conversation history as string for compatibility
                messages = self.agent.chat_history.messages
                if not messages:
                    return {'history': ''}
                
                # Format messages as conversation string
                history_str = ""
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        history_str += f"Human: {msg.content}\n"
                    elif isinstance(msg, AIMessage):
                        history_str += f"AI: {msg.content}\n"
                
                return {'history': history_str}
            
            def save_context(self, inputs, outputs):
                # Add messages to chat history
                user_input = inputs.get('input', '')
                ai_output = outputs.get('output', '')
                
                if user_input:
                    self.agent.chat_history.add_user_message(user_input)
                if ai_output:
                    self.agent.chat_history.add_ai_message(ai_output)
                
                # Summarize if we have too many messages
                if len(self.agent.chat_history.messages) > self.agent.max_messages:
                    self.agent._summarize_conversation()
            
            def clear(self):
                self.agent.chat_history.clear()
                self.agent.conversation_summary = ""
            
            @property
            def moving_summary_buffer(self):
                return self.agent.conversation_summary
            
            @property
            def chat_memory(self):
                return self.agent.chat_history
        
        self.memory = MemoryInterface(self)
        
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
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # Increased from 3 to 5 to allow more time for tool usage
            return_intermediate_steps=True
        )
    
    def _summarize_conversation(self):
        """Summarize the conversation when it gets too long."""
        try:
            messages = self.chat_history.messages
            if len(messages) <= 2:
                return
            
            # Create a summary of the conversation
            conversation_text = ""
            for msg in messages[:-2]:  # Keep the last 2 messages
                if isinstance(msg, HumanMessage):
                    conversation_text += f"Human: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    conversation_text += f"AI: {msg.content}\n"
            
            # Use the LLM to create a summary
            summary_prompt = f"""Please provide a concise summary of the following conversation:

{conversation_text}

Summary:"""
            
            try:
                new_summary = self.llm.invoke(summary_prompt).content
                
                # Combine with existing summary if any
                if self.conversation_summary:
                    combined_prompt = f"""Please combine these two conversation summaries into one concise summary:

Previous summary: {self.conversation_summary}

New summary: {new_summary}

Combined summary:"""
                    self.conversation_summary = self.llm.invoke(combined_prompt).content
                else:
                    self.conversation_summary = new_summary
                
                # Keep only the last 2 messages
                recent_messages = messages[-2:]
                self.chat_history.clear()
                for msg in recent_messages:
                    if isinstance(msg, HumanMessage):
                        self.chat_history.add_user_message(msg.content)
                    elif isinstance(msg, AIMessage):
                        self.chat_history.add_ai_message(msg.content)
                        
            except Exception as e:
                print(f"Error creating summary with LLM: {e}")
                # Fallback: simple truncation
                self.conversation_summary = f"Previous conversation covered various topics. Recent messages kept."
                recent_messages = messages[-2:]
                self.chat_history.clear()
                for msg in recent_messages:
                    if isinstance(msg, HumanMessage):
                        self.chat_history.add_user_message(msg.content)
                    elif isinstance(msg, AIMessage):
                        self.chat_history.add_ai_message(msg.content)
                        
        except Exception as e:
            print(f"Error in conversation summarization: {e}")
    
    def process_input(self, state):
        user_input = state.get("input", "") if isinstance(state, dict) else state
        
        try:
            # Get conversation summary and history from memory using load_memory_variables
            memory_variables = self.memory.load_memory_variables({})
            conversation_context = ""
            
            # Handle memory output (string format)
            if 'history' in memory_variables and memory_variables['history']:
                conversation_context = memory_variables['history']
            
            # Get conversation summary
            summary = self.conversation_summary
            
            # Construct enhanced input with proper context
            if summary and conversation_context:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nRecent Conversation:\n{conversation_context}\n\nCurrent Question: {user_input}"
            elif summary:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nCurrent Question: {user_input}"
            elif conversation_context:
                enhanced_input = f"Conversation History:\n{conversation_context}\n\nCurrent Question: {user_input}"
            else:
                enhanced_input = f"Current Question: {user_input}"
            
            # Use the React agent to process the enhanced input
            result = self.agent_executor.invoke({"input": enhanced_input})
            
            # Save the conversation to memory - this will trigger summarization if needed
            self.memory.save_context(
                {"input": user_input},
                {"output": result.get("output", "")}
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
                    self.memory.save_context({"input": user_input}, {"output": response})
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
        self.memory.max_token_limit = max_tokens
    
    def get_conversation_summary(self):
        """Get the current conversation summary and recent messages.
        
        Returns:
            dict: Dictionary containing summary and recent messages
        """
        try:
            # Load memory variables to get current state
            memory_vars = self.memory.load_memory_variables({})
            
            # Get the moving summary buffer if it exists
            summary = getattr(self.memory, 'moving_summary_buffer', '')
            
            # Get recent messages from chat memory
            recent_messages = []
            if hasattr(self.memory, 'chat_memory') and hasattr(self.memory.chat_memory, 'messages'):
                recent_messages = self.memory.chat_memory.messages
            
            return {
                'summary': summary,
                'recent_messages': recent_messages,
                'history': memory_vars.get('history', '')
            }
        except Exception as e:
            print(f"Error getting conversation summary: {e}")
            return {
                'summary': '',
                'recent_messages': [],
                'history': ''
            }
    
    def update_summary(self):
        """Manually trigger a summary update.
        
        Returns:
            str: The updated summary
        """
        try:
            # Force a summary update by calling the memory's prune method
            if hasattr(self.memory, 'prune'):
                self.memory.prune()
            
            # Get the updated summary
            summary = getattr(self.memory, 'moving_summary_buffer', '')
            return summary
        except Exception as e:
            print(f"Error updating summary: {e}")
            return ''