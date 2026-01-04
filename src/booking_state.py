"""Booking state machine for appointment scheduling."""
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BookingStateMachine:
    """State machine for multi-step appointment booking."""
    
    def __init__(self):
        """Initialize booking state."""
        self.state = "START"
        self.collected = {
            "service": None,
            "date": None,
            "time": None,
            "patient_name": None,
            "phone": None,
            "email": None
        }
    
    def process(self, entities: Dict, services: Dict, availabilities: Dict) -> str:
        """
        Process booking step with new entities.
        
        Args:
            entities: Extracted entities from user input
            services: Available services
            availabilities: Available time slots
            
        Returns:
            Response message for user
        """
        # Update collected data
        for key, value in entities.items():
            if key in self.collected and value:
                self.collected[key] = value
        
        # State machine logic
        if self.state == "START":
            return self._state_start(services)
        elif self.state == "NEED_SERVICE":
            return self._state_need_service(services)
        elif self.state == "NEED_DATE":
            return self._state_need_date(availabilities)
        elif self.state == "NEED_TIME":
            return self._state_need_time(availabilities)
        elif self.state == "NEED_PATIENT_INFO":
            return self._state_need_patient_info()
        elif self.state == "CONFIRM":
            return self._state_confirm(services)
        
        return "Something went wrong. Let's start over. What service would you like?"
    
    def _state_start(self, services: Dict) -> str:
        """Initial state - check if service is known."""
        if self.collected["service"]:
            service = services.get(self.collected["service"])
            if service:
                self.state = "NEED_DATE"
                return f"""Great! You'd like to book {service['name']}.

This appointment takes {service['duration_minutes']} minutes and costs €{service['price_eur']}.

What date would you prefer? We have availability from January 6th to 10th, 2025."""
        
        # Ask for service
        self.state = "NEED_SERVICE"
        services_list = "\n".join([
            f"{i+1}. {s['name']} - €{s['price_eur']}"
            for i, s in enumerate(services.values())
        ])
        return f"""What type of appointment would you like to book?

{services_list}

Please tell me the service name or number."""
    
    def _state_need_service(self, services: Dict) -> str:
        """Waiting for service selection."""
        if self.collected["service"]:
            service = services.get(self.collected["service"])
            if service:
                self.state = "NEED_DATE"
                return f"""Perfect! {service['name']} selected.

What date works for you? Available dates: January 6-10, 2025."""
        
        return "I didn't catch which service you'd like. Could you please repeat the service name?"
    
    def _state_need_date(self, availabilities: Dict) -> str:
        """Waiting for date selection."""
        if self.collected["date"]:
            # Convert relative date to actual date
            date_str = self._resolve_date(self.collected["date"])
            
            if date_str in availabilities:
                self.collected["date"] = date_str
                self.state = "NEED_TIME"
                
                # Show available times
                available_times = [
                    time for time, available in availabilities[date_str].items()
                    if available
                ]
                times_str = ", ".join(available_times)
                return f"""Excellent! Date {date_str} selected.

Available times: {times_str}

What time would you prefer?"""
            else:
                return f"Sorry, we don't have availability on {date_str}. Please choose from January 6-10, 2025."
        
        return "What date would you like? Please choose from January 6-10, 2025."
    
    def _state_need_time(self, availabilities: Dict) -> str:
        """Waiting for time selection."""
        if self.collected["time"] and self.collected["date"]:
            date = self.collected["date"]
            time = self.collected["time"]
            
            if date in availabilities and time in availabilities[date]:
                if availabilities[date][time]:
                    self.state = "NEED_PATIENT_INFO"
                    return f"""Great! {date} at {time} is available.

Now I need your contact information.

Please provide your full name."""
                else:
                    return f"Sorry, {time} is not available on {date}. Please choose another time."
        
        return "What time would you prefer?"
    
    def _state_need_patient_info(self) -> str:
        """Waiting for patient information."""
        if not self.collected["patient_name"]:
            return "Please provide your full name."
        
        if not self.collected["phone"]:
            return "Thank you! What's your phone number?"
        
        # All info collected
        self.state = "CONFIRM"
        return "Perfect! Let me confirm your appointment details..."
    
    def _state_confirm(self, services: Dict) -> str:
        """Confirmation state."""
        service = services.get(self.collected["service"])
        
        confirmation = f"""APPOINTMENT CONFIRMATION

Service: {service['name']}
Date: {self.collected['date']}
Time: {self.collected['time']}
Duration: {service['duration_minutes']} minutes
Price: €{service['price_eur']}

Patient: {self.collected['patient_name']}
Phone: {self.collected['phone']}

Preparation: {service['special_preparation']}

Your appointment is confirmed! We'll send you a reminder 24 hours before.

Is there anything else I can help you with?"""
        
        self.state = "COMPLETE"
        return confirmation
    
    def _resolve_date(self, date_input: str) -> str:
        """Convert relative date to YYYY-MM-DD format."""
        today = datetime.now()
        
        if date_input == "tomorrow":
            target = today + timedelta(days=1)
            return target.strftime("%Y-%m-%d")
        
        # If already in YYYY-MM-DD format
        if len(date_input) == 10 and date_input.count("-") == 2:
            return date_input
        
        # Weekday names
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        if date_input.lower() in weekdays:
            target_weekday = weekdays.index(date_input.lower())
            current_weekday = today.weekday()
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            return target.strftime("%Y-%m-%d")
        
        return date_input
    
    def is_complete(self) -> bool:
        """Check if booking is complete."""
        return self.state == "COMPLETE"
    
    def get_appointment_data(self) -> Dict:
        """Get final appointment data."""
        return {
            "service": self.collected["service"],
            "date": self.collected["date"],
            "time": self.collected["time"],
            "patient_name": self.collected["patient_name"],
            "phone": self.collected["phone"],
            "email": self.collected.get("email"),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
