#!/usr/bin/env python3
"""
Test script to verify memory buffer summary integration between backend and frontend.
"""

import requests
import json
import time

def test_memory_integration():
    """Test the memory buffer summary integration."""
    base_url = "http://localhost:5001"
    
    print("Testing Memory Buffer Summary Integration...")
    print("=" * 50)
    
    # Test 1: Send a message and check if memory is created
    print("\n1. Sending first message...")
    response = requests.post(f"{base_url}/api/v1/chat/stream_token_by_token", 
                           json={"message": "Hello, I'm planning a trip to Tokyo. Can you help me?"},
                           stream=True)
    
    if response.status_code == 200:
        print("✅ Message sent successfully")
        
        # Parse streaming response to check for conversation_summary
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('event') == 'structured_output':
                            structured_data = data.get('data', {})
                            if 'conversation_summary' in structured_data:
                                print(f"✅ Conversation summary found: {structured_data['conversation_summary'][:100]}...")
                                break
                    except json.JSONDecodeError:
                        continue
    else:
        print(f"❌ Failed to send message: {response.status_code}")
        return
    
    # Test 2: Check memory endpoint
    print("\n2. Checking memory endpoint...")
    time.sleep(2)  # Wait for memory to be saved
    
    memory_response = requests.get(f"{base_url}/api/v1/memory")
    if memory_response.status_code == 200:
        memory_data = memory_response.json()
        print(f"✅ Memory endpoint accessible")
        print(f"   Summary: {memory_data.get('summary', 'No summary')[:100]}...")
        print(f"   Message count: {memory_data.get('message_count', 0)}")
    else:
        print(f"❌ Failed to access memory: {memory_response.status_code}")
    
    # Test 3: Send another message to test memory continuity
    print("\n3. Sending second message to test memory continuity...")
    response2 = requests.post(f"{base_url}/api/v1/chat/stream_token_by_token", 
                            json={"message": "What are the best districts to stay in Tokyo?"},
                            stream=True)
    
    if response2.status_code == 200:
        print("✅ Second message sent successfully")
        
        # Check for updated conversation_summary
        for line in response2.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('event') == 'structured_output':
                            structured_data = data.get('data', {})
                            if 'conversation_summary' in structured_data:
                                print(f"✅ Updated conversation summary: {structured_data['conversation_summary'][:100]}...")
                                break
                    except json.JSONDecodeError:
                        continue
    
    print("\n" + "=" * 50)
    print("Memory integration test completed!")
    print("\nTo test frontend integration:")
    print("1. Open http://localhost:3000")
    print("2. Send a few messages")
    print("3. Check if the 'Conversation Memory' section appears and updates")
    print("4. Expand the memory section to see the full summary")

if __name__ == "__main__":
    try:
        test_memory_integration()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server.")
        print("Please make sure the backend is running on http://localhost:5001")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")