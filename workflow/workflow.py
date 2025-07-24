from .agent import Agent
from .output_parser import AgentResponse, FunctionCall
import json
from langchain_core.messages import HumanMessage
class Workflow:
    def __init__(self):
        self.agent = Agent()

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
        result = self.execute_workflow(user_input)
        
        # Create a result object with the expected attributes
        class ResultObject:
            def __init__(self, final_response, tool_outputs, conversation_history, agent_response):
                self.final_response = final_response
                self.tool_outputs = tool_outputs
                self.conversation_history = conversation_history
                self.agent_response = agent_response
        
        # Convert LangChain message objects to serializable dictionaries
        serializable_history = []
        for message in result["conversation_history"]:
            # Extract the content and type from each message object
            serializable_history.append({
                "type": message.__class__.__name__,
                "content": message.content
            })
        
        return ResultObject(
            final_response=result["raw_response"]["response"],
            tool_outputs={"reasoning": result["raw_response"]["reasoning"], "steps": result["raw_response"]["tool_calls"]},
            conversation_history=serializable_history,
            agent_response=result["agent_response"].model_dump()
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
        # Stream from the agent executor
        for chunk in self.agent.agent_executor.stream(
            {"input": user_input}
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
        # Stream from the agent executor
        async for chunk in self.agent.agent_executor.astream(
            {"input": user_input}
        ):
            # Determine the mode based on the chunk content
            if "intermediate_steps" in chunk:
                mode = "updates"
            else:
                mode = "messages"
                
            # Format the chunk based on its type
            formatted_chunk = self._format_chunk(mode, chunk)
            yield mode, formatted_chunk
    
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