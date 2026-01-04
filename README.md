# AI_MED - Local LLM Medical Call Center Assistant

## Overview
An AI design lab for building and evaluating multiple LLM-based medical call center assistants. All models run **fully locally** using **Ollama**.

## Design Pattern 1: Intent Router (Baseline)
This implementation uses:
- **Ollama** for local LLM inference (gemma:2b, llama2, or mistral)
- Intent classification with LLM + rule-based fallback
- Entity extraction for booking parameters
- Deterministic booking state machine
- Voice-based interaction (speech-to-text + text-to-speech)

## Project Structure
```
AI_MED/
├── data/
│   ├── services.json          # Medical services catalog
│   ├── availabilities.json    # Available appointment slots
│   └── appointments.json      # Booked appointments
├── src/
│   ├── llm_interface.py       # Ollama API wrapper
│   ├── intent_router.py       # Design 1: Intent classification
│   ├── booking_state.py       # Booking state machine
│   ├── voice_ui.py            # Voice interface
│   └── main.py                # Entry point
├── tests/
│   ├── test_cases.json        # Test scenarios
│   └── evaluator.py           # Performance evaluation
├── requirements.txt
├── OLLAMA_SETUP.md           # Detailed Ollama setup guide
└── README.md
```

## Quick Start

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from [https://ollama.com/download](https://ollama.com/download)

### 2. Start Ollama Server

```bash
ollama serve
```

### 3. Pull a Model

```bash
# Recommended for testing (fastest)
ollama pull gemma:2b

# Or for better quality
ollama pull llama2
ollama pull mistral
```

### 4. Install Python Dependencies

```bash
git clone https://github.com/Nixyz11/AI_MED.git
cd AI_MED
git checkout design1

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 5. Run the Assistant

```bash
python src/main.py
```

## Usage

### Text Interface (Recommended for Testing)

```bash
python src/main.py
# Choose model: 1 (gemma:2b)
# Choose interface: 2 (Text)
```

**Example conversation:**
```
You: I want to book an appointment
Assistant: What type of appointment would you like to book?
[Lists available services]

You: Cardiology consultation
Assistant: Perfect! Cardiology Consultation selected.
What date works for you? Available dates: January 6-10, 2025.

You: tomorrow at 10am
Assistant: Great! [date] at 10:00 is available.
Now I need your contact information. Please provide your full name.

You: My name is John Smith
Assistant: Thank you! What's your phone number?

You: 555-123-4567
Assistant: [Displays confirmation with all appointment details]
```

### Voice Interface

```bash
python src/main.py
# Choose model: 1 (gemma:2b)
# Choose interface: 1 (Voice)
```

- Press ENTER to start recording
- Speak your request
- Press ENTER when done
- Assistant responds via voice

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

- **Cardiology Consultation** - €120, 45min
- **Gastroenterology Consultation** - €110, 45min
- **Abdominal Ultrasound** - €85, 30min
- **Complete Blood Analysis** - €45, 15min
- **Dermatology Check-up** - €95, 30min
- **General Health Checkup** - €100, 45min
- **Orthopedic Consultation** - €105, 40min
- **Thyroid Ultrasound** - €65, 20min

## Testing & Evaluation

```bash
# Run test suite
python tests/evaluator.py
```

**Metrics:**
- Intent classification accuracy
- Entity extraction accuracy
- Response latency
- Booking flow completion rate

## Technical Details

### Ollama Integration

**API Endpoints:**
- Generate: `POST http://localhost:11434/api/generate`
- List models: `GET http://localhost:11434/api/tags`

**Models:**
- `gemma:2b` - 1.7GB, very fast, good accuracy (~75%)
- `llama2` - 3.8GB, balanced, better accuracy (~85%)
- `mistral` - 4.4GB, slower, best accuracy (~90%)

### Fallback Behavior

If Ollama is unavailable or LLM fails:
- Automatic fallback to **rule-based intent classification**
- Uses keyword matching and pattern recognition
- Maintains full functionality without LLM

### Voice Pipeline

1. **Speech-to-Text**: Google Speech Recognition (Whisper support available)
2. **Intent Processing**: Ollama LLM + state machine
3. **Text-to-Speech**: pyttsx3 (offline TTS)

### State Management

Booking state machine tracks:
- Current intent
- Collected entities (service, date, time, patient info)
- Missing fields
- Confirmation status

## Design Tradeoffs

### Advantages
- ✅ Fast and deterministic
- ✅ Low resource usage (especially with gemma:2b)
- ✅ Predictable behavior
- ✅ Easy to debug
- ✅ Works offline (fully local)
- ✅ Automatic fallback to rules

### Limitations
- ⚠️ Less natural language flexibility
- ⚠️ Requires good prompt engineering
- ⚠️ May miss nuanced queries
- ⚠️ Intent classification limited by model size

## Model Comparison

| Model | Size | Speed | Accuracy | RAM | Use Case |
|-------|------|-------|----------|-----|----------|
| gemma:2b | 1.7GB | ⚡⚡⚡ | 75% | 2GB | Testing, development |
| llama2 | 3.8GB | ⚡⚡ | 85% | 4GB | Production (balanced) |
| mistral | 4.4GB | ⚡ | 90% | 5GB | Production (quality) |

## Troubleshooting

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed troubleshooting guide.

**Common issues:**
- Ollama not running: `ollama serve`
- Model not found: `ollama pull gemma:2b`
- Slow responses: Use smaller model or reduce max_tokens

## Next Steps

- [ ] Implement Design 2: Prompt Chain
- [ ] Implement Design 3: Few-shot Prompting
- [ ] Implement Design 4: Structured Output
- [ ] Implement Design 5: RAG
- [ ] Implement Design 6: Multi-agent Orchestrator
- [ ] Compare all designs with standardized benchmarks
- [ ] Build web UI with voice button
- [ ] Switch to local Whisper for STT

## License
MIT

## Author
Nixyz11
