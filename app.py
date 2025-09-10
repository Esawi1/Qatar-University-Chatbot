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
    """Simple chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Get recent history
        history = chat_sessions[session_id][-HISTORY_PAIRS*2:] if HISTORY_PAIRS > 0 else []
        
        # Prepare messages for OpenAI
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": "You are the Qatar University Assistant. Help users with questions about Qatar University admissions, programs, and general information."
        })
        
        # Add conversation history
        for turn in history:
            messages.append({"role": "user", "content": turn.get('user', '')})
            messages.append({"role": "assistant", "content": turn.get('bot', '')})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get response from Azure OpenAI
        response = aoai.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        bot_response = response.choices[0].message.content
        
        # Store in session history
        chat_sessions[session_id].append({
            'user': message,
            'bot': bot_response
        })
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id
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
    app.run(host='0.0.0.0', port=8000, debug=False)
