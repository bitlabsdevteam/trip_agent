from .agent import Agent
from .output_parser import AgentResponse, FunctionCall
import json
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
class Workflow:
    def __init__(self, provider="groq", model_name=None, temperature=0.7, **kwargs):
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
            "conversation_history": self.agent.memory.chat_memory.messages if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "chat_memory") else []
        }
        
    def invoke(self, user_input: str):
        # Method to match the app.py implementation - preferred in Langchain and Langgraph
        
        # Get the last message from chat history if available
        last_message = None
        if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "chat_memory") and self.agent.memory.chat_memory.messages:
            messages = self.agent.memory.chat_memory.messages
            # Find the last AI message
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        # Include the last message in the input if available
        enhanced_input = user_input
        if last_message:
            enhanced_input = f"{user_input}\n\nFor context, my last response was: {last_message}"
        
        # Use the Runnable chain to process the enhanced input
        formatted_result = self.agent_chain.invoke({"input": enhanced_input})
        
        # Create function calls from the formatted result
        function_calls = []
        for call in formatted_result["function_calls"]:
            function_calls.append(FunctionCall(
                tool=call["tool"],
                parameters=call["parameters"]
            ))
        
        # Create the AgentResponse object
        agent_response = AgentResponse(
            thinking=formatted_result["thinking"],
            function_calls=function_calls,
            response=formatted_result["response"]
        )
        
        # Create a result object with the expected attributes
        class ResultObject:
            def __init__(self, final_response, tool_outputs, conversation_history, agent_response):
                self.final_response = final_response
                self.tool_outputs = tool_outputs
                self.conversation_history = conversation_history
                self.agent_response = agent_response
        
        # Convert LangChain message objects to serializable dictionaries
        serializable_history = []
        for message in self.agent.memory.chat_memory.messages:
            # Extract the content and type from each message object
            serializable_history.append({
                "type": message.__class__.__name__,
                "content": message.content
            })
        
        return ResultObject(
            final_response=formatted_result["response"],
            tool_outputs={"reasoning": formatted_result["thinking"], "steps": formatted_result["function_calls"]},
            conversation_history=serializable_history,
            agent_response=agent_response.model_dump()
        )
        
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
        # Get the last message from chat history if available
        last_message = None
        if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "chat_memory") and self.agent.memory.chat_memory.messages:
            messages = self.agent.memory.chat_memory.messages
            # Find the last AI message
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        # Include the last message in the input if available
        enhanced_input = user_input
        if last_message:
            enhanced_input = f"{user_input}\n\nFor context, my last response was: {last_message}"
        
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
    
    async def astream(self, user_input: str, stream_mode=None):
        """Asynchronously stream the workflow execution results.
        
        Args:
            user_input (str): The user's input message
            stream_mode (str or list): Not used in this implementation, kept for API compatibility
                
        Yields:
            tuple: (stream_mode, chunk) pairs where chunk is the streamed data
        """
        # Get the last message from chat history if available
        last_message = None
        if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "chat_memory") and self.agent.memory.chat_memory.messages:
            messages = self.agent.memory.chat_memory.messages
            # Find the last AI message
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        # Include the last message in the input if available
        enhanced_input = user_input
        if last_message:
            enhanced_input = f"{user_input}\n\nFor context, my last response was: {last_message}"
        
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
        
        # Get the last message from chat history if available
        last_message = None
        if hasattr(self.agent, "memory") and hasattr(self.agent.memory, "chat_memory") and self.agent.memory.chat_memory.messages:
            messages = self.agent.memory.chat_memory.messages
            # Find the last AI message
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        # Include the last message in the input if available
        enhanced_input = user_input
        if last_message:
            enhanced_input = f"{user_input}\n\nFor context, my last response was: {last_message}"
        
        # Run the agent asynchronously and return the final result
        return await self.agent.agent_executor.ainvoke({"input": enhanced_input}, config=config)
    
    def _format_chunk(self, mode, chunk):
        """Format a chunk based on its content.
        
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
                            return {
                                "type": "tool_usage",
                                "tool": action.tool,
                                "input": action.tool_input,
                                "thought": action.log
                            }
            return {"type": "thinking", "content": str(chunk)}
        
        elif mode == "messages":
            # Format message chunks (LLM tokens)
            if hasattr(chunk, "content"):
                return {"type": "token", "content": chunk.content}
            elif isinstance(chunk, dict) and "output" in chunk:
                return {"type": "token", "content": chunk.get("output", "")}
            return {"type": "token", "content": str(chunk)}
        
        # Default formatting for unknown modes
        return {"type": "unknown", "content": str(chunk)}

# Export the invoke method as the preferred way to use this module
invoke = Workflow().invoke
# For backward compatibility
execute_workflow = Workflow().execute_workflow