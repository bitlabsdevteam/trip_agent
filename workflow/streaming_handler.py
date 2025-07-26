from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List, Optional, Union
import asyncio
import json
import re
from langchain_core.messages import HumanMessage, AIMessage

class StreamingHandler(BaseCallbackHandler):
    """Callback handler for streaming tokens and agent steps.
    
    This handler collects tokens from LLM and tool usage information,
    making them available through an async iterator.
    """
    
    def __init__(self, agent=None):
        self.tokens = []
        self.queue = asyncio.Queue()
        self.current_section = "thinking"  # thinking, tool, response
        self.function_calls = []
        self.thinking_buffer = ""
        self.response_buffer = ""
        self.agent = agent  # Store reference to the agent
        
    async def on_llm_start(self, *args, **kwargs):
        """Run when LLM starts generating."""
        self.current_section = "thinking"
    
    async def on_llm_new_token(self, token: str, **kwargs):
        """Run on new LLM token with structured output parsing."""
        # Check for <think> tags to separate reasoning from response
        if "<think>" in token or "</think>" in token:
            # Handle thinking tag transitions
            if "<think>" in token:
                self.current_section = "thinking"
                # Remove the <think> tag from the token
                token = token.replace("<think>", "")
            elif "</think>" in token:
                self.current_section = "response"
                # Remove the </think> tag and any content before it
                parts = token.split("</think>")
                if len(parts) > 1:
                    # Add the thinking part to thinking buffer
                    if parts[0]:
                        self.thinking_buffer += parts[0]
                        await self.queue.put({"type": "thinking", "content": self._escape_special_chars(parts[0])})
                    # Continue with the response part
                    token = parts[1]
                else:
                    token = ""
        
        if self.current_section == "thinking" and token:
            # Accumulate thinking tokens and stream them
            self.thinking_buffer += token
            await self.queue.put({"type": "thinking", "content": self._escape_special_chars(token)})
        elif self.current_section == "response" and token:
            # Accumulate response tokens and stream them
            self.response_buffer += token
            await self.queue.put({"type": "token", "content": self._escape_special_chars(token)})
            
            # Also send a structured update with the updated response
            structured_update = {
                "type": "structured_update",
                "content": {
                    "thinking": self.thinking_buffer.strip(),
                    "function_calls": self.function_calls,
                    "response": self.response_buffer.strip()
                }
            }
            await self.queue.put(structured_update)
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Run when a tool starts being used."""
        self.current_section = "tool"
        tool_name = serialized.get("name", "unknown_tool")
        
        # Extract parameters from input_str
        params = {}
        if isinstance(input_str, str):
            # Try to extract parameters from the input string
            if '{' in input_str and '}' in input_str:
                try:
                    # Try to parse as JSON if it looks like a JSON object
                    json_str = re.search(r'\{.*\}', input_str)
                    if json_str:
                        params = json.loads(json_str.group(0))
                except json.JSONDecodeError:
                    # If JSON parsing fails, use a simple key-value approach
                    params = {"input": input_str}
            else:
                params = {"input": input_str}
        elif isinstance(input_str, dict):
            params = input_str
        
        # Add the function call to our list
        self.function_calls.append({
            "tool": tool_name,
            "parameters": params
        })
        
        # Stream the tool separator
        await self.queue.put({"type": "tool_separator", "content": f"\n---Using {tool_name}---\n"})
    
    async def on_tool_end(self, output: str, **kwargs):
        """Run when a tool finishes being used."""
        self.current_section = "thinking"
        await self.queue.put({"type": "tool_separator", "content": "\n---Tool Complete---\n"})
    
    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Run when chain starts running."""
        pass
    
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """Run when chain ends running."""
        # Set the current section to response before creating the structured output
        self.current_section = "response"
        
        # Extract the final answer from the outputs if available
        final_answer = ""
        if outputs and isinstance(outputs, dict) and "output" in outputs:
            final_answer = outputs["output"]
            # Store the final answer in the response buffer
            self.response_buffer = final_answer
            
            # Get the last message from the conversation history
            from langchain_core.messages import AIMessage
            if hasattr(self, 'agent') and hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'chat_memory'):
                self.agent.memory.chat_memory.add_message(AIMessage(content=final_answer))
        
        # Get conversation summary and history from memory for frontend
        conversation_summary = ""
        conversation_history = []
        if hasattr(self, 'agent') and hasattr(self.agent, 'get_conversation_summary'):
            try:
                # Get conversation data using the new memory system
                conversation_data = self.agent.get_conversation_summary()
                conversation_summary = conversation_data.get('summary', '')
                history_content = conversation_data.get('history', '')
                
                # If we have history content, format it for the frontend
                if history_content:
                    # For now, treat the history as a single summary entry
                    # This maintains compatibility with the existing frontend
                    conversation_history.append({
                        "type": "summary",
                        "content": history_content
                    })
                    
            except Exception as e:
                print(f"Error loading memory variables: {e}")
        
        # When the chain ends, we can send the structured format with memory info
        structured_output = {
            "type": "structured_output",
            "content": {
                "thinking": self.thinking_buffer.strip(),
                "function_calls": self.function_calls,
                "response": self.response_buffer.strip(),
                "conversation_summary": conversation_summary,
                "conversation_history": conversation_history
            }
        }
        
        await self.queue.put(structured_output)
        
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Run when chain errors with enhanced parsing."""
        error_str = str(error)
        await self.queue.put({"type": "error", "content": self._escape_special_chars(error_str)})
        
        # Enhanced error patterns matching frontend implementation
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
            thinking_content = ""
            response_content = extracted_content
            
            # Try different thinking tag patterns
            thinking_patterns = [
                r'<think>([\s\S]*?)</think>',
                r'<thinking>([\s\S]*?)</thinking>',
                r'Thought:([\s\S]*?)(?=Action:|Final Answer:|$)'
            ]
            
            for think_pattern in thinking_patterns:
                thinking_match = re.search(think_pattern, extracted_content, re.IGNORECASE)
                if thinking_match:
                    thinking_content = thinking_match.group(1).strip()
                    # Remove thinking content from response
                    response_content = re.sub(think_pattern, '', extracted_content, flags=re.IGNORECASE).strip()
                    break
            
            # Clean up response content
            response_content = response_content.strip()
            if not response_content:
                response_content = "I encountered a parsing error but was able to extract some content. Please try rephrasing your question."
            
            # Update buffers
            self.thinking_buffer = thinking_content
            self.response_buffer = response_content
            
            # Get conversation summary and history from memory for error case
            conversation_summary = ""
            conversation_history = []
            if hasattr(self, 'agent') and hasattr(self.agent, 'get_conversation_summary'):
                try:
                    # Get conversation data using the new memory system
                    conversation_data = self.agent.get_conversation_summary()
                    conversation_summary = conversation_data.get('summary', '')
                    history_content = conversation_data.get('history', '')
                    
                    # If we have history content, format it for the frontend
                    if history_content:
                        # For now, treat the history as a single summary entry
                        # This maintains compatibility with the existing frontend
                        conversation_history.append({
                            "type": "summary",
                            "content": history_content
                        })
                        
                except Exception as e:
                    print(f"Error loading memory variables in error handler: {e}")
            
            # Send the extracted content as a structured output
            structured_output = {
                "type": "structured_output",
                "content": {
                    "thinking": thinking_content,
                    "function_calls": self.function_calls,
                    "response": response_content,
                    "conversation_summary": conversation_summary,
                    "conversation_history": conversation_history
                }
            }
            await self.queue.put(structured_output)
            
            # Also send the content as a token to ensure it's displayed
            await self.queue.put({"type": "token", "content": self._escape_special_chars(response_content)})
    
    def _escape_special_chars(self, text):
        """Escape special characters for JSON."""
        if not isinstance(text, str):
            return text
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    
    async def aiter(self):
        """Async iterator for getting tokens and updates."""
        while True:
            try:
                # Get the next token from the queue
                token_data = await self.queue.get()
                
                # Yield the token data
                yield token_data
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    # Event loop is closed, stop iteration gracefully
                    break
                else:
                    # Re-raise other RuntimeErrors
                    raise
            except Exception as e:
                # Log other exceptions and break to prevent infinite loops
                print(f"Error in streaming handler aiter: {e}")
                break

def get_streaming_handler(agent=None):
    """Create and return a new StreamingHandler instance.
    
    This function is used to create a new StreamingHandler for each request,
    ensuring that each client gets their own isolated stream of tokens.
    
    Args:
        agent: Optional reference to the Agent instance for accessing chat history
    
    Returns:
        StreamingHandler: A new instance of the StreamingHandler with agent reference.
    """
    return StreamingHandler(agent=agent)