from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List, Optional, Union
import asyncio
import json

class StreamingHandler(BaseCallbackHandler):
    """Callback handler for streaming tokens and agent steps.
    
    This handler collects tokens from LLM and tool usage information,
    making them available through an async iterator.
    """
    
    def __init__(self):
        self.tokens = []
        self.queue = asyncio.Queue()
        self.current_section = "thinking"  # thinking, tool, response
        
    async def on_llm_start(self, *args, **kwargs):
        """Run when LLM starts generating."""
        self.current_section = "thinking"
    
    async def on_llm_new_token(self, token: str, **kwargs):
        """Run on new LLM token."""
        if self.current_section == "thinking":
            # Stream thinking tokens
            await self.queue.put({"type": "thinking", "content": self._escape_special_chars(token)})
        elif self.current_section == "response":
            # Stream response tokens
            await self.queue.put({"type": "token", "content": self._escape_special_chars(token)})
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Run when a tool starts being used."""
        self.current_section = "tool"
        tool_name = serialized.get("name", "unknown_tool")
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
        self.current_section = "response"
        
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs):
        """Run when chain errors."""
        await self.queue.put({"type": "error", "content": self._escape_special_chars(str(error))})
    
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
                yield token_data
                self.queue.task_done()
            except asyncio.CancelledError:
                break

def get_streaming_handler():
    """Create and return a new StreamingHandler instance.
    
    This function is used to create a new StreamingHandler for each request,
    ensuring that each client gets their own isolated stream of tokens.
    
    Returns:
        StreamingHandler: A new instance of the StreamingHandler.
    """
    return StreamingHandler()