#!/usr/bin/env python3
"""
Test script to verify conversation memory functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow.agent import Agent
import json

def test_conversation_memory():
    """Test that the agent retains conversation context."""
    print("🧪 Testing Conversation Memory...")
    
    try:
        # Initialize agent
        agent = Agent(provider="openai", model_name="gpt-4o", temperature=0.7)
        session_id = "test_session"
        
        print("\n1️⃣ First interaction - asking about a city without specifying which one")
        first_input = "Tell me about the best local food"
        result1 = agent.process_input({"input": first_input}, session_id=session_id)
        print(f"Agent response: {result1['response'][:100]}...")
        
        print("\n2️⃣ Second interaction - specifying the city")
        second_input = "I meant Tokyo"
        result2 = agent.process_input({"input": second_input}, session_id=session_id)
        print(f"Agent response: {result2['response'][:100]}...")
        
        # Check conversation history
        print("\n📋 Checking conversation history...")
        conversation_data = agent.get_conversation_summary(session_id)
        print(f"Number of messages in history: {len(conversation_data['recent_messages'])}")
        print(f"Has summary: {conversation_data['stats']['has_summary']}")
        
        # Print conversation history
        print("\n💬 Conversation History:")
        for i, msg in enumerate(conversation_data['recent_messages']):
            role = "Human" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
            print(f"{i+1}. {role}: {msg.content[:80]}...")
        
        print("\n3️⃣ Third interaction - testing if context is maintained")
        third_input = "What's the weather like there?"
        result3 = agent.process_input({"input": third_input}, session_id=session_id)
        print(f"Agent response: {result3['response'][:100]}...")
        
        # Final check
        final_conversation_data = agent.get_conversation_summary(session_id)
        print(f"\n📊 Final conversation stats:")
        print(f"Total messages: {len(final_conversation_data['recent_messages'])}")
        print(f"Memory stats: {json.dumps(final_conversation_data['stats'], indent=2)}")
        
        # Test if the agent understood "there" refers to Tokyo
        if "tokyo" in result3['response'].lower() or any("tokyo" in call.get('parameters', {}).get('city', '').lower() for call in result3.get('function_calls', [])):
            print("\n✅ SUCCESS: Agent maintained conversation context and understood 'there' refers to Tokyo!")
            return True
        else:
            print("\n❌ FAILURE: Agent did not maintain conversation context")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversation_memory()
    sys.exit(0 if success else 1)