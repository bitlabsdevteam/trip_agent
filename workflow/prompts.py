SYSTEM_PROMPT = """
You are a helpful assistant with access to these tools:
{tools}

Always format responses with:
- Current weather summary
- Local time
- 2 interesting city facts
- Clear reasoning explanation
"""

USER_PROMPT = """
User Input: {input}

Conversation History:
{history}

Generate response using available tools and maintain natural conversation flow.
"""