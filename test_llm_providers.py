#!/usr/bin/env python3
"""
Test script to demonstrate using different LLM providers with the Trip Agent.

This script shows how to initialize the Workflow with different LLM providers
and test basic functionality.
"""

import os
from dotenv import load_dotenv
from workflow import Workflow

# Load environment variables
load_dotenv()

def test_provider(provider, model=None, query="What's the weather in Tokyo?"):
    """Test a specific LLM provider with a sample query."""
    print(f"\n{'='*50}")
    print(f"Testing {provider.upper()} provider")
    if model:
        print(f"Model: {model}")
    print(f"{'='*50}")
    
    # Initialize the workflow with the specified provider and model
    workflow = Workflow(provider=provider, model_name=model)
    
    # Process the query
    print(f"\nQuery: {query}")
    print("\nProcessing...\n")
    
    try:
        result = workflow.invoke(query)
        print(f"Response: {result.final_response}\n")
        print(f"Thinking: {result.agent_response.get('thinking', 'No thinking available')}\n")
        
        # Print function calls
        if result.agent_response.get('function_calls'):
            print("Function Calls:")
            for call in result.agent_response['function_calls']:
                print(f"  - {call['tool']}: {call['parameters']}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}\n")
        return False

def main():
    """Test different LLM providers."""
    # Test the default provider (OpenAI GPT-4o)
    test_provider("openai")
    
    # Test Groq with deepseek-r1-distill-llama-70b model
    if os.getenv("GROQ_API_KEY"):
        test_provider("groq", "deepseek-r1-distill-llama-70b")
    else:
        print("\nSkipping Groq test (GROQ_API_KEY not found)")
    
    # Test Google with Gemini 1.5 Flash model
    if os.getenv("GOOGLE_API_KEY"):
        test_provider("google", "gemini-1.5-flash")
    else:
        print("\nSkipping Google test (GOOGLE_API_KEY not found)")

if __name__ == "__main__":
    main()