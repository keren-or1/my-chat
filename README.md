# Ollama Chat Application

A modern, feature-rich web chat application powered by local LLM inference using Ollama. No API keys, no data sent to external servers—everything runs on your machine.

## Features

- 🎨 **Beautiful Modern UI** - Dark theme with gradients, smooth animations, fully responsive
- 🤖 **Local AI** - Uses Ollama + TinyLLaMA (1.1B params, 637MB) for private inference
- ⚡ **Real-time Streaming** - Token-by-token response display for immediate feedback
- 🔧 **Simple Setup** - Works in 5 minutes with minimal dependencies
- 📊 **Zero Dependencies (Frontend)** - Pure HTML/CSS/JavaScript
- 🛡️ **Privacy-First** - All processing local, no external calls

## Screenshots

### Chat Interface
![Ollama Chat App UI](screenshots/app-ui.png)

### In-Action
![Chat in Progress](screenshots/app-chat.png)

## Quick Start (5 minutes)

### Prerequisites
- Ollama installed ([ollama.ai](https://ollama.ai))
- Python 3.11+
- 4GB+ RAM, 2GB disk space

### Setup
```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Pull model (one-time)
ollama pull tinyllama

# Terminal 3: Install dependencies and start app
uv sync          # Install dependencies
uv run app/main.py

# Open browser: http://localhost:8000
```

Done! Start chatting. 🚀

**Note:** Make sure `ollama serve` is running in a separate terminal before starting the FastAPI app.

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI backend with type hints
│   └── templates/
│       └── index.html       # Complete web UI (1000+ lines)
├── screenshots/
│   ├── app-ui.png          # Application UI screenshot
│   └── app-chat.png        # Chat interaction screenshot
├── pyproject.toml           # Project config
├── uv.lock                  # Dependencies lock
├── requirements.txt         # Alternative dependency list
├── README.md               # This file
└── PROMPTS.md              # Development documentation
```

## Technology Stack

**Backend:** FastAPI, Uvicorn, Python 3.11, Requests
**Frontend:** HTML5, CSS3, Vanilla JavaScript (no build tools)
**AI:** Ollama + TinyLLaMA

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Check service status |
| `GET` | `/api/models` | List available models |
| `GET` | `/api/info` | App metadata |
| `POST` | `/api/chat` | Send message, get response (streaming) |
| `GET` | `/` | Serve web UI |

### Example: Send a message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?", "stream": true}'
```

## Configuration

### Change the Model
Edit `app/main.py`:
```python
MODEL_NAME = "llama2"  # or any available Ollama model
```

Then: `ollama pull llama2`

### Adjust AI Parameters
In `app/main.py`, modify `ollama_payload`:
```python
"temperature": 0.7,  # 0=deterministic, 1=creative
"top_p": 0.9,       # nucleus sampling
"top_k": 40,        # vocab limiting
```

### Change Server Port
In `app/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## Usage

- **Type message** → Press Enter or click Send
- **Watch stream** → Response appears token-by-token in real-time
- **Clear chat** → Sidebar button wipes history
- **Status indicator** → Green = Ollama connected, Red = offline

### Keyboard Shortcuts
- `Enter` - Send message
- `Ctrl+C` - Stop the server (in terminal)

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Or restart: killall ollama && ollama serve
```

**Important:** Make sure you've run `ollama serve` in a separate terminal before starting the FastAPI application.

### "Model not found"
```bash
ollama list
ollama pull tinyllama
```

### "Port 8000 already in use"
Change port in `app/main.py` line `uvicorn.run(...)` to 8001, 8002, etc.

### "Slow responses"
- First call: 3-5s (model loading). Subsequent: 0.5-2s (cached)
- Close other apps to free RAM
- TinyLLaMA is already optimized for speed

## Architecture Overview

```
Browser (HTML/CSS/JS)
        ↓ (HTTP/Fetch API)
   FastAPI Server
        ↓
   Ollama Service (localhost:11434)
        ↓
   TinyLLaMA Model (1.1B params)
```

**Data Flow:**
1. User types message in browser
2. JavaScript sends POST to `/api/chat`
3. FastAPI receives request, validates
4. Sends to Ollama with model parameters
5. Ollama streams tokens back
6. FastAPI streams to browser
7. JavaScript displays in real-time

## Code Quality

✅ **Type hints** on all Python functions - Full type annotations for all function parameters and return types
✅ **Docstrings** for every endpoint - Clear documentation of what each endpoint does
✅ **Error handling** with HTTPException - Graceful error responses
✅ **CORS middleware** for flexibility - Cross-origin requests supported
✅ **Async/await** for performance - Non-blocking I/O operations
✅ **Responsive CSS** with custom properties - Mobile-friendly design
✅ **Vanilla JS** with proper event handling - No external dependencies required

## Performance Characteristics

| Operation | Time |
|-----------|------|
| First response | 3-5 seconds |
| Subsequent | 0.5-2 seconds |
| Per token | 50-100ms |
| UI response | <50ms |

## Development

### Adding a New Endpoint
```python
@app.get("/api/your-endpoint")
async def your_endpoint() -> dict:
    """Describe what this endpoint does."""
    return {"message": "response"}
```

### Customizing the UI
Edit `app/templates/index.html` - all HTML/CSS/JS in one file.

### Running Tests
```bash
# Manual API test
curl http://localhost:8000/api/health

# Browser test: Open http://localhost:8000
```

## Security

✅ **Secure by default:**
- No external API calls
- No data sent to internet
- Localhost only
- Input validation
- Error messages don't expose internals

⚠️ **For production:**
- Add HTTPS via reverse proxy (nginx)
- Implement authentication if exposing to network
- Add rate limiting for API endpoints
- Consider database for chat history

## System Requirements

- **OS:** macOS, Linux, Windows (WSL2)
- **RAM:** 4GB minimum (8GB+ recommended)
- **Disk:** 2GB for model
- **CPU:** Any modern processor
- **Network:** Optional (local-only by default)

## FAQ

**Q: Is my data safe?**
A: Yes. Everything runs locally. No external calls ever.

**Q: How fast is it?**
A: First call 3-5s (loading model), then 0.5-2s per response. Depends on your hardware.

**Q: Can I use a bigger model?**
A: Yes. Change `MODEL_NAME` and run `ollama pull <model>`. Be aware of RAM requirements.

**Q: Does it work offline?**
A: Yes, completely offline after setup.

**Q: Can I share this with others?**
A: Yes! Share the project folder. They just need Ollama + Python 3.11.

## Resources

- **Ollama:** https://ollama.ai
- **Available Models:** https://ollama.ai/library
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **TinyLLaMA:** https://github.com/jzhang38/TinyLlama

## Future Ideas

- [ ] Multiple conversations
- [ ] Export chat as PDF/JSON
- [ ] Custom system prompts
- [ ] Model switching in UI
- [ ] Chat persistence (database)
- [ ] User authentication
- [ ] Voice input/output
- [ ] Docker image

## License

MIT - Use freely, modify as needed

---

**Ready to chat with your local AI?** Run the Quick Start above and enjoy a private, powerful LLM experience! 🚀
