"""
Audio processing and Whisper transcription for local STT.
No cloud calls - fully offline.
"""

import os
import logging
import whisper
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Process audio files and transcribe using local Whisper model.
    Supports multiple audio formats (WAV, WEBM, MP3, etc.)
    """
    
    def __init__(self, model_size="base"):
        """
        Initialize Whisper model.
        
        Args:
            model_size: 'tiny' (39M), 'base' (140M), 'small' (244M), 
                       'medium' (769M), 'large' (2.9GB)
            
        For testing: Use 'tiny' or 'base' for speed
        For quality: Use 'small' or 'medium'
        """
        self.model_size = model_size
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load Whisper model (downloads if not cached)."""
        try:
            logger.info(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            logger.info(f"Whisper {self.model_size} model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe_audio(self, audio_bytes, audio_format="wav"):
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Raw audio data (from browser)
            audio_format: Audio format (wav, webm, mp3, etc.)
            
        Returns:
            dict with 'text', 'language', 'confidence'
        """
        if not self.model:
            raise RuntimeError("Whisper model not loaded")
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                result = self.model.transcribe(
                    tmp_path,
                    language="en",
                    fp16=False,
                    verbose=False
                )
                
                return {
                    "text": result["text"].strip(),
                    "language": result.get("language", "en"),
                    "segments": result.get("segments", []),
                    "confidence": self._calculate_confidence(result)
                }
            
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def transcribe_file(self, file_path):
        """
        Transcribe audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not self.model:
            raise RuntimeError("Whisper model not loaded")
        
        try:
            result = self.model.transcribe(file_path, language="en", fp16=False)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            raise
    
    def _calculate_confidence(self, result):
        """Calculate overall confidence score (0-1)."""
        segments = result.get("segments", [])
        if not segments:
            return 0.0
        
        confidences = [seg.get("confidence", 0.5) for seg in segments]
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def get_model_size(self):
        """Get current model size."""
        return self.model_size


_processor = None

def initialize_processor(model_size="base"):
    """Initialize global audio processor."""
    global _processor
    _processor = AudioProcessor(model_size=model_size)
    return _processor

def get_processor():
    """Get or initialize processor."""
    global _processor
    if _processor is None:
        _processor = AudioProcessor(model_size="base")
    return _processor
