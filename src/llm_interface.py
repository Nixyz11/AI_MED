"""Local LLM interface using Ollama."""
import requests
import json
from typing import Dict, Optional, Any, List
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalLLM:
    """Interface for local LLM using Ollama."""
    
    def __init__(
        self, 
        model_name: str = "gemma:2b",
        ollama_host: str = "http://localhost:11434"
    ):
        """
        Initialize local LLM with Ollama.
        
        Args:
            model_name: Ollama model name (gemma:2b, llama2, mistral)
            ollama_host: Ollama server URL
        """
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.generate_url = f"{ollama_host}/api/generate"
        self.tags_url = f"{ollama_host}/api/tags"
        self.chat_url = f"{ollama_host}/api/chat"
        
        logger.info(f"Initializing Ollama with model: {model_name}")
        
        # Check if Ollama is running
        if not self._check_ollama_running():
            logger.error("Ollama is not running! Please start Ollama first.")
            logger.info("Run: ollama serve")
            self.available = False
            return
        
        # Check if model is available
        if not self._check_model_available():
            logger.warning(f"Model {model_name} not found locally")
            logger.info(f"Pulling model... Run: ollama pull {model_name}")
            self._pull_model()
        
        self.available = True
        logger.info(f"Ollama initialized successfully with {model_name}")
    
    def _check_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(self.tags_url, timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _check_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            response = requests.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return self.model_name in models
            return False
        except Exception as e:
            logger.error(f"Error checking models: {e}")
            return False
    
    def _pull_model(self):
        """Attempt to pull the model (logs instruction)."""
        logger.info(f"To pull the model, run: ollama pull {self.model_name}")
        logger.info("Waiting for manual model pull...")
    
    def list_models(self) -> List[str]:
        """
        List all available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.1, 
        max_tokens: int = 150
    ) -> str:
        """
        Generate text from prompt using Ollama.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self.available:
            logger.warning("Ollama not available, using fallback")
            return ""
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                }
            }
            
            logger.debug(f"Sending request to Ollama: {prompt[:100]}...")
            start_time = time.time()
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=30
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"Ollama responded in {elapsed:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                logger.debug(f"Generated: {generated_text[:100]}...")
                return generated_text
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timeout")
            return ""
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent using LLM or fallback rules.
        
        Args:
            user_input: User's message
            
        Returns:
            Dict with intent and confidence
        """
        # Try LLM first
        if self.available:
            prompt = f"""Classify this medical call center query into ONE intent category.

Available intents:
- BOOK_APPOINTMENT: user wants to schedule/book an appointment
- SERVICE_INFO: asking about services, procedures, what's included, pricing
- SPECIALIST_INFO: asking which specialist/doctor for symptoms
- HOURS_INFO: asking about working hours, schedule
- MEDICAL_CONDITION: describing symptoms or health issues
- GENERAL_QUESTION: other questions

Query: "{user_input}"

Respond with ONLY the intent category name, nothing else.
Intent:"""
            
            response = self.generate(prompt, temperature=0.1, max_tokens=30)
            
            # Parse intent from response
            intents = [
                "BOOK_APPOINTMENT", "SERVICE_INFO", "SPECIALIST_INFO",
                "HOURS_INFO", "MEDICAL_CONDITION", "GENERAL_QUESTION"
            ]
            
            # Check if response contains a valid intent
            response_upper = response.upper()
            for intent in intents:
                if intent in response_upper:
                    logger.info(f"LLM classified intent: {intent}")
                    return {"intent": intent, "confidence": 0.8}
        
        # Fallback to rule-based
        logger.info("Using rule-based intent classification")
        return self._rule_based_intent(user_input)
    
    def _rule_based_intent(self, user_input: str) -> Dict[str, Any]:
        """Rule-based intent classification fallback."""
        text = user_input.lower()
        
        # Booking keywords
        booking_kw = [
            "book", "schedule", "appointment", "reservation", "reserve",
            "zakazati", "termin", "want to", "need to", "i'd like"
        ]
        if any(kw in text for kw in booking_kw):
            return {"intent": "BOOK_APPOINTMENT", "confidence": 0.9}
        
        # Service info keywords
        service_kw = [
            "cost", "price", "included", "preparation", "prepare", "procedure",
            "what is", "how much", "cena", "kako", "tell me about"
        ]
        if any(kw in text for kw in service_kw):
            return {"intent": "SERVICE_INFO", "confidence": 0.85}
        
        # Specialist keywords
        specialist_kw = [
            "which doctor", "what specialist", "koji lekar", "koji doktor",
            "should i see", "recommend", "who should"
        ]
        if any(kw in text for kw in specialist_kw):
            return {"intent": "SPECIALIST_INFO", "confidence": 0.85}
        
        # Hours keywords
        hours_kw = [
            "hours", "when open", "working time", "radno vreme", 
            "kada radite", "open", "available"
        ]
        if any(kw in text for kw in hours_kw) and "appointment" not in text:
            return {"intent": "HOURS_INFO", "confidence": 0.9}
        
        # Medical condition keywords
        symptom_kw = [
            "pain", "hurt", "ache", "symptom", "feel", "sick", "problem",
            "bol", "osecam", "having", "suffering"
        ]
        if any(kw in text for kw in symptom_kw):
            return {"intent": "MEDICAL_CONDITION", "confidence": 0.8}
        
        return {"intent": "GENERAL_QUESTION", "confidence": 0.6}
    
    def extract_entities(self, user_input: str, intent: str) -> Dict[str, Any]:
        """
        Extract entities from user input based on intent.
        
        Args:
            user_input: User's message
            intent: Classified intent
            
        Returns:
            Dict of extracted entities
        """
        entities = {}
        text = user_input.lower()
        
        # Service/specialty extraction
        services = [
            ("cardiology", "cardiology_consultation"),
            ("cardiologist", "cardiology_consultation"),
            ("heart", "cardiology_consultation"),
            ("cardiac", "cardiology_consultation"),
            ("gastro", "gastroenterology_consultation"),
            ("gastroenterology", "gastroenterology_consultation"),
            ("stomach", "gastroenterology_consultation"),
            ("digestive", "gastroenterology_consultation"),
            ("ultrasound", "abdominal_ultrasound"),
            ("blood", "blood_analysis"),
            ("blood test", "blood_analysis"),
            ("blood work", "blood_analysis"),
            ("skin", "dermatology_checkup"),
            ("derma", "dermatology_checkup"),
            ("dermatology", "dermatology_checkup"),
            ("checkup", "general_checkup"),
            ("general", "general_checkup"),
            ("ortho", "orthopedic_consultation"),
            ("orthopedic", "orthopedic_consultation"),
            ("bone", "orthopedic_consultation"),
            ("joint", "orthopedic_consultation"),
            ("thyroid", "thyroid_ultrasound")
        ]
        
        for keyword, service_id in services:
            if keyword in text:
                entities["service"] = service_id
                break
        
        # Date extraction (simple patterns)
        date_patterns = [
            ("tomorrow", "tomorrow"),
            ("sutra", "tomorrow"),
            ("today", "today"),
            ("danas", "today"),
            ("monday", "monday"),
            ("tuesday", "tuesday"),
            ("wednesday", "wednesday"),
            ("thursday", "thursday"),
            ("friday", "friday"),
            ("saturday", "saturday"),
            ("sunday", "sunday"),
        ]
        
        for pattern, date_val in date_patterns:
            if pattern in text:
                entities["date"] = date_val
                break
        
        # Time extraction
        import re
        
        # Match patterns like: 10am, 2pm, 14:00, 9:30
        time_patterns = [
            r'(\d{1,2})\s*(?:am|a\.m\.)',  # 10am, 10 am
            r'(\d{1,2})\s*(?:pm|p\.m\.)',  # 2pm, 2 pm
            r'(\d{1,2}):(\d{2})',           # 14:00, 9:30
            r'(\d{1,2})\s*h',               # 10h
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'pm' in text.lower() or 'p.m.' in text.lower():
                    hour = int(match.group(1))
                    if hour < 12:
                        hour += 12
                    entities["time"] = f"{hour:02d}:00"
                elif 'am' in text.lower() or 'a.m.' in text.lower():
                    hour = int(match.group(1))
                    entities["time"] = f"{hour:02d}:00"
                elif ':' in match.group(0):
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    entities["time"] = f"{hour:02d}:{minute:02d}"
                else:
                    hour = int(match.group(1))
                    entities["time"] = f"{hour:02d}:00"
                break
        
        # Name extraction (simple)
        name_patterns = [
            r'(?:my name is|i am|i\'m|ime mi je|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:this is|i\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input)  # Use original case
            if match:
                entities["patient_name"] = match.group(1).strip()
                break
        
        # Phone extraction
        phone_patterns = [
            r'\+?\d{1,3}[-\s]?\d{2,3}[-\s]?\d{3}[-\s]?\d{3,4}',  # International or local
            r'\d{3}[-\s]?\d{3}[-\s]?\d{3,4}',  # Simple format
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                entities["phone"] = match.group(0).strip()
                break
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, user_input)
        if email_match:
            entities["email"] = email_match.group(0)
        
        logger.info(f"Extracted entities: {entities}")
        return entities
