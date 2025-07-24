from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from dotenv import load_dotenv

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
    title='GPT-4o Agent Chat API',
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
            
            result = workflow.execute(user_input)
            return {
                "response": result.final_response,
                "reasoning": result.tool_outputs,
                "history": result.conversation_history,
                "agent_response": result.agent_response
            }
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