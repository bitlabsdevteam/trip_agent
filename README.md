# Trip Agent

A smart agent application built with Flask and LangChain that provides travel-related information using GPT-4o. The agent can retrieve weather information, time data, and city facts through specialized tools.

## Features

- Interactive chat interface with a GPT-4o powered agent
- Specialized tools for retrieving weather, time, and city information
- RESTful API with Swagger documentation
- Langchain ReAct agent implementation

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file (see `.env.example` for required variables)

4. Run the Flask app:
   ```bash
   python app.py
   ```

## API Endpoints

- `GET /api/v1/health` - Health check endpoint
- `POST /api/v1/chat` - Chat with the GPT-4o powered agent
- `POST /api/v1/chat/stream` - Stream real-time updates from the agent (synchronous)
- `POST /api/v1/chat/astream` - Stream real-time updates from the agent (asynchronous)
- `POST /api/v1/chat/stream_tokens` - Stream only the final response tokens (ChatGPT-like experience)

## Swagger Documentation

API documentation is available at `/docs/` when the application is running.

## Streaming API Usage

The application provides three streaming API endpoints for real-time updates:

### 1. Synchronous Streaming (`/api/v1/chat/stream`)

Get real-time updates from the agent, including thinking steps, tool usage, and individual tokens.

```python
import requests
import json

# Request payload
payload = {
    "message": "What's the weather in Tokyo?",
    "stream_mode": "both"  # Options: "updates", "messages", or "both"
}

# Send request with stream=True
response = requests.post("http://localhost:5000/api/v1/chat/stream", 
                        json=payload, stream=True)

# Process streaming response
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:].decode('utf-8'))
        # Process the data based on its type
        print(data)
```

### 2. Asynchronous Streaming (`/api/v1/chat/astream`)

Similar to synchronous streaming but designed for async applications.

### 3. Token-Only Streaming (`/api/v1/chat/stream_tokens`)

Streams only the final response tokens for a ChatGPT-like experience.

```python
import requests
import json
import sys

# Request payload
payload = {
    "message": "Tell me a joke."
}

# Send request with stream=True
response = requests.post("http://localhost:5000/api/v1/chat/stream_tokens", 
                        json=payload, stream=True)

# Process streaming response
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:].decode('utf-8'))
        if 'text' in data:
            sys.stdout.write(data['text'])
            sys.stdout.flush()
```

For a complete example, see the `test_streaming.py` file.