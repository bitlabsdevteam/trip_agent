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
        """Run on new LLM token."""
        if self.current_section == "thinking":
            # Accumulate thinking tokens and stream them
            self.thinking_buffer += token
            await self.queue.put({"type": "thinking", "content": self._escape_special_chars(token)})
        elif self.current_section == "response":
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
        
        # When the chain ends, we can send the structured format
        structured_output = {
            "type": "structured_output",
            "content": {
                "thinking": self.thinking_buffer.strip(),
                "function_calls": self.function_calls,
                "response": self.response_buffer.strip() # Include any response content that might already be available
            }
        }
        
        await self.queue.put(structured_output)
        
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Run when chain errors."""
        error_str = str(error)
        await self.queue.put({"type": "error", "content": self._escape_special_chars(error_str)})
        
        # Check if this is a parsing error and try to extract the content
        if "Could not parse LLM output" in error_str:
            # Try to extract the actual content from the error message
            import re
            match = re.search(r'Could not parse LLM output: `(.+)`', error_str)
            if match and match[1]:
                # Extract the actual content from the error message
                content = match[1]
                self.response_buffer = content
                
                # Send the extracted content as a structured output
                structured_output = {
                    "type": "structured_output",
                    "content": {
                        "thinking": self.thinking_buffer.strip(),
                        "function_calls": self.function_calls,
                        "response": content.strip()
                    }
                }
                await self.queue.put(structured_output)
    
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