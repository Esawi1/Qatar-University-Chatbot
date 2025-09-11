# app.py - Simple Flask version to avoid Pydantic issues
import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=True)
logging.basicConfig(level=logging.INFO)

# Azure OpenAI configuration
AOAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AOAI_KEY = os.environ["AZURE_OPENAI_KEY"]
AOAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

# History configuration
HISTORY_PAIRS = int(os.getenv("HISTORY_PAIRS", "3") or "3")

# Initialize Azure OpenAI client
from openai import AzureOpenAI
aoai = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
    api_version=AOAI_API_VERSION,
)

# Initialize Flask app
app = Flask(__name__)

# Simple chat history storage (in-memory)
chat_sessions = {}

@app.route('/')
def home():
    """Serve the chat UI"""
    return send_from_directory('web', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('web', filename)

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint with Azure Search integration"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Import search functionality
        from ai import answer_question
        
        # Get or create session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Get recent history
        history = chat_sessions[session_id][-HISTORY_PAIRS*2:] if HISTORY_PAIRS > 0 else []
        
        # Check if this is a basic conversational question
        basic_greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        basic_questions = ['how are you', 'how are you doing', 'what is your name', 'who are you', 'thanks', 'thank you']
        
        message_lower = message.lower().strip()
        
        if any(greeting in message_lower for greeting in basic_greetings):
            bot_response = "Hello! I'm your Qatar University admissions assistant. How can I help you today with questions about QU admissions, programs, or requirements?"
            sources = []
        elif any(question in message_lower for question in basic_questions):
            if 'how are you' in message_lower:
                bot_response = "I'm doing great, thank you for asking! I'm here to help you with all your Qatar University questions. What would you like to know about QU admissions or programs?"
            elif 'name' in message_lower or 'who are you' in message_lower:
                bot_response = "I'm the Qatar University Admissions Assistant! I can help you with questions about admissions requirements, application deadlines, programs, fees, and other QU-related information. What would you like to know?"
            elif 'thank' in message_lower:
                bot_response = "You're very welcome! I'm happy to help. Feel free to ask me any other questions about Qatar University!"
            else:
                bot_response = "I'm here to help you with Qatar University questions! What would you like to know about admissions, programs, or requirements?"
            sources = []
        else:
            # Use Azure Search + OpenAI for QU-specific questions
            try:
                result = answer_question(message, top=5)
                bot_response = result['answer']
                sources = result['sources']
            except Exception as search_error:
                logging.warning(f"Search failed: {search_error}, falling back to basic response")
                # Fallback to basic response if search fails
                bot_response = "I'm having trouble accessing the Qatar University documents right now. Please try again later or contact QU admissions directly."
                sources = []
        
        # Store in session history
        chat_sessions[session_id].append({
            'user': message,
            'bot': bot_response
        })
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id,
            'sources': sources
        })
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/test-aoai')
def test_aoai():
    """Test Azure OpenAI connection"""
    try:
        response = aoai.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            temperature=0.7,
            max_tokens=100
        )
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
