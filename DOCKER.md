# Docker Setup for Trip Agent

This document explains how to run the Trip Agent application using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system

## Environment Variables

Before running the application, you need to set up your environment variables. Create a `.env` file in the root directory of the project based on the `.env.example` file:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your API keys:

```
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# Optional API Keys
GOOGLE_API_KEY=your_google_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# LLM Configuration
LLM_PROVIDER=openai  # Can be "openai", "groq", or "google"
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
```

## Running the Application

To start the application using Docker Compose, run the following command from the root directory of the project:

```bash
docker-compose up --build
```

This will:
1. Build the Docker images for both the backend and frontend
2. Start the containers
3. Make the application available at http://localhost:3000

To run the application in the background, use:

```bash
docker-compose up -d
```

To stop the application, run:

```bash
docker-compose down
```

## Services

### Backend

- Built from the root directory
- Runs on port 5001
- Provides the API endpoints for the frontend

### Frontend

- Built from the `frontend` directory
- Runs on port 3000
- Provides the user interface for the application

## Volumes

The `.env` file is mounted as a volume to the backend container, allowing you to update environment variables without rebuilding the container.

## Troubleshooting

### API Connection Issues

If the frontend cannot connect to the backend, check that:

1. Both containers are running: `docker-compose ps`
2. The backend container is exposing port 5001: `docker-compose logs backend`
3. The frontend is correctly configured to use the backend URL

### Missing API Keys

If you see errors related to missing API keys, ensure that:

1. Your `.env` file contains all the required API keys
2. The `.env` file is in the root directory of the project
3. The Docker Compose service is correctly loading the environment variables

## Customization

### Changing Ports

To change the ports that the services run on, edit the `docker-compose.yml` file and update the port mappings:

```yaml
services:
  backend:
    ports:
      - "<new-port>:5001"
  
  frontend:
    ports:
      - "<new-port>:3000"
```

Remember to also update the `NEXT_PUBLIC_API_URL` environment variable in the frontend service if you change the backend port.