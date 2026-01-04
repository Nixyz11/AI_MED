"""Design 1: Intent Router implementation."""
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class IntentRouter:
    """Routes user queries to appropriate handlers based on intent."""
    
    def __init__(self, llm_interface, data_dir: str = "data"):
        """
        Initialize intent router.
        
        Args:
            llm_interface: LocalLLM instance
            data_dir: Directory containing data files
        """
        self.llm = llm_interface
        self.data_dir = data_dir
        
        # Load data
        self.services = self._load_json("services.json")
        self.availabilities = self._load_json("availabilities.json")
        self.appointments = self._load_appointments()
        
        # Clinic info
        self.clinic_info = {
            "name": "MedClinic",
            "hours": "Monday-Friday: 9:00-17:00",
            "phone": "+381 11 123 4567",
            "address": "Kralja Petra 15, Belgrade"
        }
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return {}
    
    def _load_appointments(self) -> Dict:
        """Load or initialize appointments file."""
        filepath = os.path.join(self.data_dir, "appointments.json")
        if os.path.exists(filepath):
            return self._load_json("appointments.json")
        else:
            # Create from template
            return {"appointments": [], "last_id": 0}
    
    def _save_appointments(self):
        """Save appointments to file."""
        filepath = os.path.join(self.data_dir, "appointments.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.appointments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save appointments: {e}")
    
    def route(self, user_input: str, conversation_state: Dict) -> Dict[str, Any]:
        """
        Route user input to appropriate handler.
        
        Args:
            user_input: User's message
            conversation_state: Current conversation state
            
        Returns:
            Dict with response and updated state
        """
        # Classify intent
        intent_result = self.llm.classify_intent(user_input)
        intent = intent_result["intent"]
        
        # Extract entities
        entities = self.llm.extract_entities(user_input, intent)
        
        # Route to handler
        handlers = {
            "BOOK_APPOINTMENT": self._handle_booking,
            "SERVICE_INFO": self._handle_service_info,
            "SPECIALIST_INFO": self._handle_specialist_info,
            "HOURS_INFO": self._handle_hours_info,
            "MEDICAL_CONDITION": self._handle_medical_condition,
            "GENERAL_QUESTION": self._handle_general_question
        }
        
        handler = handlers.get(intent, self._handle_general_question)
        result = handler(user_input, entities, conversation_state)
        
        # Update state
        result["state"]["last_intent"] = intent
        result["state"]["last_entities"] = entities
        
        return result
    
    def _handle_booking(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle appointment booking intent."""
        from booking_state import BookingStateMachine
        
        # Initialize booking state machine if needed
        if "booking" not in state:
            state["booking"] = BookingStateMachine()
        
        booking_sm = state["booking"]
        
        # Process booking with extracted entities
        response = booking_sm.process(entities, self.services, self.availabilities)
        
        # If booking complete, save appointment
        if booking_sm.is_complete():
            appointment = booking_sm.get_appointment_data()
            appointment["id"] = self.appointments["last_id"] + 1
            self.appointments["last_id"] += 1
            self.appointments["appointments"].append(appointment)
            self._save_appointments()
            
            # Mark slot as unavailable
            date_key = appointment["date"]
            time_key = appointment["time"]
            if date_key in self.availabilities:
                self.availabilities[date_key][time_key] = False
            
            # Reset booking state
            state["booking"] = None
        
        return {"response": response, "state": state}
    
    def _handle_service_info(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle service information requests."""
        service_id = entities.get("service")
        
        if service_id and service_id in self.services:
            service = self.services[service_id]
            response = f"""Here's information about {service['name']}:

Price: €{service['price_eur']}
Duration: {service['duration_minutes']} minutes

{service['description']}

What's included: {service['what_is_included']}

Preparation needed: {service['special_preparation']}

Would you like to book this service?"""
        else:
            # List all services
            services_list = "\n".join([
                f"- {s['name']}: €{s['price_eur']} ({s['duration_minutes']}min)"
                for s in self.services.values()
            ])
            response = f"""We offer the following services:

{services_list}

Which service would you like to know more about?"""
        
        return {"response": response, "state": state}
    
    def _handle_specialist_info(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle specialist recommendation requests."""
        text = user_input.lower()
        
        recommendations = {
            "chest pain": ("cardiology_consultation", "Cardiologist"),
            "heart": ("cardiology_consultation", "Cardiologist"),
            "stomach": ("gastroenterology_consultation", "Gastroenterologist"),
            "digestive": ("gastroenterology_consultation", "Gastroenterologist"),
            "skin": ("dermatology_checkup", "Dermatologist"),
            "rash": ("dermatology_checkup", "Dermatologist"),
            "bone": ("orthopedic_consultation", "Orthopedist"),
            "joint": ("orthopedic_consultation", "Orthopedist"),
        }
        
        for symptom, (service_id, specialist) in recommendations.items():
            if symptom in text:
                service = self.services[service_id]
                response = f"""Based on your symptoms, I recommend seeing a {specialist}.

We offer {service['name']} for €{service['price_eur']}.

IMPORTANT: If you're experiencing severe symptoms or emergency, please call 194 or visit the nearest emergency room immediately.

Would you like to book an appointment with our {specialist}?"""
                return {"response": response, "state": state}
        
        response = """To recommend the right specialist, could you describe your symptoms in more detail? 

For example:
- Where do you feel discomfort?
- When did it start?
- How severe is it?

IMPORTANT: For emergencies, call 194 immediately."""
        return {"response": response, "state": state}
    
    def _handle_hours_info(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle working hours requests."""
        response = f"""Our clinic hours:
{self.clinic_info['hours']}

We're closed on weekends and public holidays.

You can call us at {self.clinic_info['phone']} during working hours.

Would you like to schedule an appointment?"""
        return {"response": response, "state": state}
    
    def _handle_medical_condition(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle medical condition descriptions."""
        # This is similar to specialist info but more symptom-focused
        return self._handle_specialist_info(user_input, entities, state)
    
    def _handle_general_question(self, user_input: str, entities: Dict, state: Dict) -> Dict:
        """Handle general questions."""
        response = f"""Hello! I'm here to help you with:
- Booking appointments
- Information about our services
- Specialist recommendations
- Our working hours

How can I assist you today?"""
        return {"response": response, "state": state}
