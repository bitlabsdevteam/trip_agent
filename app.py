from flask import Flask, jsonify, request, Response, stream_with_context
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from dotenv import load_dotenv
import json
import os
import threading
import asyncio
from queue import Queue

# Load environment variables first
load_dotenv()

# Import workflow after loading environment variables
from workflow import Workflow
from workflow.streaming_handler import get_streaming_handler

app = Flask(__name__)
# Enable CORS for all routes and origins with additional configuration
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization", "Accept"], methods=["GET", "POST", "OPTIONS"])

api = Api(
    app,
    version='1.0',
    title='Trip AI Agent',
    description='A Flask API with Langchain React Agent powered by GPT-4o for intelligent chat interactions',
    doc='/docs/',
    prefix='/api/v1'
)

# Get LLM configuration from environment variables or use defaults
llm_provider = os.getenv("LLM_PROVIDER", "openai")  # Default to OpenAI
llm_model = os.getenv("LLM_MODEL", "gpt-4o")  # Default to GPT-4o
llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))  # Default temperature

# Initialize the workflow with the configured LLM
workflow = Workflow(
    provider=llm_provider,
    model_name=llm_model,
    temperature=llm_temperature
)

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
    def post(self):
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
            
            # Create a queue for async streaming
            from queue import Queue
            import threading
            import asyncio
            
            queue = Queue()
            
            # Define the async workflow runner
            def run_async_workflow():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    async def async_stream():
                        try:
                            async for mode, chunk in workflow.astream(user_input, stream_mode=stream_mode):
                                # Add the mode to the chunk
                                chunk['stream_mode'] = mode
                                queue.put(chunk)
                        except Exception as e:
                            error_chunk = {
                                'type': 'error',
                                'content': str(e),
                                'stream_mode': 'error'
                            }
                            queue.put(error_chunk)
                        finally:
                            queue.put(None)  # Signal completion
                    
                    loop.run_until_complete(async_stream())
                except Exception as e:
                    error_chunk = {
                        'type': 'error',
                        'content': str(e),
                        'stream_mode': 'error'
                    }
                    queue.put(error_chunk)
                    queue.put(None)
                finally:
                    loop.close()
            
            # Start the async workflow in a separate thread
            thread = threading.Thread(target=run_async_workflow)
            thread.start()
            
            # Define the synchronous generator function for streaming
            def generate():
                while True:
                    chunk = queue.get()
                    if chunk is None:
                        break
                    yield f"data: {json.dumps(chunk)}\n\n"
            
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

# Add token-by-token streaming endpoint using the new approach
@chat_ns.route('/stream_token_by_token')
class StreamTokenByToken(Resource):
    @api.expect(chat_request_model)
    @api.response(200, 'Token-by-token streaming response')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('stream_token_by_token')
    def post(self):
        """Stream tokens one by one from the AI agent's response
        
        This endpoint provides an image-like streaming experience by sending
        individual tokens as they are generated, including thinking steps and
        tool usage markers.
        """
        try:
            if not request.json or 'message' not in request.json:
                api.abort(400, 'Missing required field: message')
            
            user_input = request.json.get('message')
            if not user_input or not user_input.strip():
                api.abort(400, 'Message cannot be empty')
            
            # Create a queue for the streaming handler
            queue = Queue()
            
            # Create a thread to run the async workflow
            def run_async_workflow():
                # Create an event loop for the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Create the workflow
                    wf = Workflow()
                    
                    # Create the streaming handler with agent reference
                    stream_handler = get_streaming_handler(wf.agent)
                    
                    # Define the async function to run
                    async def run():
                        # Start the streaming task
                        stream_task = asyncio.create_task(process_stream(stream_handler))
                        
                        # Run the agent with the streaming handler
                        final_result = await wf.astream_tokens(user_input, callbacks=[stream_handler])
                        
                        # Signal that we're done and add the final answer
                        queue.put({"type": "final", "content": final_result.get("output", "")})
                        queue.put(None)  # Signal that we're done
                        
                        # Wait for the streaming to complete
                        await stream_task
                    
                    # Process the stream and put chunks into the queue
                    async def process_stream(handler):
                        async for chunk in handler.aiter():
                            queue.put(chunk)
                    
                    # Run the async function
                    loop.run_until_complete(run())
                except Exception as e:
                    queue.put({"type": "error", "content": str(e)})
                    queue.put(None)  # Signal that we're done
                finally:
                    loop.close()
            
            # Start the thread
            thread = threading.Thread(target=run_async_workflow)
            thread.start()
            
            # Define the generator function for streaming
            def generate():
                # Track the current section for formatting
                current_section = "thinking"
                
                while True:
                    chunk = queue.get()
                    if chunk is None:
                        break
                    
                    if chunk["type"] == "thinking":
                        # Send thinking tokens individually
                        event_data = {"event": "message", "data": chunk['content']}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "token":
                        # Send response tokens individually
                        event_data = {"event": "message", "data": chunk['content']}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "tool_separator":
                        # Send tool separator
                        event_data = {"event": "message", "data": chunk['content']}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "error":
                        event_data = {"event": "error", "data": chunk['content']}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "final":
                        # Send a final answer marker
                        event_data = {"event": "message", "data": f"\n\n✅ Final Answer: {chunk['content']}"}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "structured_output":
                        # Send the initial structured output
                        event_data = {"event": "structured_output", "data": chunk["content"]}
                        yield f"data: {json.dumps(event_data)}\n\n"
                    elif chunk["type"] == "structured_update":
                        # Send structured updates as they come in
                        event_data = {"event": "structured_update", "data": chunk["content"]}
                        yield f"data: {json.dumps(event_data)}\n\n"
                
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



# Memory endpoints
memory_ns = api.namespace('memory', description='Memory management operations')

@memory_ns.route('')
class Memory(Resource):
    @api.response(200, 'Memory retrieved successfully')
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('get_memory')
    def get(self):
        """Get current conversation memory summary with BufferSummaryMemory details"""
        try:
            # Get comprehensive memory information from the agent
            memory_info = workflow.agent.get_conversation_summary()
            
            return {
                'summary': memory_info.get('summary', ''),
                'message_count': memory_info.get('stats', {}).get('total_messages', 0),
                'has_history': bool(memory_info.get('history', '')),
                'buffer_messages': memory_info.get('buffer_messages', []),
                'stats': memory_info.get('stats', {}),
                'buffer_size': memory_info.get('stats', {}).get('buffer_size', 8),
                'current_buffer_count': memory_info.get('stats', {}).get('current_buffer_count', 0),
                'summarizations_count': memory_info.get('stats', {}).get('summarizations_count', 0),
                'has_summary': memory_info.get('stats', {}).get('has_summary', False)
            }
        except Exception as e:
            api.abort(500, f'Failed to retrieve memory: {str(e)}')

@memory_ns.route('/clear')
class ClearMemory(Resource):
    @api.response(200, 'Memory cleared successfully')
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc('clear_memory')
    def post(self):
        """Clear conversation memory"""
        try:
            # Clear the memory using the new system
            workflow.agent.clear_memory()
            return {'success': True, 'message': 'Memory cleared successfully'}
        except Exception as e:
            api.abort(500, f'Failed to clear memory: {str(e)}')

# Add a health check endpoint
health_ns = api.namespace('health', description='Health check operations')

@health_ns.route('')
class Health(Resource):
    @api.doc('health_check')
    def get(self):
        """Health check endpoint"""
        return {'status': 'healthy', 'message': 'AI Agent Chat API is running'}

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Flask API server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    # Run the app on the specified port and bind to all interfaces
    app.run(debug=True, host='0.0.0.0', port=args.port)