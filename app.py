from flask import Flask, jsonify, request, Response, stream_with_context
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from dotenv import load_dotenv
import json
import os

# Load environment variables first
load_dotenv()

# Import workflow after loading environment variables
from workflow import Workflow

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

api = Api(
    app,
    version='1.0',
    title='Trip AI Agent',
    description='A Flask API with Langchain React Agent powered by GPT-4o for intelligent chat interactions',
    doc='/docs/',
    prefix='/api/v1'
)

workflow = Workflow()

# Define namespaces
chat_ns = api.namespace('chat', description='Chat operations')

# Define models for request/response documentation
chat_request_model = api.model('ChatRequest', {
    'message': fields.String(required=True, description='User message to send to the agent', example='What is the weather in New York?')
})

# Define models for streaming request
stream_request_model = api.model('StreamRequest', {
    'message': fields.String(required=True, description='User message to send to the agent', example='What is the weather in New York?'),
    'stream_mode': fields.String(description='Streaming mode to use', enum=['updates', 'messages', 'both'], default='both')
})

chat_response_model = api.model('ChatResponse', {
    'response': fields.String(description='Agent response to the user message'),
    'reasoning': fields.Raw(description='Tool outputs and reasoning from the agent'),
    'history': fields.Raw(description='Conversation history'),
    'agent_response': fields.Raw(description='Structured agent response with thinking, function calls, and final response')
})

error_model = api.model('Error', {
    'message': fields.String(description='Error message'),
    'status': fields.String(description='Error status')
})

@chat_ns.route('')
class Chat(Resource):
    @api.expect(chat_request_model)
    @api.marshal_with(chat_response_model)
    @api.response(200, 'Success', chat_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('chat_with_agent')
    def post(self):
        """Send a message to the AI agent and get a response
        
        This endpoint allows you to interact with the AI agent that has access to:
        - Weather information tool
        - Time information tool  
        - City facts tool
        
        The agent uses OpenAI's GPT-4o model with a React framework to reason about
        which tools to use based on your message.
        """
        try:
            if not request.json or 'message' not in request.json:
                api.abort(400, 'Missing required field: message')
            
            user_input = request.json.get('message')
            if not user_input or not user_input.strip():
                api.abort(400, 'Message cannot be empty')
            
            result = workflow.invoke(user_input)
            return {
                "response": result.final_response,
                "reasoning": result.tool_outputs,
                "history": result.conversation_history,
                "agent_response": result.agent_response
            }
        except Exception as e:
            api.abort(500, f'Internal server error: {str(e)}')

@chat_ns.route('/stream')
class StreamChat(Resource):
    @api.expect(stream_request_model)
    @api.response(200, 'Streaming response')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('stream_chat_with_agent')
    def post(self):
        """Stream a message to the AI agent and get real-time updates
        
        This endpoint allows you to interact with the AI agent and receive streaming updates as:
        - Thinking: Initial reasoning steps
        - Tool usage: When tools are called
        - Tokens: Individual tokens as they're generated
        
        You can specify the stream_mode to control what types of updates you receive.
        """
        try:
            if not request.json or 'message' not in request.json:
                api.abort(400, 'Missing required field: message')
            
            user_input = request.json.get('message')
            if not user_input or not user_input.strip():
                api.abort(400, 'Message cannot be empty')
            
            # Get the stream mode from the request
            stream_mode_param = request.json.get('stream_mode', 'both')
            
            # Convert the stream mode to the format expected by the workflow
            if stream_mode_param == 'both':
                stream_mode = ['updates', 'messages']
            else:
                stream_mode = stream_mode_param
            
            # Define the generator function for streaming
            def generate():
                try:
                    for mode, chunk in workflow.stream(user_input, stream_mode=stream_mode):
                        # Add the mode to the chunk
                        chunk['stream_mode'] = mode
                        # Yield the chunk as a JSON string with a data: prefix for SSE
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    error_chunk = {
                        'type': 'error',
                        'content': str(e),
                        'stream_mode': 'error'
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Return a streaming response
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive'
                }
            )
        except Exception as e:
            api.abort(500, f'Internal server error: {str(e)}')

# Add the async streaming endpoint
@chat_ns.route('/astream')
class AsyncStreamChat(Resource):
    @api.expect(stream_request_model)
    @api.response(200, 'Asynchronous streaming response')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('astream_chat_with_agent')
    async def post(self):
        """Asynchronously stream a message to the AI agent and get real-time updates
        
        This endpoint allows you to interact with the AI agent and receive streaming updates as:
        - Thinking: Initial reasoning steps
        - Tool usage: When tools are called
        - Tokens: Individual tokens as they're generated
        
        This is the asynchronous version of the streaming endpoint, suitable for use with
        async frameworks and WebSockets.
        """
        try:
            if not request.json or 'message' not in request.json:
                api.abort(400, 'Missing required field: message')
            
            user_input = request.json.get('message')
            if not user_input or not user_input.strip():
                api.abort(400, 'Message cannot be empty')
            
            # Get the stream mode from the request
            stream_mode_param = request.json.get('stream_mode', 'both')
            
            # Convert the stream mode to the format expected by the workflow
            if stream_mode_param == 'both':
                stream_mode = ['updates', 'messages']
            else:
                stream_mode = stream_mode_param
            
            # Define the async generator function for streaming
            async def generate():
                try:
                    async for mode, chunk in workflow.astream(user_input, stream_mode=stream_mode):
                        # Add the mode to the chunk
                        chunk['stream_mode'] = mode
                        # Yield the chunk as a JSON string with a data: prefix for SSE
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    error_chunk = {
                        'type': 'error',
                        'content': str(e),
                        'stream_mode': 'error'
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Return a streaming response
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive'
                }
            )
        except Exception as e:
            api.abort(500, f'Internal server error: {str(e)}')

# Add the token-only streaming endpoint
@chat_ns.route('/stream_tokens')
class StreamTokens(Resource):
    @api.expect(chat_request_model)
    @api.response(200, 'Token streaming response')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('stream_tokens_from_agent')
    def post(self):
        """Stream only the tokens from the AI agent's response
        
        This endpoint provides a ChatGPT-like experience by streaming only the
        tokens of the final response, without intermediate reasoning steps.
        """
        try:
            if not request.json or 'message' not in request.json:
                api.abort(400, 'Missing required field: message')
            
            user_input = request.json.get('message')
            if not user_input or not user_input.strip():
                api.abort(400, 'Message cannot be empty')
            
            # Define the generator function for streaming tokens only
            def generate():
                try:
                    for mode, chunk in workflow.stream(user_input, stream_mode="messages"):
                        if chunk.get('type') == 'token':
                            yield f"data: {json.dumps({'text': chunk.get('content', '')})}\n\n"
                except Exception as e:
                    error_chunk = {
                        'type': 'error',
                        'content': str(e)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Return a streaming response
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive'
                }
            )
        except Exception as e:
            api.abort(500, f'Internal server error: {str(e)}')

# Add a health check endpoint
health_ns = api.namespace('health', description='Health check operations')

@health_ns.route('')
class Health(Resource):
    @api.doc('health_check')
    def get(self):
        """Health check endpoint"""
        return {'status': 'healthy', 'message': 'AI Agent Chat API is running'}

if __name__ == '__main__':
    app.run(debug=True)