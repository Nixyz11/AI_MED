# AI_MED - Local LLM Medical Call Center Assistant

## Overview
An AI design lab for building and evaluating multiple LLM-based medical call center assistants. All models run **fully locally** using small HuggingFace models.

## Design Pattern 1: Intent Router (Baseline)
This implementation uses:
- Small local LLM for intent classification
- Entity extraction for booking parameters
- Deterministic booking state machine
- Voice-based interaction (speech-to-text + text-to-speech)

## Project Structure
```
AI_MED/
├── data/
│   ├── services.json          # Medical services catalog
│   ├── availabilities.json    # Available appointment slots
│   └── appointments.json      # Booked appointments (generated)
├── src/
│   ├── llm_interface.py       # Local model abstraction
│   ├── intent_router.py       # Design 1: Intent classification
│   ├── booking_state.py       # Booking state machine
│   ├── voice_ui.py            # Voice interface
│   └── main.py                # Entry point
├── tests/
│   ├── test_cases.json        # Test scenarios
│   └── evaluator.py           # Performance evaluation
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
1. Python 3.9+
2. FFmpeg (for audio processing)

### Setup
```bash
# Clone repository
git clone https://github.com/Nixyz11/AI_MED.git
cd AI_MED
git checkout design1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required models (automatic on first run)
```

## Usage

### Start Voice Assistant
```bash
python src/main.py
```

The assistant will:
1. Initialize local LLM (downloads on first run)
2. Load medical services and availability data
3. Start voice interface
4. Wait for you to press the microphone button to speak

### Interaction Flow
- **Press and hold** the microphone button
- **Speak** your request (e.g., "I need a cardiology appointment")
- **Release** the button
- The assistant will respond via voice

## Supported Intents

| Intent | Example |
|--------|----------|
| BOOK_APPOINTMENT | "I want to schedule a checkup" |
| SERVICE_INFO | "What's included in blood analysis?" |
| SPECIALIST_INFO | "I have chest pain, which doctor should I see?" |
| HOURS_INFO | "What are your working hours?" |
| MEDICAL_CONDITION | "I've been having headaches" |
| GENERAL_QUESTION | "How much does a consultation cost?" |

## Available Services
- Cardiology Consultation (€120, 45min)
- Gastroenterology Consultation (€110, 45min)
- Abdominal Ultrasound (€85, 30min)
- Complete Blood Analysis (€45, 15min)
- Dermatology Check-up (€95, 30min)
- General Health Checkup (€100, 45min)
- Orthopedic Consultation (€105, 40min)
- Thyroid Ultrasound (€65, 20min)

## Testing

```bash
# Run test suite
python tests/evaluator.py
```

Evaluator measures:
- Intent classification accuracy
- Entity extraction accuracy
- Response latency
- Booking flow completion rate

## Technical Details

### LLM Models
Using small HuggingFace models (< 1GB):
- **Primary**: `distilgpt2` or `TinyLlama-1.1B` for intent classification
- **Fallback**: Rule-based classification if model unavailable

### Voice Pipeline
1. **Speech-to-Text**: Whisper tiny model (local)
2. **Intent Processing**: Local LLM + state machine
3. **Text-to-Speech**: pyttsx3 (offline TTS)

### State Management
Booking state tracks:
- Current intent
- Collected entities (service, date, time, patient info)
- Missing fields
- Confirmation status

## Design Tradeoffs

### Advantages
- Fast and deterministic
- Low resource usage
- Predictable behavior
- Easy to debug

### Limitations
- Less natural language flexibility
- Requires good prompt engineering
- May miss nuanced queries

## Next Steps
- Implement Design 2: Prompt Chain
- Implement Design 3: Few-shot Prompting
- Implement Design 4: Structured Output
- Implement Design 5: RAG
- Implement Design 6: Multi-agent Orchestrator
- Compare all designs with standardized benchmarks

## License
MIT

## Author
Nixyz11