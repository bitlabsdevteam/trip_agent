#!/usr/bin/env python3

"""
Test script for the ConversationSummaryBufferMemory implementation in the Agent class.

This script initializes an Agent instance and tests the conversation memory functionality
by simulating a conversation and checking the summary and buffer contents.

Usage:
    1. Make sure you have set your Groq API key in your environment variables:
       export GROQ_API_KEY="your-api-key"
    2. Run the script: python test_summary_memory.py
"""

import os
import sys
from workflow.agent import Agent

# Check if API key is set
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY environment variable is not set.")
    print("Please set it using: export GROQ_API_KEY='your-api-key'")
    sys.exit(1)

# Initialize the Agent with a smaller token limit for testing
agent = Agent(provider="groq", model_name="deepseek-r1-distill-llama-70b", temperature=0.7)
agent.set_max_token_limit(5000)  # Set a smaller limit for testing

def print_separator():
    print("\n" + "-" * 50 + "\n")

# Function to process input and display results
def process_and_display(user_input):
    print(f"User: {user_input}")
    result = agent.process_input({"input": user_input})
    print(f"AI: {result['response']}")
    print_separator()
    
    # Get and display the conversation summary
    summary_info = agent.get_conversation_summary()
    print("Current Summary:")
    print(summary_info.get("summary", "No summary available"))
    print_separator()
    
    # Display recent messages
    print("Recent Messages:")
    for message in summary_info.get("recent_messages", []):
        print(f"{message.type}: {message.content}")
    print_separator()
    
    return result

# Test with a series of inputs
print("Starting conversation test with ConversationSummaryBufferMemory...")
print_separator()

# First interaction
process_and_display("Hello, can you tell me about Tokyo?")

# Second interaction
process_and_display("What's the best time of year to visit?")

# Third interaction
process_and_display("What about local cuisine?")

# Fourth interaction - should start summarizing earlier messages
process_and_display("Can you recommend some specific dishes to try?")

# Fifth interaction
process_and_display("What about transportation in Tokyo?")

# Manually update the summary and display it
print("Manually updating summary...")
new_summary = agent.update_summary()
print(f"New Summary: {new_summary}")
print_separator()

print("Test completed.")