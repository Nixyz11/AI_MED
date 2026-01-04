"""Main entry point for AI_MED Design 1: Intent Router."""
import os
import sys
import logging
from typing import Dict

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_interface import LocalLLM
from intent_router import IntentRouter
from voice_ui import VoiceInterface, SimpleVoiceUI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MedicalAssistant:
    """Main medical call center assistant."""
    
    def __init__(self, data_dir: str = "data", use_small_model: bool = True):
        """
        Initialize medical assistant.
        
        Args:
            data_dir: Directory containing data files
            use_small_model: Use small model for faster inference
        """
        logger.info("Initializing Medical Assistant (Design 1: Intent Router)...")
        
        # Initialize components
        self.data_dir = data_dir
        
        # Choose model based on flag
        if use_small_model:
            # Use tiny model for faster response
            model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        else:
            # Use slightly larger model for better accuracy
            model_name = "microsoft/DialoGPT-medium"
        
        logger.info(f"Loading LLM: {model_name}")
        self.llm = LocalLLM(model_name=model_name)
        
        logger.info("Initializing intent router...")
        self.router = IntentRouter(self.llm, data_dir=data_dir)
        
        logger.info("Initializing voice interface...")
        # Use Whisper for better accuracy if available
        try:
            self.voice = VoiceInterface(use_whisper=False)  # Set to True for Whisper
        except Exception as e:
            logger.error(f"Failed to initialize voice interface: {e}")
            logger.info("Continuing without voice support")
            self.voice = None
        
        # Conversation state
        self.conversation_state = {
            "booking": None,
            "last_intent": None,
            "last_entities": None
        }
        
        logger.info("Medical Assistant initialized successfully!")
    
    def process_message(self, message: str) -> str:
        """
        Process user message and return response.
        
        Args:
            message: User's message
            
        Returns:
            Assistant's response
        """
        try:
            # Route message through intent router
            result = self.router.route(message, self.conversation_state)
            
            # Update conversation state
            self.conversation_state = result["state"]
            
            return result["response"]
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, I'm having trouble processing your request. Could you please try again?"
    
    def run_voice_ui(self):
        """Run voice-based user interface."""
        if self.voice is None:
            logger.error("Voice interface not available")
            print("\n❌ Voice interface is not available. Please check your audio setup.\n")
            return
        
        # Create simple voice UI
        ui = SimpleVoiceUI(self.voice)
        
        # Start UI with callback
        ui.start(on_speech_callback=self.process_message)
    
    def run_text_ui(self):
        """Run text-based user interface (fallback)."""
        print("\n" + "="*60)
        print("  MEDICAL CALL CENTER - Text Assistant")
        print("="*60)
        print("\nType your messages below. Type 'quit' to exit.\n")
        
        print("Assistant: Hello! Welcome to MedClinic. How may I assist you today?\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nAssistant: Thank you for contacting MedClinic. Goodbye!\n")
                    break
                
                if not user_input:
                    continue
                
                response = self.process_message(user_input)
                print(f"\nAssistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nExiting...\n")
                break
            except Exception as e:
                logger.error(f"UI error: {e}")
                print(f"\n❌ Error: {e}\n")


def main():
    """Main function."""
    # Determine data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    
    # Create assistant
    assistant = MedicalAssistant(data_dir=data_dir, use_small_model=True)
    
    # Ask user for interface type
    print("\n" + "="*60)
    print("  AI_MED - Design 1: Intent Router")
    print("="*60)
    print("\nChoose interface:")
    print("1. Voice (recommended)")
    print("2. Text (fallback)")
    
    choice = input("\nEnter choice (1/2): ").strip()
    
    if choice == "1":
        assistant.run_voice_ui()
    else:
        assistant.run_text_ui()


if __name__ == "__main__":
    main()
