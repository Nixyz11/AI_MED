# Whisper STT Integration - Complete Testing Guide

## Overview

This document provides comprehensive testing instructions for the local Whisper speech-to-text integration in the AI_MED Medical Call Center Assistant. The system now uses local audio recording with Whisper for accurate speech transcription.

## Architecture

### Frontend (app.js)
- **MediaRecorder API**: Captures audio from microphone
- **Web Audio Context**: Handles audio stream initialization
- **FormData**: Sends audio to backend for processing

### Backend (web_ui.py)
- **Whisper API**: Processes audio and returns transcription
- **/api/transcribe**: New endpoint for audio-to-text conversion
- **Flask**: Handles multipart form data

## Pre-Testing Checklist

### System Requirements
- [ ] Python 3.8+
- [ ] FFmpeg installed (required for Whisper)
- [ ] Microphone access enabled
- [ ] Modern browser (Chrome 49+, Firefox 25+, Safari 14+)
- [ ] Ollama running (for LLM responses)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify FFmpeg
ffmpeg -version

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## Testing Scenarios

### 1. Audio Recording Test

**Objective**: Verify microphone access and audio capture

**Steps**:
1. Open the web UI in browser
2. Allow microphone access when prompted
3. Press and hold the voice button
4. Speak clearly: "Hello, I need an appointment"
5. Release the button

**Expected Result**:
- Button shows "Recording..." state
- Listening indicator appears
- Audio is captured without errors

### 2. Whisper Transcription Test

**Objective**: Verify local Whisper transcription accuracy

**Test Cases**:

#### Case 2.1: Simple English
- **Input**: "I have a fever and sore throat"
- **Expected**: Correct transcription in conversation
- **Acceptance**: 95%+ accuracy

#### Case 2.2: Medical Terms
- **Input**: "I need to schedule a dermatology appointment"
- **Expected**: Accurate medical term recognition
- **Acceptance**: Correct spelling of medical terms

#### Case 2.3: Background Noise
- **Input**: Say the text with mild background noise
- **Expected**: Whisper filters noise and transcribes correctly
- **Acceptance**: Still achieves >80% accuracy

#### Case 2.4: Numbers and Dates
- **Input**: "Call me at 555-123-4567 on Monday the 15th"
- **Expected**: Correct date/number recognition
- **Acceptance**: Numbers match input pattern

### 3. Intent Recognition Test

**Objective**: Verify transcribed text is correctly processed

**Steps**:
1. Transcribe: "I want to book an appointment"
2. Check assistant's response includes slot filling
3. Verify conversation shows user message and response

**Expected Results**:
- Intent: BOOK_APPOINTMENT
- Entities detected correctly
- Appropriate response generated

### 4. Speech Synthesis Test

**Objective**: Verify assistant responses are spoken

**Steps**:
1. Enable Voice Mode (button shows 🎤)
2. Transcribe a question
3. Listen for audio response

**Expected Result**:
- Response is spoken with natural prosody
- Volume and speed are appropriate
- User can interrupt with new voice input

### 5. Error Handling Test

**Objective**: Verify graceful error handling

#### Case 5.1: Microphone Denied
- **Action**: Deny microphone permission
- **Expected**: Error toast appears, button disabled

#### Case 5.2: No Speech Detected
- **Action**: Press button without speaking
- **Expected**: Timeout or "no speech" error handled

#### Case 5.3: Backend Offline
- **Action**: Stop Ollama service
- **Expected**: Status shows "Offline", fallback response provided

#### Case 5.4: Network Error
- **Action**: Disconnect network during transcription
- **Expected**: Error message shown, user can retry

### 6. End-to-End Conversation Test

**Objective**: Verify complete workflow

**Scenario**: Patient booking appointment

```
User: "I need an appointment next week"
Assistant: "What time would suit you?"
User: "Monday at 2 PM"
Assistant: "I've booked your appointment for Monday at 2 PM with Dr. Smith"
User: "What's the address?"
Assistant: "The clinic is at 123 Main Street, Suite 100"
```

**Acceptance Criteria**:
- All voice inputs transcribed correctly
- Intent recognized at each turn
- Responses are contextually appropriate
- Conversation flow is natural

## Performance Benchmarks

### Latency Targets
- Audio recording: <100ms to start
- Transcription: <3s for 10s audio
- Intent recognition: <500ms
- Total response: <5s end-to-end

### Accuracy Targets
- Transcription: >90% word accuracy
- Intent recognition: >95% accuracy
- Slot filling: >90% accuracy

## Local Whisper Model Options

### Model Sizes
```
tiny:   39M parameters  (~1s for 30s audio)   - Fast, lower accuracy
base:   74M parameters  (~2s for 30s audio)   - Balanced
small:  244M parameters (~5s for 30s audio)   - Good accuracy
medium: 769M parameters (~10s for 30s audio)  - High accuracy
large:  1.5B parameters (~30s for 30s audio)  - Highest accuracy
```

### Selection Guide
- **Low-latency requirement**: Use `tiny` or `base`
- **Medical accuracy**: Use `small` or `medium`
- **Resource constrained**: Use `tiny` or `base`
- **Maximum accuracy**: Use `medium` or `large`

## Debugging Tips

### Check Browser Console
```javascript
// Verify audio context
console.log('AudioContext State:', audioContext?.state);

// Verify stream
console.log('Stream Active:', stream?.active);

// Check transcription response
console.log('Transcription:', response.json());
```

### Check Backend Logs
```bash
# Monitor Flask logs
# Look for POST /api/transcribe requests
# Check Whisper processing time
```

### Check Whisper Setup
```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.wav")
print(result["text"])
```

## Troubleshooting

### Issue: "Microphone access is required"
**Solution**:
- Check browser permissions
- For HTTPS, ensure valid certificate
- Try in incognito/private window

### Issue: Slow transcription
**Solution**:
- Use smaller Whisper model (tiny/base)
- Check system resources
- Ensure FFmpeg is installed

### Issue: Inaccurate transcription
**Solution**:
- Use larger Whisper model (small/medium)
- Reduce background noise
- Speak more clearly and slower

### Issue: Backend returns 500 error
**Solution**:
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Check Flask error logs
- Verify audio file format (should be WAV)

## Regression Testing

### Critical Paths to Test
1. Voice input -> Transcription -> Intent -> Response -> Voice output
2. Text input -> Intent -> Response (ensure still works)
3. Reset conversation -> Clean state
4. Mode toggle Voice <-> Text

### Test Data

#### Appointment Booking
- "I need an appointment tomorrow at 3 PM"
- "Can I book a doctor's appointment?"
- "Schedule me for next Monday"

#### Symptom Inquiry
- "I have a headache and fever"
- "My leg hurts when I walk"
- "I've been coughing for 3 days"

#### Information Requests
- "What are your hours?"
- "How much does a consultation cost?"
- "Do you accept insurance?"

## Success Criteria

- [ ] All audio is captured without errors
- [ ] Whisper transcribes with >90% accuracy
- [ ] Intents are recognized correctly
- [ ] Responses are generated appropriately
- [ ] Speech synthesis works clearly
- [ ] Error handling is graceful
- [ ] Performance meets latency targets
- [ ] No crashes or console errors
- [ ] System works fully offline (except Ollama)

## Support

For issues or questions:
1. Check browser console for errors
2. Check Flask server logs
3. Verify all services are running
4. Review this testing guide
5. Open an issue on GitHub
