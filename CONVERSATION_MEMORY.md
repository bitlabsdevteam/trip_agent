# Conversation Summary Memory

## Overview

This project implements `ConversationSummaryBufferMemory` from LangChain to enhance the agent's ability to remember conversation history. This memory implementation combines the benefits of buffer memory (keeping recent interactions in full detail) with summary memory (summarizing older interactions to save tokens).

## How It Works

The `ConversationSummaryBufferMemory` works by:

1. Keeping the most recent interactions in full detail (up to a configurable token limit)
2. Summarizing older interactions to maintain context while saving tokens
3. Using the same LLM to generate summaries of past conversations

This approach allows the agent to maintain context over longer conversations without exceeding token limits.

## Implementation Details

The implementation in `workflow/agent.py` includes:

- Replacing `ConversationBufferWindowMemory` with `ConversationSummaryBufferMemory`
- Setting a default token limit of 2000 tokens for the buffer
- Adding methods to access and manipulate the conversation summary

## Usage

### Basic Usage

The memory is automatically used when you initialize the Agent class:

```python
from workflow.agent import Agent

# Initialize the agent with default settings
agent = Agent(provider="openai", model_name="gpt-4o", temperature=0.7)

# Process user input
result = agent.process_input({"input": "Tell me about Tokyo"})
```

### Accessing the Conversation Summary

You can access the current conversation summary using the `get_conversation_summary` method:

```python
# Get the current summary and recent messages
summary_info = agent.get_conversation_summary()
print("Summary:", summary_info.get("summary", "No summary available"))

# Access recent messages that haven't been summarized yet
for message in summary_info.get("recent_messages", []):
    print(f"{message.type}: {message.content}")
```

### Adjusting the Token Limit

You can adjust how many tokens are kept in the buffer before summarization:

```python
# Set a higher token limit to keep more detailed context
agent.set_max_token_limit(4000)

# Set a lower token limit to save tokens
agent.set_max_token_limit(1000)
```

### Manually Updating the Summary

You can force the agent to update its conversation summary:

```python
# Manually generate a new summary
new_summary = agent.update_summary()
print("New summary:", new_summary)
```

## Testing

A test script is provided to demonstrate the conversation summary memory functionality:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Run the test script
python test_summary_memory.py
```

## Benefits

- **Longer Context**: The agent can maintain context over longer conversations
- **Token Efficiency**: Summarizing older interactions saves tokens while preserving context
- **Customizable**: The token limit can be adjusted based on your specific needs
- **Transparent**: You can access both the summary and recent messages

## Limitations

- Summarization may lose some details from earlier in the conversation
- Requires additional LLM calls to generate summaries (though these are typically small)
- The quality of the summary depends on the capabilities of the underlying LLM