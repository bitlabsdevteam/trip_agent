# Trip Agent

A smart agent application built with Flask and LangChain that provides travel-related information using Groq's LLama3-70B model. The agent can retrieve weather information, time data, and city facts through specialized tools, offering a comprehensive travel assistant experience.

## Features

- Interactive chat interface with a LLama3-70B powered agent
- Specialized tools for retrieving:
  - Weather information for cities worldwide
  - Local time data for major cities
  - City facts and information via Wikipedia
- RESTful API with Swagger documentation
- LangChain ReAct agent implementation
- Multiple streaming options for real-time responses
- Token-by-token streaming for a natural chat experience

## Project Structure

- `app.py`: Main Flask application with API endpoints
- `workflow/`: Core agent implementation
  - `agent.py`: LangChain agent configuration
  - `workflow.py`: Main workflow implementation
  - `streaming_handler.py`: Handlers for streaming responses
  - `tools/`: Custom tools implementation
    - `weather_tool.py`: Tool for retrieving weather data
    - `time_tool.py`: Tool for getting local time in cities
    - `city_facts_tool.py`: Tool for retrieving city information

## Prerequisites

- Python 3.8 or higher
- Groq API key
- WeatherAPI.com API key (for weather data)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd trip_agent
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file:
   ```
   # Create a .env file in the project root
   touch .env
   ```
   
   Add the following variables to your `.env` file:
   ```
   # Required API Keys
   GROQ_API_KEY=your_groq_api_key_here
   WEATHER_API_KEY=your_weather_api_key_here
   
   # Optional API Keys
   GOOGLE_API_KEY=your_google_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   ```

5. Run the Flask app:
   ```bash
   python app.py --port 5001  # Specify port (default is 5000)
   ```

6. Access the application:
   - API Documentation: http://localhost:5001/docs/
   - Test HTML Interface: http://localhost:5001/test_streaming.html

## Testing

### Running the Test Server

To test the HTML interface, you can run a simple HTTP server:

```bash
python -m http.server 8000
```

Then access the test interface at: http://localhost:8000/test_streaming.html

### Testing the Streaming API

You can use the provided test script to test the streaming API:

```bash
python test_streaming.py
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Health check endpoint

### Chat Endpoints
- `POST /api/v1/chat` - Chat with the LLama3-70B powered agent
- `POST /api/v1/chat/stream` - Stream real-time updates from the agent (synchronous)
- `POST /api/v1/chat/astream` - Stream real-time updates from the agent (asynchronous)
- `POST /api/v1/chat/stream_tokens` - Stream only the final response tokens (ChatGPT-like experience)
- `POST /api/v1/chat/stream_token_by_token` - Stream tokens with structured updates

## Swagger Documentation

API documentation is available at `/docs/` when the application is running.

## Streaming API Usage

The application provides multiple streaming API endpoints for real-time updates:

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
response = requests.post("http://localhost:5001/api/v1/chat/stream", 
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
response = requests.post("http://localhost:5001/api/v1/chat/stream_tokens", 
                        json=payload, stream=True)

# Process streaming response
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:].decode('utf-8'))
        if 'text' in data:
            sys.stdout.write(data['text'])
            sys.stdout.flush()
```

### 4. Token-by-Token Streaming with Structured Updates (`/api/v1/chat/stream_token_by_token`)

Provides a comprehensive streaming experience with structured updates including thinking process, function calls, and response tokens.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.