"""Local LLM interface using small HuggingFace models."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import json
from typing import Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalLLM:
    """Interface for local LLM using HuggingFace models."""
    
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """
        Initialize local LLM.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading model {model_name} on {self.device}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.info("Falling back to rule-based system")
            self.model = None
            self.tokenizer = None
    
    def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 150) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if self.model is None or self.tokenizer is None:
            logger.warning("Model not available, returning empty response")
            return ""
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from response
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response
            
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
        if self.model is not None:
            prompt = f"""Classify this medical call center query into ONE intent:
- BOOK_APPOINTMENT: user wants to schedule/book an appointment
- SERVICE_INFO: asking about services, procedures, what's included, pricing
- SPECIALIST_INFO: asking which specialist/doctor for symptoms
- HOURS_INFO: asking about working hours, schedule
- MEDICAL_CONDITION: describing symptoms or health issues
- GENERAL_QUESTION: other questions

Query: "{user_input}"
Intent:"""
            
            response = self.generate(prompt, temperature=0.1, max_tokens=30)
            
            # Parse intent from response
            intents = [
                "BOOK_APPOINTMENT", "SERVICE_INFO", "SPECIALIST_INFO",
                "HOURS_INFO", "MEDICAL_CONDITION", "GENERAL_QUESTION"
            ]
            
            for intent in intents:
                if intent.lower() in response.lower():
                    return {"intent": intent, "confidence": 0.8}
        
        # Fallback to rule-based
        return self._rule_based_intent(user_input)
    
    def _rule_based_intent(self, user_input: str) -> Dict[str, Any]:
        """Rule-based intent classification fallback."""
        text = user_input.lower()
        
        # Booking keywords
        booking_kw = ["book", "schedule", "appointment", "reservation", "zakazati", "termin"]
        if any(kw in text for kw in booking_kw):
            return {"intent": "BOOK_APPOINTMENT", "confidence": 0.9}
        
        # Service info keywords
        service_kw = ["cost", "price", "included", "preparation", "procedure", "what is", "cena", "kako"]
        if any(kw in text for kw in service_kw):
            return {"intent": "SERVICE_INFO", "confidence": 0.85}
        
        # Specialist keywords
        specialist_kw = ["which doctor", "what specialist", "koji lekar", "koji doktor"]
        if any(kw in text for kw in specialist_kw):
            return {"intent": "SPECIALIST_INFO", "confidence": 0.85}
        
        # Hours keywords
        hours_kw = ["hours", "when open", "working time", "radno vreme", "kada radite"]
        if any(kw in text for kw in hours_kw):
            return {"intent": "HOURS_INFO", "confidence": 0.9}
        
        # Medical condition keywords
        symptom_kw = ["pain", "hurt", "symptom", "feel", "sick", "bol", "osecam"]
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
            ("heart", "cardiology_consultation"),
            ("gastro", "gastroenterology_consultation"),
            ("stomach", "gastroenterology_consultation"),
            ("digestive", "gastroenterology_consultation"),
            ("ultrasound", "abdominal_ultrasound"),
            ("blood", "blood_analysis"),
            ("blood test", "blood_analysis"),
            ("skin", "dermatology_checkup"),
            ("derma", "dermatology_checkup"),
            ("checkup", "general_checkup"),
            ("general", "general_checkup"),
            ("ortho", "orthopedic_consultation"),
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
            ("monday", "monday"),
            ("tuesday", "tuesday"),
            ("wednesday", "wednesday"),
            ("thursday", "thursday"),
            ("friday", "friday"),
        ]
        
        for pattern, date_val in date_patterns:
            if pattern in text:
                entities["date"] = date_val
                break
        
        # Time extraction
        import re
        time_match = re.search(r'(\d{1,2})[:h]?(\d{2})?\s*(am|pm)?', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = time_match.group(2) or "00"
            entities["time"] = f"{hour:02d}:{minute}"
        
        # Name extraction (simple)
        name_match = re.search(r'(?:my name is|i am|i\'m|ime mi je)\s+([a-z]+(?:\s+[a-z]+)?)', text)
        if name_match:
            entities["patient_name"] = name_match.group(1).strip()
        
        # Phone extraction
        phone_match = re.search(r'\d{3}[-\s]?\d{3}[-\s]?\d{3,4}', text)
        if phone_match:
            entities["phone"] = phone_match.group(0)
        
        return entities
