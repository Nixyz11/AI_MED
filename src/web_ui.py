"""Flask web UI for AI_MED voice assistant."""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_interface import LocalLLM
from intent_router import IntentRouter
from audio_processor import initialize_processor, get_processor

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates')
CORS(app)

# Global state
assistant_state = {
    "llm": None,
    "router": None,
    "audio_processor": None,
    "conversation_state": {
        "booking": None,
        "last_intent": None,
        "last_entities": None
    },
    "conversation_history": []
}

def initialize_assistant(model_name="gemma:2b", data_dir="data", whisper_model="base"):
    """
    Initialize the medical assistant with LLM and Whisper.
    
    Args:
        model_name: Ollama model name
        data_dir: Data directory path
        whisper_model: Whisper model size (tiny, base, small, medium, large)
    """
    logger.info(f"Initializing assistant with LLM: {model_name}, Whisper: {whisper_model}")
    
    # Initialize LLM
    assistant_state["llm"] = LocalLLM(model_name=model_name)
    
    # Initialize router
    assistant_state["router"] = IntentRouter(
        assistant_state["llm"], 
        data_dir=data_dir
    )
    
    # Initialize audio processor for Whisper
    try:
        assistant_state["audio_processor"] = initialize_processor(model_size=whisper_model)
        logger.info("Audio processor initialized successfully")
    except Exception as e:
        logger.warning(f"Audio processor initialization failed: {e}")
        assistant_state["audio_processor"] = None
    
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
    {"message": "user message text"}
    
    Returns:
    {"response": "assistant response", "intent": "...", "timestamp": "..."}
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
    Process audio from the browser using local Whisper.
    Uses local transcription - 100% offline.
    
    Expected: multipart/form-data with 'audio' file
    
    Returns:
    {
        "text": "transcribed text",
        "message_response": "assistant response",
        "intent": "classified intent",
        "confidence": 0.95
    }
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({"error": "Empty audio file"}), 400
        
        # Check if processor is available
        if not assistant_state["audio_processor"]:
            return jsonify({
                "error": "Audio processor not available. Using text mode only."
            }), 503
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Get file extension
        filename = audio_file.filename
        audio_format = filename.split('.')[-1].lower() if '.' in filename else 'webm'
        
        logger.info(f"Processing audio: {filename} ({len(audio_data)} bytes)")
        
        # Transcribe using Whisper
        processor = assistant_state["audio_processor"]
        transcript_result = processor.transcribe_audio(audio_data, audio_format=audio_format)
        
        transcribed_text = transcript_result["text"]
        
        if not transcribed_text:
            return jsonify({
                "error": "Could not transcribe audio. Try speaking more clearly."
            }), 400
        
        logger.info(f"Transcribed: {transcribed_text}")
        
        # Add user message to history
        assistant_state["conversation_history"].append({
            "role": "user",
            "message": transcribed_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process through router
        result = assistant_state["router"].route(
            transcribed_text,
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
            "text": transcribed_text,
            "message_response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat(),
            "confidence": transcript_result.get("confidence", 0.0)
        })
    
    except Exception as e:
        logger.error(f"Audio processing error: {e}", exc_info=True)
        return jsonify({"error": f"Audio processing failed: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history."""
    return jsonify({
        "history": assistant_state["conversation_history"]
    })

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation state."""
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
    """Get system status."""
    return jsonify({
        "ollama_available": assistant_state["llm"].available if assistant_state["llm"] else False,
        "model": assistant_state["llm"].model_name if assistant_state["llm"] else "none",
        "whisper_available": assistant_state["audio_processor"] is not None,
        "whisper_model": assistant_state["audio_processor"].get_model_size() if assistant_state["audio_processor"] else "none",
        "conversation_length": len(assistant_state["conversation_history"])
    })

def run_web_ui(model_name="gemma:2b", data_dir="data", whisper_model="base", host="0.0.0.0", port=5000, debug=False):

    # Alias for /api/transcribe - same as /api/audio
@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Alias for process_audio - supports /api/transcribe endpoint"""
    return process_audio()
    """
    Run the web UI server.
    
    Args:
        model_name: Ollama model name
        data_dir: Data directory path
        whisper_model: Whisper model size
        host: Server host
        port: Server port
        debug: Debug mode
    """
    # Initialize assistant
    initialize_assistant(model_name=model_name, data_dir=data_dir, whisper_model=whisper_model)
    
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
    run_web_ui(model_name="gemma:2b", data_dir=data_dir, whisper_model="base", debug=True)
