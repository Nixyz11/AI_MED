# AI_MED Web UI Guide

## Overview

The Web UI provides a modern, browser-based voice interface for the AI_MED medical call center assistant. It features:

- 🎤 **Press-and-hold voice button** for natural conversation
- 💬 **Text input fallback** for typing messages
- 🔊 **Text-to-speech** for assistant responses
- 📱 **Responsive design** that works on desktop and mobile
- ⚡ **Real-time status** indicator for Ollama connection
- 📊 **Conversation history** with timestamps

## Quick Start

### 1. Start Ollama

```bash
# In terminal 1
ollama serve
```

### 2. Pull a model (if not already done)

```bash
# In terminal 2
ollama pull gemma:2b
```

### 3. Start the Web UI

```bash
# In terminal 2 (or terminal 3)
cd AI_MED
python src/main.py

# Choose:
# Model: 1 (gemma:2b)
# Interface: 1 (Web UI)
```

### 4. Open in Browser

```
http://localhost:5000
```

## Features

### Voice Interaction

**How to use the voice button:**

1. **Press and HOLD** the large circular microphone button
2. **Speak** your request clearly
3. **Release** the button when done speaking
4. The assistant will:
   - Display your transcribed text
   - Process your request
   - Display the response
   - Speak the response out loud

**Tips for best voice recognition:**
- Speak clearly and at normal pace
- Reduce background noise
- Use Chrome or Edge for best compatibility
- Grant microphone permissions when prompted

### Text Input

If voice is not working or preferred:

1. Type your message in the text box at the bottom
2. Press **Enter** or click the **send button** (➤)
3. The assistant will respond in text (and voice if Voice Mode is on)

### Voice Mode Toggle

- **Voice Mode ON** (🎤): Assistant speaks responses
- **Voice Mode OFF** (⌨️): Text-only responses
- Toggle with the button in the bottom controls

### New Conversation

- Click **🔄 New Conversation** to reset the chat
- All booking state and history will be cleared

## Browser Compatibility

| Browser | Voice Input | Voice Output | Notes |
|---------|-------------|--------------|-------|
| Chrome | ✅ | ✅ | Best support |
| Edge | ✅ | ✅ | Excellent |
| Safari | ✅ | ✅ | Good (macOS/iOS) |
| Firefox | ⚠️ | ✅ | Limited voice input |

**Recommended:** Chrome or Edge for best experience

## Status Indicators

### Connection Status (Top Right)

- 🟢 **Green dot + "Connected (gemma:2b)"**: Ollama is running and model loaded
- 🔴 **Red dot + "Ollama Offline (Rule-based)"**: Ollama not available, using fallback
- 🔴 **Red dot + "Connection Error"**: Server not reachable

### Voice Button States

- **Blue/Purple gradient**: Ready to record
- **Red pulsing**: Currently listening
- **Gray/disabled**: Speaking or processing

## Example Conversations

### Booking an Appointment

```
You: I want to book a cardiology appointment

Assistant: Great! You'd like to book Cardiology Consultation.
This appointment takes 45 minutes and costs €120.
What date would you prefer? We have availability from January 6th to 10th, 2025.

You: Tomorrow at 10am

Assistant: Great! [date] at 10:00 is available.
Now I need your contact information. Please provide your full name.

You: My name is John Smith

Assistant: Thank you! What's your phone number?

You: 555-123-4567

Assistant: [Shows confirmation with all appointment details]
```

### Asking About Services

```
You: What's included in blood analysis?

Assistant: Here's information about Complete Blood Analysis:

Price: €45
Duration: 15 minutes

Comprehensive blood work and analysis

What's included: Blood collection, complete blood count (CBC), metabolic panel, lipid profile, liver and kidney function tests

Preparation needed: Fasting recommended (8-12 hours). Come early in the morning. Drink plenty of water.

Would you like to book this service?
```

### Getting Specialist Recommendation

```
You: I've been having chest pain. Which doctor should I see?

Assistant: Based on your symptoms, I recommend seeing a Cardiologist.

We offer Cardiology Consultation for €120.

IMPORTANT: If you're experiencing severe symptoms or emergency, please call 194 or visit the nearest emergency room immediately.

Would you like to book an appointment with our Cardiologist?
```

## Troubleshooting

### Microphone Not Working

**Issue:** "Speech recognition not supported" message

**Solutions:**
1. Use Chrome, Edge, or Safari
2. Check browser microphone permissions
3. Ensure you're using HTTPS (or localhost)
4. Try the text input as fallback

**Issue:** "No speech detected"

**Solutions:**
1. Speak louder or closer to microphone
2. Check system microphone settings
3. Grant microphone permission in browser
4. Test microphone in another app

### Voice Output Not Working

**Issue:** Assistant doesn't speak

**Solutions:**
1. Check if Voice Mode is enabled (🎤 icon)
2. Ensure system volume is up
3. Check browser audio permissions
4. Try toggling Voice Mode off and on

### Connection Issues

**Issue:** "Cannot connect to server"

**Solutions:**
1. Ensure `python src/main.py` is running
2. Check that port 5000 is not in use
3. Verify URL is `http://localhost:5000`
4. Check firewall settings

**Issue:** "Ollama Offline (Rule-based)"

**Solutions:**
1. Start Ollama: `ollama serve`
2. Pull model: `ollama pull gemma:2b`
3. Check Ollama status: `ollama list`
4. System will still work with rule-based fallback

### Slow Responses

**Issue:** Long processing time

**Solutions:**
1. Use `gemma:2b` instead of larger models
2. Check Ollama logs for issues
3. Ensure sufficient RAM (2GB+ free)
4. Close other applications

## Mobile Usage

The Web UI is mobile-responsive:

1. Open `http://[your-computer-ip]:5000` on mobile
2. Add to home screen for app-like experience
3. Grant microphone permissions
4. Works on iOS Safari and Android Chrome

**Note:** Computer and mobile must be on same network

## API Endpoints

For developers:

### POST `/api/message`
```json
{
  "message": "I want to book an appointment"
}
```

Response:
```json
{
  "response": "What type of appointment...",
  "intent": "BOOK_APPOINTMENT",
  "timestamp": "2026-01-04T20:00:00"
}
```

### GET `/api/status`
```json
{
  "ollama_available": true,
  "model": "gemma:2b",
  "conversation_length": 5
}
```

### POST `/api/reset`
Resets conversation state

### GET `/api/history`
Returns full conversation history

## Architecture

```
Browser (app.js)
    ↓
    ↓ Web Speech API (STT)
    ↓
    ↓ HTTP POST /api/message
    ↓
Flask Server (web_ui.py)
    ↓
    ↓ process_message()
    ↓
Intent Router (intent_router.py)
    ↓
    ↓ classify_intent()
    ↓
Ollama API (llm_interface.py)
    ↓
    ↓ POST localhost:11434/api/generate
    ↓
Ollama Server
    ↓
Local Model (gemma:2b / llama2 / mistral)
```

## Performance

**Expected latency with gemma:2b:**
- Voice recognition: 1-2 seconds
- Intent classification: 0.5-1.5 seconds
- Response generation: 1-3 seconds
- Total: **3-7 seconds**

**With llama2/mistral:**
- Add 2-5 seconds for generation
- Total: **5-12 seconds**

## Security Notes

- Web UI runs on localhost by default
- No authentication (for local development)
- HTTPS recommended for production
- Microphone access requires user permission
- No data is sent to external servers

## Next Steps

- [ ] Add local Whisper for offline STT
- [ ] Implement audio file upload
- [ ] Add conversation export
- [ ] Create mobile app wrapper
- [ ] Add user authentication
- [ ] Support multiple languages

## Support

For issues or questions:
1. Check OLLAMA_SETUP.md for Ollama issues
2. Check browser console (F12) for errors
3. Check server logs in terminal
4. Review conversation history for context
