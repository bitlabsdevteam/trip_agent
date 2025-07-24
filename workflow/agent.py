from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from .tools import tools
import os

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
            k=5,
            return_messages=True
        )
        
        # Create the prompt template for the React agent
        self.prompt = PromptTemplate.from_template(
            """You are a helpful assistant with access to tools. Use the following tools to answer questions:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

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
            max_iterations=3
        )
    
    def process_input(self, state):
        user_input = state.get("input", "")
        
        try:
            # Use the React agent to process the input
            result = self.agent_executor.invoke({"input": user_input})
            
            return {
                "response": result.get("output", "I couldn't process your request."),
                "tool_calls": [],
                "reasoning": f"Used React agent to process: {user_input}"
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