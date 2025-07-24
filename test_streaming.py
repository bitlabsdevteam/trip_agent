import requests
import json
import sys


def test_streaming_api():
    """Test the streaming API endpoint"""
    # API endpoint URL
    url = "http://localhost:5000/api/v1/chat/stream"
    
    # Message to send
    message = "What's the weather in Tokyo?"
    
    # Request payload
    payload = {
        "message": message,
        "stream_mode": "both"  # Can be 'updates', 'messages', or 'both'
    }
    
    # Send the request with stream=True to get a streaming response
    response = requests.post(url, json=payload, stream=True)
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"Sending message: {message}\n")
        print("Streaming response:")
        
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                # SSE format: lines starting with 'data: '
                if line.startswith(b'data: '):
                    # Parse the JSON data
                    data = json.loads(line[6:].decode('utf-8'))
                    
                    # Process different types of chunks
                    if data.get('type') == 'thinking':
                        print(f"\nThinking: {data.get('content')}")
                    elif data.get('type') == 'tool_usage':
                        print(f"\nUsing tool: {data.get('tool')} with input: {data.get('input')}")
                        print(f"Thought: {data.get('thought')}")
                    elif data.get('type') == 'token':
                        # Print tokens without newlines for a more natural output
                        sys.stdout.write(data.get('content', ''))
                        sys.stdout.flush()
                    elif data.get('type') == 'error':
                        print(f"\nError: {data.get('content')}")
                    else:
                        print(f"\nUnknown chunk type: {data}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def test_token_streaming_api():
    """Test the token-only streaming API endpoint"""
    # API endpoint URL
    url = "http://localhost:5000/api/v1/chat/stream_tokens"
    
    # Message to send
    message = "Tell me a joke about programming."
    
    # Request payload
    payload = {
        "message": message
    }
    
    # Send the request with stream=True to get a streaming response
    response = requests.post(url, json=payload, stream=True)
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"Sending message: {message}\n")
        print("Streaming tokens:")
        
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                # SSE format: lines starting with 'data: '
                if line.startswith(b'data: '):
                    # Parse the JSON data
                    data = json.loads(line[6:].decode('utf-8'))
                    
                    # Print tokens without newlines for a more natural output
                    if 'text' in data:
                        sys.stdout.write(data['text'])
                        sys.stdout.flush()
                    elif 'type' in data and data['type'] == 'error':
                        print(f"\nError: {data.get('content')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("Testing the streaming API...\n")
    test_streaming_api()
    
    print("\n\nTesting the token-only streaming API...\n")
    test_token_streaming_api()