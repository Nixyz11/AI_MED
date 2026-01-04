# Ollama Setup Guide for AI_MED

## Prerequisites

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

Leave this running in a separate terminal. It will listen on `http://localhost:11434`.

### 3. Pull Models

Choose one or more models based on your system:

**Option 1: gemma:2b (Fastest - Recommended for testing)**
```bash
ollama pull gemma:2b
```
- Size: ~1.7GB
- Speed: Very fast
- Quality: Good for basic classification

**Option 2: llama2 (Balanced)**
```bash
ollama pull llama2
```
- Size: ~3.8GB
- Speed: Moderate
- Quality: Better understanding

**Option 3: mistral (Best Quality)**
```bash
ollama pull mistral
```
- Size: ~4.4GB
- Speed: Slower
- Quality: Best results

### 4. Verify Installation

```bash
# List available models
ollama list

# Test a model
ollama run gemma:2b "Hello, how are you?"
```

## Running AI_MED with Ollama

### 1. Install Python Dependencies

```bash
cd AI_MED
pip install -r requirements.txt
```

### 2. Run the Assistant

```bash
python src/main.py
```

You'll be prompted to:
1. Choose a model (gemma:2b, llama2, or mistral)
2. Choose interface (voice or text)

### 3. Test in Text Mode (Recommended First)

Choose option 2 (Text) for initial testing:

```
You: I want to book an appointment
Assistant: [Will classify intent and respond]

You: I need a cardiology consultation tomorrow at 10am
Assistant: [Will extract service, date, time and proceed with booking]
```

## Troubleshooting

### Ollama Server Not Running

**Error:** `Ollama is not running!`

**Solution:**
```bash
# Start Ollama in a separate terminal
ollama serve
```

### Model Not Found

**Error:** `Model gemma:2b not found locally`

**Solution:**
```bash
ollama pull gemma:2b
```

### Slow Response

- Try using `gemma:2b` instead of larger models
- Reduce `max_tokens` in `llm_interface.py` (default: 150)
- Use rule-based fallback by setting `self.available = False` in `LocalLLM.__init__`

### Port Already in Use

**Error:** `Port 11434 is already in use`

**Solution:**
```bash
# Kill existing Ollama process
pkill ollama

# Start again
ollama serve
```

## API Testing

You can test the Ollama API directly:

```bash
# Test generate endpoint
curl http://localhost:11434/api/generate -d '{
  "model": "gemma:2b",
  "prompt": "Classify this as BOOK_APPOINTMENT or SERVICE_INFO: I want to schedule a checkup",
  "stream": false
}'

# List models
curl http://localhost:11434/api/tags
```

## Performance Tips

### For Fast Responses
1. Use `gemma:2b`
2. Set temperature to 0.1 (already configured)
3. Keep max_tokens low (150 or less)
4. Run Ollama server with GPU support if available

### For Better Quality
1. Use `mistral` or `llama2`
2. Increase max_tokens to 200-300
3. Add more context to prompts

## Model Comparison

| Model | Size | Speed | Intent Accuracy | Memory Usage |
|-------|------|-------|----------------|-------------|
| gemma:2b | 1.7GB | ⚡⚡⚡ | ~75% | ~2GB RAM |
| llama2 | 3.8GB | ⚡⚡ | ~85% | ~4GB RAM |
| mistral | 4.4GB | ⚡ | ~90% | ~5GB RAM |

## Next Steps

1. ✅ Test with text interface
2. Test with voice interface (requires microphone)
3. Run evaluator: `python tests/evaluator.py`
4. Compare different models
5. Fine-tune prompts in `llm_interface.py`

## Switching to Rule-Based Fallback

If Ollama is not available or too slow, the system automatically falls back to rule-based intent classification. You can force this by:

```python
# In llm_interface.py __init__
self.available = False  # Force rule-based mode
```
