from .agent import Agent
from .output_parser import AgentResponse, FunctionCall
import json
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
class Workflow:
    def __init__(self, provider="openai", model_name=None, temperature=0.7, **kwargs):
        """Initialize the Workflow with a configurable Agent.
        
        Args:
            provider: The LLM provider (openai, groq, google)
            model_name: The specific model name to use (defaults to provider's default)
            temperature: The temperature for the LLM
            **kwargs: Additional arguments to pass to the LLM constructor
        """
        self.agent = Agent(provider=provider, model_name=model_name, temperature=temperature, **kwargs)
        
        # Define a custom output formatter for structured response
        def format_agent_output(result):
            steps = result.get("intermediate_steps", [])
            thinking = steps[0][0].log if steps else "No reasoning."
            function_calls = [
                {
                    "tool": step[0].tool,
                    "parameters": step[0].tool_input if isinstance(step[0].tool_input, dict) else {"input": step[0].tool_input}
                }
                for step in steps
            ]
            return {
                "thinking": thinking,
                "function_calls": function_calls,
                "response": result["output"]
            }
        
        # Create the Runnable chain by piping the agent executor through the formatter
        self.agent_chain = self.agent.agent_executor | RunnableLambda(format_agent_output)

    def execute_workflow(self, user_input: str):
        # Simplified workflow execution
        state = {"input": user_input}
        result = self.agent.process_input(state)
        
        # Use the function_calls directly if available, otherwise convert from tool_calls
        function_calls = []
        if "function_calls" in result and result["function_calls"]:
            # Use the pre-formatted function calls
            for call in result["function_calls"]:
                function_calls.append(FunctionCall(
                    tool=call["tool"],
                    parameters=call["parameters"]
                ))
        else:
            # Fall back to converting from tool_calls
            for step in result["tool_calls"]:
                function_calls.append(FunctionCall(
                    tool=step["action"],
                    parameters={"input": step["action_input"]} if isinstance(step["action_input"], str) else step["action_input"]
                ))
        
        # Create the AgentResponse object
        agent_response = AgentResponse(
            thinking=result["reasoning"],
            function_calls=function_calls,
            response=result["response"]
        )
        
        return {
            "agent_response": agent_response,
            "raw_response": result,
            "conversation_history": []
        }
        
    def invoke(self, user_input: str):
        # Method to match the app.py implementation - preferred in Langchain and Langgraph
        
        try:
            # Use the agent's process_input method which handles memory
            result = self.agent.process_input(user_input)
            
            # Parse and separate reasoning from final output if using <think> tags
            response = result["response"]
            thinking = result.get("reasoning", "")
            
            # Check for <think> tag format in response
            import re
            think_match = re.search(r'<think>([\s\S]+?)</think>([\s\S]*)', response)
            if think_match:
                thinking = think_match.group(1).strip()
                response = think_match.group(2).strip()
            
            # Create function calls from the result
            function_calls = []
            if "function_calls" in result:
                for call in result["function_calls"]:
                    function_calls.append(FunctionCall(
                        tool=call["tool"],
                        parameters=call["parameters"]
                    ))
            
            # Create the AgentResponse object with structured output
            agent_response = AgentResponse(
                thinking=thinking,
                function_calls=function_calls,
                response=response
            )
            
            # Create a result object with the expected attributes
            class ResultObject:
                def __init__(self, final_response, tool_outputs, conversation_history, agent_response):
                    self.final_response = final_response
                    self.tool_outputs = tool_outputs
                    self.conversation_history = conversation_history
                    self.agent_response = agent_response
            
            # Get conversation history and summary from memory
            try:
                memory_vars = self.agent.memory.load_memory_variables({})
                conversation_history = []
                
                # Get the memory buffer summary and recent messages
                if 'history' in memory_vars and memory_vars['history']:
                    # ConversationSummaryBufferMemory provides history as a string
                    history_content = memory_vars['history']
                    conversation_history.append({
                        "type": "summary",
                        "content": history_content
                    })
                
                # Also get the moving summary buffer if available
                summary = getattr(self.agent.memory, 'moving_summary_buffer', '')
                if summary:
                    conversation_history.append({
                        "type": "moving_summary",
                        "content": summary
                    })
                
                # Get recent chat messages
                chat_history = self.agent.memory.chat_memory.messages
                for message in chat_history:
                    if hasattr(message, 'content'):
                        message_type = "human" if hasattr(message, 'type') and message.type == "human" else "ai"
                        conversation_history.append({
                            "type": message_type,
                            "content": message.content
                        })
                        
            except Exception as e:
                print(f"Error loading conversation history: {e}")
                conversation_history = []

            return ResultObject(
                final_response=response,
                tool_outputs={"reasoning": thinking, "steps": result.get("tool_calls", [])},
                conversation_history=conversation_history,
                agent_response=agent_response.model_dump()
            )
            
        except Exception as e:
            # Enhanced error handling for parsing failures
            error_str = str(e)
            
            # Try to extract content from OUTPUT_PARSING_FAILURE errors
            if "Could not parse LLM output" in error_str or "OUTPUT_PARSING_FAILURE" in error_str:
                import re
                patterns = [
                    r'Could not parse LLM output: `([\s\S]+?)`',
                    r'Stream error: "Could not parse LLM output: `([\s\S]+?)`',
                    r'OUTPUT_PARSING_FAILURE[\s\S]*?`([\s\S]+?)`'
                ]
                
                extracted_content = None
                for pattern in patterns:
                    match = re.search(pattern, error_str, re.DOTALL)
                    if match and match.group(1):
                        extracted_content = match.group(1)
                        break
                
                if extracted_content:
                    # Parse thinking and response from extracted content
                    thinking = ""
                    response = extracted_content
                    
                    # Handle <think> tags in extracted content
                    think_match = re.search(r'<think>([\s\S]+?)</think>([\s\S]*)', extracted_content)
                    if think_match:
                        thinking = think_match.group(1).strip()
                        response = think_match.group(2).strip()
                    
                    # Save to memory
                    self.agent.memory.save_context(
                        {"input": user_input},
                        {"output": response}
                    )
                    
                    # Create structured response
                    agent_response = AgentResponse(
                        thinking=thinking or "I processed your request despite a formatting issue.",
                        function_calls=[],
                        response=response
                    )
                    
                    class ResultObject:
                        def __init__(self, final_response, tool_outputs, conversation_history, agent_response):
                            self.final_response = final_response
                            self.tool_outputs = tool_outputs
                            self.conversation_history = conversation_history
                            self.agent_response = agent_response
                    
                    # Get conversation history and summary from memory for error case
                    try:
                        memory_vars = self.agent.memory.load_memory_variables({})
                        conversation_history = []
                        
                        # Get the memory buffer summary and recent messages
                        if 'history' in memory_vars and memory_vars['history']:
                            history_content = memory_vars['history']
                            conversation_history.append({
                                "type": "summary",
                                "content": history_content
                            })
                        
                        # Also get the moving summary buffer if available
                        summary = getattr(self.agent.memory, 'moving_summary_buffer', '')
                        if summary:
                            conversation_history.append({
                                "type": "moving_summary",
                                "content": summary
                            })
                            
                    except Exception as mem_error:
                        print(f"Error loading conversation history in error handler: {mem_error}")
                        conversation_history = []
                    
                    return ResultObject(
                        final_response=response,
                        tool_outputs={"reasoning": thinking, "steps": []},
                        conversation_history=conversation_history,
                        agent_response=agent_response.model_dump()
                    )
            
            # If we can't extract content, raise the original error
            raise e
        
    def execute(self, user_input: str):
        # Legacy method, maintained for backward compatibility
        # Use invoke() instead as it's the preferred method in Langchain and Langgraph
        return self.invoke(user_input)
        
    def stream(self, user_input: str, stream_mode=None):
        """Stream the workflow execution results.
        
        Args:
            user_input (str): The user's input message
            stream_mode (str or list): Not used in this implementation, kept for API compatibility
                
        Yields:
            tuple: (stream_mode, chunk) pairs where chunk is the streamed data
        """
        # Get conversation summary and history from memory using load_memory_variables
        try:
            memory_vars = self.agent.memory.load_memory_variables({})
            conversation_context = ""
            
            # Handle ConversationSummaryBufferMemory output (string format)
            if 'history' in memory_vars and memory_vars['history']:
                conversation_context = memory_vars['history']
            
            # Check for moving summary buffer
            summary = getattr(self.agent.memory, 'moving_summary_buffer', '')
            
            # Memory state is working correctly - debug prints removed
            
            # Construct enhanced input with proper context
            if summary and conversation_context:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nRecent Conversation:\n{conversation_context}\n\nCurrent Question: {user_input}"
            elif summary:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nCurrent Question: {user_input}"
            elif conversation_context:
                enhanced_input = f"Conversation History:\n{conversation_context}\n\nCurrent Question: {user_input}"
            else:
                enhanced_input = f"Current Question: {user_input}"
                
        except Exception as e:
            print(f"Error loading memory variables: {e}")
            enhanced_input = f"Current Question: {user_input}"
        
        # Stream from the agent executor with enhanced input
        for chunk in self.agent.agent_executor.stream(
            {"input": enhanced_input}
        ):
            # Determine the mode based on the chunk content
            if "intermediate_steps" in chunk:
                mode = "updates"
            else:
                mode = "messages"
                
            # Format the chunk based on its type
            formatted_chunk = self._format_chunk(mode, chunk)
            yield mode, formatted_chunk
        
        # Save the conversation to memory after streaming
        self.agent.memory.save_context(
            {"input": user_input},
            {"output": "[Streaming response completed]"}
        )
    
    async def astream(self, user_input: str, stream_mode=None):
        """Asynchronously stream the workflow execution results.
        
        Args:
            user_input (str): The user's input message
            stream_mode (str or list): Not used in this implementation, kept for API compatibility
                
        Yields:
            tuple: (stream_mode, chunk) pairs where chunk is the streamed data
        """
        # Get conversation summary and history from memory using load_memory_variables
        try:
            memory_vars = self.agent.memory.load_memory_variables({})
            conversation_context = ""
            
            # Handle ConversationSummaryBufferMemory output (string format)
            if 'history' in memory_vars and memory_vars['history']:
                conversation_context = memory_vars['history']
            
            # Check for moving summary buffer
            summary = getattr(self.agent.memory, 'moving_summary_buffer', '')
            
            # Memory state is working correctly - debug prints removed
            
            # Construct enhanced input with proper context
            if summary and conversation_context:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nRecent Conversation:\n{conversation_context}\n\nCurrent Question: {user_input}"
            elif summary:
                enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nCurrent Question: {user_input}"
            elif conversation_context:
                enhanced_input = f"Conversation History:\n{conversation_context}\n\nCurrent Question: {user_input}"
            else:
                enhanced_input = f"Current Question: {user_input}"
                
        except Exception as e:
            print(f"Error loading memory variables: {e}")
            enhanced_input = f"Current Question: {user_input}"
        
        # Stream from the agent executor with enhanced input
        async for chunk in self.agent.agent_executor.astream(
            {"input": enhanced_input}
        ):
            # Determine the mode based on the chunk content
            if "intermediate_steps" in chunk:
                mode = "updates"
            else:
                mode = "messages"
                
            # Format the chunk based on its type
            formatted_chunk = self._format_chunk(mode, chunk)
            yield mode, formatted_chunk
        
        # Save the conversation to memory after streaming
        self.agent.memory.save_context(
            {"input": user_input},
            {"output": "[Streaming response completed]"}
        )
            
    async def astream_tokens(self, user_input: str, callbacks=None):
        """Asynchronously stream tokens using agent.ainvoke with callbacks.
        
        This method is designed to work with the StreamingHandler callback
        to provide token-by-token streaming similar to the FastAPI example.
        
        Args:
            user_input (str): The user's input message
            callbacks (list): List of callback handlers including StreamingHandler
                
        Returns:
            dict: The final result from the agent
        """
        from langchain_core.runnables import RunnableConfig
        
        # Create a config with the provided callbacks
        config = RunnableConfig(callbacks=callbacks)
        
        # Pass the agent reference to the StreamingHandler
        for callback in callbacks or []:
            if hasattr(callback, 'agent') and callback.agent is None:
                callback.agent = self.agent
        
        # Get conversation summary and history from memory using load_memory_variables
        try:
            memory_vars = self.agent.memory.load_memory_variables({})
            conversation_context = ""
            
            # Handle ConversationSummaryBufferMemory output
            if 'history' in memory_vars:
                if isinstance(memory_vars['history'], str):
                    # String format - includes summary and recent messages
                    conversation_context = memory_vars['history']
                elif isinstance(memory_vars['history'], list):
                    # Message list format - convert to string
                    for message in memory_vars['history']:
                        if hasattr(message, 'content'):
                            role = "Human" if hasattr(message, 'type') and message.type == "human" else "Assistant"
                            conversation_context += f"{role}: {message.content}\n"
            
            # Check for moving summary buffer (ConversationSummaryBufferMemory specific)
            if hasattr(self.agent.memory, 'moving_summary_buffer') and self.agent.memory.moving_summary_buffer:
                summary = self.agent.memory.moving_summary_buffer
                if conversation_context:
                    enhanced_input = f"Previous Conversation Summary:\n{summary}\n\nRecent Conversation:\n{conversation_context}\nCurrent Question: {user_input}"
                else:
                    enhanced_input = f"Previous Conversation Summary:\n{summary}\nCurrent Question: {user_input}"
            else:
                enhanced_input = f"Conversation History:\n{conversation_context}\nCurrent Question: {user_input}" if conversation_context else f"Current Question: {user_input}"
                
        except Exception as e:
            print(f"Error loading memory variables: {e}")
            # Fallback to basic input
            enhanced_input = f"Current Question: {user_input}"
        
        # Run the agent asynchronously and return the final result
        result = await self.agent.agent_executor.ainvoke({"input": enhanced_input}, config=config)
        
        # Save the conversation to memory after completion
        self.agent.memory.save_context(
            {"input": user_input},
            {"output": result.get("output", "[Response completed]")}
        )
        
        return result
    
    def _format_chunk(self, mode, chunk):
        """Format a chunk based on its content with structured output parsing.
        
        Args:
            mode (str): The determined mode ("updates" or "messages")
            chunk: The chunk data
            
        Returns:
            dict: A formatted representation of the chunk
        """
        if mode == "updates":
            # Format update chunks (reasoning steps, tool calls, etc.)
            if isinstance(chunk, dict) and "intermediate_steps" in chunk:
                steps = chunk.get("intermediate_steps", [])
                if steps:
                    last_step = steps[-1]
                    if isinstance(last_step, tuple) and len(last_step) >= 2:
                        action = last_step[0]
                        observation = last_step[1]
                        
                        if hasattr(action, "tool") and hasattr(action, "tool_input") and hasattr(action, "log"):
                            # Parse thinking from log if it contains <think> tags
                            thinking = action.log
                            import re
                            think_match = re.search(r'<think>([\s\S]+?)</think>', action.log)
                            if think_match:
                                thinking = think_match.group(1).strip()
                            
                            return {
                                "type": "tool_usage",
                                "tool": action.tool,
                                "input": action.tool_input,
                                "thought": thinking
                            }
            return {"type": "thinking", "content": str(chunk)}
        
        elif mode == "messages":
            # Format message chunks (LLM tokens) with reasoning separation
            content = ""
            if hasattr(chunk, "content"):
                content = chunk.content
            elif isinstance(chunk, dict) and "output" in chunk:
                content = chunk.get("output", "")
            else:
                content = str(chunk)
            
            # Check for <think> tags in streaming content
            import re
            think_match = re.search(r'<think>([\s\S]+?)</think>([\s\S]*)', content)
            if think_match:
                thinking = think_match.group(1).strip()
                response = think_match.group(2).strip()
                return {
                    "type": "structured_token",
                    "thinking": thinking,
                    "content": response
                }
            
            return {"type": "token", "content": content}
        
        # Default formatting for unknown modes
        return {"type": "unknown", "content": str(chunk)}

# Export the invoke method as the preferred way to use this module
invoke = Workflow().invoke
# For backward compatibility
execute_workflow = Workflow().execute_workflow