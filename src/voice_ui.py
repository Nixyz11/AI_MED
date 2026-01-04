"""Voice interface using speech recognition and text-to-speech."""
import speech_recognition as sr
import pyttsx3
import logging
import threading
import time

logger = logging.getLogger(__name__)

class VoiceInterface:
    """Handles voice input/output for the assistant."""
    
    def __init__(self, use_whisper: bool = False):
        """
        Initialize voice interface.
        
        Args:
            use_whisper: Use Whisper model for better accuracy (requires more resources)
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.use_whisper = use_whisper
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed
        self.tts_engine.setProperty('volume', 0.9)  # Volume
        
        # Try to set a pleasant voice
        voices = self.tts_engine.getProperty('voices')
        if len(voices) > 1:
            # Try to use female voice if available (usually index 1)
            self.tts_engine.setProperty('voice', voices[1].id)
        
        self.is_listening = False
        self.is_speaking = False
        
        logger.info("Voice interface initialized")
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone ready")
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
    
    def listen(self, timeout: int = 10) -> str:
        """
        Listen for voice input.
        
        Args:
            timeout: Maximum seconds to wait for speech
            
        Returns:
            Transcribed text or empty string if failed
        """
        try:
            with self.microphone as source:
                logger.info("Listening...")
                self.is_listening = True
                
                # Listen with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
                
                self.is_listening = False
                logger.info("Processing speech...")
                
                # Transcribe
                if self.use_whisper:
                    # Use Whisper model (more accurate but slower)
                    try:
                        text = self.recognizer.recognize_whisper(audio, language="en")
                    except:
                        logger.warning("Whisper failed, falling back to Google")
                        text = self.recognizer.recognize_google(audio)
                else:
                    # Use Google Speech Recognition (faster)
                    text = self.recognizer.recognize_google(audio)
                
                logger.info(f"Recognized: {text}")
                return text
                
        except sr.WaitTimeoutError:
            logger.warning("No speech detected")
            return ""
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in listen: {e}")
            return ""
        finally:
            self.is_listening = False
    
    def speak(self, text: str, async_mode: bool = False):
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            async_mode: Run in background thread
        """
        if async_mode:
            thread = threading.Thread(target=self._speak_sync, args=(text,))
            thread.start()
        else:
            self._speak_sync(text)
    
    def _speak_sync(self, text: str):
        """Synchronous speech synthesis."""
        try:
            self.is_speaking = True
            logger.info(f"Speaking: {text[:50]}...")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self.is_speaking = False
    
    def is_busy(self) -> bool:
        """Check if interface is busy listening or speaking."""
        return self.is_listening or self.is_speaking


class SimpleVoiceUI:
    """Simple voice UI for terminal-based interaction."""
    
    def __init__(self, voice_interface: VoiceInterface):
        """
        Initialize simple voice UI.
        
        Args:
            voice_interface: VoiceInterface instance
        """
        self.voice = voice_interface
        self.running = False
    
    def start(self, on_speech_callback):
        """
        Start voice UI loop.
        
        Args:
            on_speech_callback: Function to call with recognized speech
        """
        self.running = True
        
        print("\n" + "="*60)
        print("  MEDICAL CALL CENTER - Voice Assistant")
        print("="*60)
        print("\nPress ENTER to speak, then press ENTER again after you finish.")
        print("Type 'quit' to exit.\n")
        
        # Welcome message
        welcome = """Hello! Welcome to MedClinic. 
        I'm here to help you with booking appointments, 
        information about our services, and answering your questions. 
        How may I assist you today?"""
        
        self.voice.speak(welcome)
        
        while self.running:
            try:
                # Wait for user to press Enter
                user_input = input("\n[Press ENTER to speak, or type 'quit' to exit]: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    goodbye = "Thank you for calling MedClinic. Goodbye!"
                    print(f"\nAssistant: {goodbye}")
                    self.voice.speak(goodbye)
                    break
                
                # Listen for voice input
                print("\n🎤 Listening... (speak now)")
                speech_text = self.voice.listen(timeout=10)
                
                if speech_text:
                    print(f"\nYou: {speech_text}")
                    
                    # Process speech
                    response = on_speech_callback(speech_text)
                    
                    print(f"\nAssistant: {response}")
                    print("\n📢 Speaking...")
                    self.voice.speak(response)
                else:
                    print("\n❌ Could not understand. Please try again.")
                    self.voice.speak("I'm sorry, I didn't catch that. Could you please repeat?")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting...")
                break
            except Exception as e:
                logger.error(f"UI error: {e}")
                print(f"\n❌ Error: {e}")
        
        self.running = False
        print("\nVoice assistant stopped.\n")
    
    def stop(self):
        """Stop the voice UI."""
        self.running = False
