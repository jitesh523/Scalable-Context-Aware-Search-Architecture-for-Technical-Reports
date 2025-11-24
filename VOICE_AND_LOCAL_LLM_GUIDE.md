# Phase 19 & 20: Voice Interface and Local LLM Setup Guide

This guide covers the setup and usage of the newly implemented voice interface and local LLM features.

## 🎙️ Phase 19: Voice & Real-time Interface

### Features

- **WebSocket-based Voice Communication**: Low-latency bidirectional audio streaming
- **Speech-to-Text**: OpenAI Whisper API integration with local fallback option
- **Text-to-Speech**: ElevenLabs and OpenAI TTS support
- **Real-time Transcription**: Stream audio chunks for immediate processing
- **Voice Response Caching**: Improved performance for common responses

### Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure API Keys

Add to your `.env` file:

```bash
# Voice Services
STT_PROVIDER=openai  # or 'local_whisper'
TTS_PROVIDER=openai  # or 'elevenlabs'
ELEVENLABS_API_KEY=your_elevenlabs_key_here  # Optional
DEFAULT_VOICE_ID=alloy  # OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
ENABLE_VOICE_INTERFACE=true
```

#### 3. Test Voice Services

```bash
# Test Speech-to-Text
pytest tests/test_stt.py -v

# Test Text-to-Speech
pytest tests/test_tts.py -v

# Test WebSocket connection
pytest tests/test_websocket.py -v
```

### Usage

#### WebSocket Endpoint

Connect to the voice WebSocket at:

```
ws://localhost:8000/ws/voice?token=YOUR_JWT_TOKEN
```

#### Message Format

**Send Audio Chunk:**
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio_data"
}
```

**Request Transcription:**
```json
{
  "type": "transcribe"
}
```

**Send Query:**
```json
{
  "type": "query",
  "query": "What is the status of my order?"
}
```

**Receive Response:**
```json
{
  "type": "synthesis",
  "session_id": "uuid",
  "data": {
    "audio_chunk": "base64_encoded_audio",
    "format": "mp3"
  },
  "timestamp": 1234567890.123
}
```

### Voice Providers

#### OpenAI Whisper (STT)
- **Pros**: High accuracy, multi-language support, no local setup
- **Cons**: Requires API key, network latency
- **Cost**: $0.006 per minute

#### Local Whisper (STT)
- **Pros**: Privacy, no API costs, offline capable
- **Cons**: Requires local setup, slower on CPU
- **Setup**:
  ```bash
  pip install openai-whisper
  # Download model (first use)
  ```

#### OpenAI TTS
- **Pros**: Good quality, multiple voices, reliable
- **Cons**: Requires API key
- **Cost**: $15 per 1M characters

#### ElevenLabs TTS
- **Pros**: Superior voice quality, voice cloning
- **Cons**: Higher cost, requires separate API key
- **Cost**: Varies by plan

---

## 🤖 Phase 20: Local LLM & Privacy Mode

### Features

- **Local LLM Support**: Run models locally with Ollama or LocalAI
- **Intelligent Model Routing**: Automatic selection between cloud and local models
- **Privacy Mode**: PII detection and masking before sending to LLMs
- **Optimized Prompts**: Model-specific templates for Llama 3, Phi-3, Mistral
- **Fallback Mechanisms**: Automatic failover to cloud models

### Setup

#### 1. Install Ollama

```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai
```

#### 2. Pull Models

```bash
# Llama 3 (8B - Recommended)
ollama pull llama3

# Phi-3 (3.8B - Lightweight)
ollama pull phi3

# Mistral (7B)
ollama pull mistral

# List available models
ollama list
```

#### 3. Start Ollama Server

```bash
# Ollama runs automatically after installation
# Check status:
curl http://localhost:11434/api/tags
```

#### 4. Configure Local LLM

Add to your `.env` file:

```bash
# Local LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
ENABLE_LOCAL_LLM=true
DEFAULT_PROVIDER=ollama  # or 'openai' or 'localai'

# Privacy Mode
PRIVACY_MODE=true
PII_MASKING_ENABLED=true
MASKING_STRATEGY=replace  # or 'redact', 'hash', 'partial'
USE_NER_FOR_PII=false  # Enable for better name detection
PII_SENSITIVITY=0.7
```

#### 5. Install Privacy Dependencies (Optional)

For advanced PII detection with NER:

```bash
# Install spaCy model
python -m spacy download en_core_web_sm
```

### Usage

#### Model Selection

The system automatically selects the best model based on:
- **Privacy Mode**: Prefers local models
- **Query Complexity**: Complex queries use cloud models
- **Model Availability**: Falls back if local model unavailable

#### Force Specific Provider

```python
from src.llm.model_router import ModelRouter, ModelProvider

router = ModelRouter()

# Force local model
response = await router.generate(
    "Your query here",
    provider=ModelProvider.OLLAMA
)

# Force OpenAI
response = await router.generate(
    "Your query here",
    provider=ModelProvider.OPENAI
)
```

#### Privacy Mode

When privacy mode is enabled:

1. **PII Detection**: Automatically detects emails, phones, SSNs, credit cards, names, addresses
2. **Masking**: Replaces PII with placeholders before sending to LLM
3. **Unmasking**: Restores original PII in responses (if applicable)

**Example:**

```python
from src.privacy.pii_masker import PIIMasker

masker = PIIMasker()

query = "What's the status for john.doe@example.com?"
masked_query, _, entities = masker.mask_query_response(query, "")

# masked_query: "What's the status for [EMAIL]?"
```

### Performance Comparison

| Model | Size | RAM Required | Speed (tokens/s) | Quality |
|-------|------|--------------|------------------|---------|
| Llama 3 8B | 4.7GB | 16GB | 20-30 | Excellent |
| Phi-3 3.8B | 2.3GB | 8GB | 40-50 | Good |
| Mistral 7B | 4.1GB | 16GB | 25-35 | Excellent |
| GPT-4 Turbo | Cloud | N/A | 50-100 | Excellent |

### Docker Deployment

Start all services including Ollama:

```bash
docker-compose up -d
```

Pull models inside container:

```bash
docker exec -it ollama ollama pull llama3
```

### GPU Acceleration

For NVIDIA GPUs, uncomment in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Testing

```bash
# Test Ollama client
pytest tests/test_ollama.py -v

# Test model router
pytest tests/test_model_router.py -v

# Test PII masking
pytest tests/test_pii_masker.py -v

# Integration test
pytest tests/test_local_rag.py -v
```

### Troubleshooting

#### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

#### Model Not Found

```bash
# List installed models
ollama list

# Pull missing model
ollama pull llama3
```

#### Out of Memory

- Use smaller models (Phi-3 instead of Llama 3)
- Reduce context window
- Close other applications
- Consider cloud models for complex queries

### Privacy Considerations

**When to use Privacy Mode:**
- Processing sensitive customer data
- Handling PII (emails, phones, SSNs)
- Compliance requirements (GDPR, HIPAA)
- Internal company documents

**When to use Local LLMs:**
- Maximum privacy (data never leaves your infrastructure)
- Offline/air-gapped environments
- Cost optimization for high-volume queries
- Reduced latency for simple queries

### Cost Comparison

**Cloud (OpenAI GPT-4 Turbo):**
- Input: $10 per 1M tokens
- Output: $30 per 1M tokens
- ~$0.04 per typical query

**Local (Ollama):**
- One-time hardware cost
- Electricity (~$0.001 per query)
- Free API usage

**Break-even**: ~1,000 queries/month

---

## 🔧 Configuration Reference

### Voice Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_PROVIDER` | `openai` | Speech-to-Text provider |
| `TTS_PROVIDER` | `openai` | Text-to-Speech provider |
| `ELEVENLABS_API_KEY` | - | ElevenLabs API key (optional) |
| `DEFAULT_VOICE_ID` | `alloy` | Default TTS voice |
| `ENABLE_VOICE_INTERFACE` | `true` | Enable/disable voice features |

### Local LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Default Ollama model |
| `ENABLE_LOCAL_LLM` | `false` | Enable local LLM support |
| `DEFAULT_PROVIDER` | `openai` | Default LLM provider |

### Privacy Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PRIVACY_MODE` | `false` | Enable privacy mode |
| `PII_MASKING_ENABLED` | `true` | Enable PII masking |
| `MASKING_STRATEGY` | `replace` | Masking strategy |
| `USE_NER_FOR_PII` | `false` | Use NER for name detection |
| `PII_SENSITIVITY` | `0.7` | Detection sensitivity (0.0-1.0) |

---

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [ElevenLabs API Docs](https://docs.elevenlabs.io/)
- [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [Presidio (PII Detection)](https://microsoft.github.io/presidio/)

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review test files for usage examples
3. Open an issue on GitHub
