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

## Swagger Documentation

API documentation is available at `/docs/` when the application is running.