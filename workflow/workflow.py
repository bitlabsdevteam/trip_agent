from .agent import Agent

class Workflow:
    def __init__(self):
        self.agent = Agent()

    def execute_workflow(self, user_input: str):
        # Simplified workflow execution
        state = {"input": user_input}
        result = self.agent.process_input(state)
        
        return {
            "response": result["response"],
            "reasoning": result["reasoning"],
            "conversation_history": self.agent.conversation_history
        }

execute_workflow = Workflow().execute_workflow