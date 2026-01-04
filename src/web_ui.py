"""Flask web UI for AI_MED voice assistant."""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import logging
import base64
import io
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_interface import LocalLLM
from intent_router import IntentRouter

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')
CORS(app)  # Enable CORS for development

# Global state
assistant_state = {
    "llm": None,
    "router": None,
    "conversation_state": {
        "booking": None,
        "last_intent": None,
        "last_entities": None
    },
    "conversation_history": []
}


def initialize_assistant(model_name="gemma:2b", data_dir="data"):
    """
    Initialize the medical assistant.
    
    Args:
        model_name: Ollama model name
        data_dir: Data directory path
    """
    logger.info(f"Initializing assistant with model: {model_name}")
    
    # Initialize LLM
    assistant_state["llm"] = LocalLLM(model_name=model_name)
    
    # Initialize router
    assistant_state["router"] = IntentRouter(
        assistant_state["llm"], 
        data_dir=data_dir
    )
    
    # Add welcome message to history
    assistant_state["conversation_history"] = [{
        "role": "assistant",
        "message": "Hello! Welcome to MedClinic. I'm here to help you book appointments, answer questions about our services, and recommend specialists. How may I assist you today?",
        "timestamp": datetime.now().isoformat()
    }]
    
    logger.info("Assistant initialized successfully")


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('../static', path)


@app.route('/api/message', methods=['POST'])
def process_message():
    """
    Process a text message from the user.
    
    Expected JSON:
    {
        "message": "user message text"
    }
    
    Returns:
    {
        "response": "assistant response",
        "intent": "classified intent",
        "timestamp": "ISO timestamp"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        # Add user message to history
        assistant_state["conversation_history"].append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process through router
        result = assistant_state["router"].route(
            user_message, 
            assistant_state["conversation_state"]
        )
        
        # Update conversation state
        assistant_state["conversation_state"] = result["state"]
        
        response = result["response"]
        intent = assistant_state["conversation_state"].get("last_intent", "UNKNOWN")
        
        # Add assistant response to history
        assistant_state["conversation_history"].append({
            "role": "assistant",
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "intent": intent
        })
        
        return jsonify({
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/audio', methods=['POST'])
def process_audio():
    """
    Process audio from the user (for future Whisper integration).
    
    Expected: multipart/form-data with 'audio' file
    
    Returns: Same as /api/message
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        audio_file = request.files['audio']
        
        # TODO: Implement Whisper transcription
        # For now, return error
        return jsonify({
            "error": "Audio transcription not yet implemented. Use Web Speech API instead."
        }), 501
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get conversation history.
    
    Returns:
    {
        "history": [
            {"role": "user|assistant", "message": "...", "timestamp": "..."}
        ]
    }
    """
    return jsonify({
        "history": assistant_state["conversation_history"]
    })


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """
    Reset the conversation state.
    
    Returns:
    {
        "status": "success"
    }
    """
    assistant_state["conversation_state"] = {
        "booking": None,
        "last_intent": None,
        "last_entities": None
    }
    assistant_state["conversation_history"] = [{
        "role": "assistant",
        "message": "Hello! Welcome to MedClinic. How may I assist you today?",
        "timestamp": datetime.now().isoformat()
    }]
    
    return jsonify({"status": "success"})


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get system status.
    
    Returns:
    {
        "ollama_available": true/false,
        "model": "model_name",
        "conversation_length": number
    }
    """
    return jsonify({
        "ollama_available": assistant_state["llm"].available if assistant_state["llm"] else False,
        "model": assistant_state["llm"].model_name if assistant_state["llm"] else "none",
        "conversation_length": len(assistant_state["conversation_history"])
    })


def run_web_ui(model_name="gemma:2b", data_dir="data", host="0.0.0.0", port=5000, debug=False):
    """
    Run the web UI server.
    
    Args:
        model_name: Ollama model name
        data_dir: Data directory path
        host: Server host
        port: Server port
        debug: Debug mode
    """
    # Initialize assistant
    initialize_assistant(model_name=model_name, data_dir=data_dir)
    
    # Run Flask app
    logger.info(f"Starting web UI on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    
    # Run server
    run_web_ui(model_name="gemma:2b", data_dir=data_dir, debug=True)
