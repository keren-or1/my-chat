# Architecture Documentation
## Ollama Chat Application - System Design & Decisions

**Version:** 1.0
**Last Updated:** November 2025

---

### Related Documentation
- **[README.md](../README.md)** - Setup instructions and usage guide
- **[PRD.md](./PRD.md)** - Product requirements and specifications
- **[RESEARCH_ANALYSIS.md](./RESEARCH_ANALYSIS.md)** - Parameter analysis and performance metrics
- **[PROMPTS.md](PROMPTS.md)** - Development prompts and decisions

---

## Table of Contents
1. [System Context (C4 Level 1)](#system-context-c4-level-1)
2. [Container Architecture (C4 Level 2)](#container-architecture-c4-level-2)
3. [Component Architecture (C4 Level 3)](#component-architecture-c4-level-3)
4. [Architecture Decision Records (ADRs)](#architecture-decision-records-adrs)
5. [API Specifications](#api-specifications)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Deployment Architecture](#deployment-architecture)

---

## System Context (C4 Level 1)

### High-Level System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      End User                                 │
│               (Using Web Browser)                             │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Uses
                             ▼
┌──────────────────────────────────────────────────────────────┐
│              Ollama Chat Application                          │
│                                                               │
│  - Web-based chat interface                                  │
│  - Local LLM inference                                       │
│  - No external API calls                                     │
│  - Privacy-first architecture                                │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Uses Ollama API
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  Ollama Service                               │
│                                                               │
│  - LLM Inference Engine                                      │
│  - Model Management                                          │
│  - Token Generation                                          │
│  - Parameter Control                                         │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Loads Model
                             ▼
┌──────────────────────────────────────────────────────────────┐
│              TinyLLaMA 1.1B Model                             │
│                                                               │
│  - Language Understanding                                    │
│  - Text Generation                                           │
│  - Inference Engine                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Container Architecture (C4 Level 2)

### System Decomposition

```
┌────────────────────────────────────────────────────────┐
│                 Ollama Chat System                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Web Browser Container                    │ │
│  ├──────────────────────────────────────────────────┤ │
│  │                                                  │ │
│  │  HTML/CSS/JavaScript Frontend                   │ │
│  │  - Single-page application                      │ │
│  │  - Real-time message display                    │ │
│  │  - Streaming response handling                  │ │
│  │  - Health monitoring                            │ │
│  │  - Chat UI with message history                 │ │
│  │                                                  │ │
│  │  Technologies:                                  │ │
│  │  - HTML5 (semantic markup)                      │ │
│  │  - CSS3 (gradients, animations)                 │ │
│  │  - Vanilla JavaScript (no build tools)          │ │
│  │                                                  │ │
│  └────────────────┬─────────────────────────────────┘ │
│                   │ HTTP/Fetch API                     │
│                   ▼                                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │    FastAPI Backend Container                    │ │
│  ├──────────────────────────────────────────────────┤ │
│  │                                                  │ │
│  │  Core Modules:                                  │ │
│  │  - src/main.py                                  │ │
│  │    * FastAPI application setup                  │ │
│  │    * Endpoint definitions                       │ │
│  │    * CORS middleware                            │ │
│  │    * Ollama API integration                     │ │
│  │    * Streaming response handling                │ │
│  │    * Error handling & validation                │ │
│  │                                                  │ │
│  │  API Endpoints:                                 │ │
│  │  - GET /api/health          [Service health]   │ │
│  │  - GET /api/models          [Available models] │ │
│  │  - POST /api/chat           [Chat request]     │ │
│  │  - GET /api/info            [App info]         │ │
│  │  - GET /                    [UI serving]       │ │
│  │                                                  │ │
│  │  Technologies:                                  │ │
│  │  - FastAPI (async framework)                    │ │
│  │  - Uvicorn (ASGI server)                        │ │
│  │  - Python 3.11+ (type hints)                    │ │
│  │  - requests library (HTTP client)               │ │
│  │                                                  │ │
│  └────────────────┬─────────────────────────────────┘ │
│                   │ HTTP Requests                      │
│                   ▼                                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Ollama Service Container                     │ │
│  ├──────────────────────────────────────────────────┤ │
│  │                                                  │ │
│  │  External Service (localhost:11434)             │ │
│  │  - Model inference engine                       │ │
│  │  - Token generation                             │ │
│  │  - Parameter control (temperature, top_p, etc) │ │
│  │  - Response streaming                           │ │
│  │                                                  │ │
│  │  API Endpoints Used:                            │ │
│  │  - POST /api/generate    [Text generation]     │ │
│  │  - GET /api/tags         [Model listing]       │ │
│  │                                                  │ │
│  │  Note: External to our application              │ │
│  │                                                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## Component Architecture (C4 Level 3)

### Backend Components Detailed View

```
┌─────────────────────────────────────────────────────────┐
│              src/main.py Components                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Application Setup                                │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  - FastAPI() instance creation                    │ │
│  │  - CORS Middleware configuration                 │ │
│  │  - Static files mounting                         │ │
│  │  - Configuration constants                       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Request Handlers (Endpoints)                     │ │
│  ├────────────────────────────────────────────────────┤ │
│  │                                                   │ │
│  │  1. Health Check Endpoint                        │ │
│  │     ├─ Route: GET /api/health                   │ │
│  │     ├─ Purpose: Verify service connectivity     │ │
│  │     ├─ Logic:                                    │ │
│  │     │  └─ Check Ollama service availability     │ │
│  │     └─ Return: Status JSON                      │ │
│  │                                                   │ │
│  │  2. Models Endpoint                              │ │
│  │     ├─ Route: GET /api/models                   │ │
│  │     ├─ Purpose: List available Ollama models    │ │
│  │     ├─ Logic:                                    │ │
│  │     │  └─ Fetch models from Ollama API         │ │
│  │     └─ Return: Models list                      │ │
│  │                                                   │ │
│  │  3. Chat Endpoint                                │ │
│  │     ├─ Route: POST /api/chat                    │ │
│  │     ├─ Purpose: Main chat functionality         │ │
│  │     ├─ Request: {message: str, stream: bool}   │ │
│  │     ├─ Logic:                                    │ │
│  │     │  ├─ Validate request body                 │ │
│  │     │  ├─ Check message not empty               │ │
│  │     │  ├─ Prepare Ollama payload                │ │
│  │     │  ├─ Send to Ollama API                    │ │
│  │     │  ├─ Handle streaming response             │ │
│  │     │  └─ Stream tokens to client               │ │
│  │     └─ Return: StreamingResponse or Dict        │ │
│  │                                                   │ │
│  │  4. Info Endpoint                                │ │
│  │     ├─ Route: GET /api/info                     │ │
│  │     ├─ Purpose: Application metadata            │ │
│  │     ├─ Logic:                                    │ │
│  │     │  └─ Return application information        │ │
│  │     └─ Return: Info JSON                        │ │
│  │                                                   │ │
│  │  5. UI Serving Endpoint                          │ │
│  │     ├─ Route: GET /                             │ │
│  │     ├─ Purpose: Serve main chat interface       │ │
│  │     ├─ Logic:                                    │ │
│  │     │  └─ Return index.html from templates      │ │
│  │     └─ Return: FileResponse (HTML)              │ │
│  │                                                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Error Handling Layer                             │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  - JSON validation errors (400)                   │ │
│  │  - Empty message validation (400)                 │ │
│  │  - Ollama connection errors (503)                 │ │
│  │  - Ollama API errors (5xx passthrough)            │ │
│  │  - Generic server errors (500)                    │ │
│  │  - HTTPException with detail messages             │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Frontend Components Detailed View

```
┌─────────────────────────────────────────────────────────┐
│          app/templates/index.html Components            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  HTML Structure                                   │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  - Header: App title, info                        │ │
│  │  - Main container: Chat area + sidebar            │ │
│  │  - Chat display: Messages (user + assistant)      │ │
│  │  - Input form: Message input + send button        │ │
│  │  - Sidebar: Status, clear chat, info             │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  CSS Styling                                       │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  - CSS Variables: Colors, spacing, fonts          │ │
│  │  - Flexbox layout: Responsive design              │ │
│  │  - Animations: Smooth transitions                 │ │
│  │  - Dark theme: Modern gradient accents             │ │
│  │  - Mobile-first: Responsive breakpoints           │ │
│  │  - Message styling: User vs Assistant bubbles     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  JavaScript Functionality                         │ │
│  ├────────────────────────────────────────────────────┤ │
│  │                                                   │ │
│  │  Core Functions:                                  │ │
│  │  ├─ setupHealthCheck()                           │ │
│  │  │  └─ Polls /api/health every 5 seconds        │ │
│  │  │  └─ Updates status indicator                 │ │
│  │  │                                              │ │
│  │  ├─ sendMessage()                               │ │
│  │  │  ├─ Gets message from input field             │ │
│  │  │  ├─ Validates non-empty                       │ │
│  │  │  ├─ Adds to UI immediately                    │ │
│  │  │  ├─ Sends POST to /api/chat                  │ │
│  │  │  └─ Handles streaming response                │ │
│  │  │                                              │ │
│  │  ├─ handleStreamingResponse()                    │ │
│  │  │  ├─ Creates response ReadableStream           │ │
│  │  │  ├─ Reads chunks progressively                │ │
│  │  │  ├─ Decodes text (UTF-8)                      │ │
│  │  │  ├─ Appends to message bubble                 │ │
│  │  │  ├─ Scrolls to latest message                 │ │
│  │  │  └─ Handles errors gracefully                 │ │
│  │  │                                              │ │
│  │  ├─ clearChat()                                 │ │
│  │  │  ├─ Shows confirmation dialog                 │ │
│  │  │  └─ Clears message display                    │ │
│  │  │                                              │ │
│  │  ├─ displayMessage()                            │ │
│  │  │  ├─ Creates message DOM element               │ │
│  │  │  ├─ Applies styling (user vs assistant)      │ │
│  │  │  ├─ Inserts into DOM                         │ │
│  │  │  └─ Auto-scrolls chat                        │ │
│  │  │                                              │ │
│  │  └─ Event Listeners:                            │ │
│  │     ├─ Send button click                         │ │
│  │     ├─ Input Enter key                           │ │
│  │     ├─ Clear button click                        │ │
│  │     └─ Form submit prevention                    │ │
│  │                                                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture Decision Records (ADRs)

### ADR-1: Backend Framework Selection

**Status:** ACCEPTED

**Context:**
The backend needed to support streaming responses and handle concurrent requests efficiently. Key requirements were:
- Real-time token-by-token response streaming
- Type hints for code quality
- High performance
- Async/await support

**Decision:**
Use **FastAPI** with **Uvicorn** as the ASGI server.

**Alternatives Considered:**
1. Flask - Simpler but no native async support
2. Django - Overkill for this use case, slower startup
3. aiohttp - More low-level, less batteries-included
4. Starlette - Raw ASGI, less DX than FastAPI

**Rationale:**
- FastAPI provides async/await native support
- Built-in StreamingResponse for efficient token streaming
- Type hints are first-class, improving code quality
- Automatic OpenAPI documentation
- High performance with Uvicorn (ASGI)
- Easy CORS middleware integration
- Excellent for microservices

**Consequences:**
- Small dependency footprint
- Python 3.7+ required for async syntax
- Streaming works efficiently for real-time UX

---

### ADR-2: Frontend Technology Stack

**Status:** ACCEPTED

**Context:**
Frontend needed to support:
- Real-time streaming message display
- No external API key exposure
- Minimal dependencies for simplicity
- Cross-browser compatibility

**Decision:**
Use **Vanilla HTML5/CSS3/JavaScript** (no framework or build tools).

**Alternatives Considered:**
1. React + TypeScript - Overkill for simple UI, requires build step
2. Vue.js - Still requires build tools
3. jQuery - Legacy, not modern patterns
4. Web Components - Good but more complexity

**Rationale:**
- Zero build step (5-minute setup goal)
- Minimal dependencies to ship/maintain
- Native Fetch API handles streaming elegantly
- Modern browsers have all needed features
- Easier for students to understand
- FileResponse serving single HTML file is simple

**Consequences:**
- Need to be careful with DOM manipulation
- No component abstraction (but single file is OK for this size)
- Larger HTML file (but still <50KB)
- Must handle browser compatibility manually

---

### ADR-3: Streaming Implementation

**Status:** ACCEPTED

**Context:**
Users expect real-time feedback (tokens appearing as they're generated). Two options:
1. Buffer entire response, send once
2. Stream tokens in real-time

**Decision:**
Implement **HTTP streaming** with `text/event-stream` media type and progressive text rendering.

**Alternatives Considered:**
1. WebSocket - More complex, requires WebSocket server
2. Server-Sent Events (SSE) - Similar to streaming but standardized
3. Long polling - Inefficient, not real-time
4. Complete response buffering - Bad UX, no perceived progress

**Rationale:**
- Fetch API natively supports streaming with `response.body.getReader()`
- `text/event-stream` allows progressive updates
- Better perceived performance
- No WebSocket complexity
- Works with any reverse proxy (nginx, etc.)

**Consequences:**
- Must handle chunked encoding properly
- Need error handling for stream interruptions
- Frontend must accumulate text progressively

---

### ADR-4: Error Handling Strategy

**Status:** ACCEPTED

**Context:**
Several error scenarios are possible:
- Ollama not running (503)
- Invalid JSON request (400)
- Empty message (400)
- Ollama model errors (500)
- Network timeouts
- Browser-side request failures

**Decision:**
Implement **graceful error handling** with:
- HTTPException for all API errors
- Meaningful error messages for users
- Try/catch for exception-based error handling
- Frontend error display in UI

**Error Codes:**
| Code | Scenario | Handling |
|------|----------|----------|
| 400 | Bad request (invalid JSON, empty message) | User sees validation message |
| 503 | Ollama unavailable | Status indicator red, helpful message |
| 500 | Server error | Generic error message, suggest restart |

**Consequences:**
- Users get helpful feedback instead of crashes
- No sensitive information in error messages
- Resilient operation even with Ollama down
- Easy debugging with error logs

---

### ADR-5: Configuration Management

**Status:** PROPOSED (for improvement)

**Context:**
Currently configuration is hardcoded:
```python
OLLAMA_API_URL = "http://localhost:11434/api"
MODEL_NAME = "tinyllama"
```

This prevents easy configuration for different environments.

**Decision:**
Implement **environment variables** with `.env` file support.

**Configuration Items:**
- `OLLAMA_API_URL` - Ollama service endpoint
- `MODEL_NAME` - LLM model to use
- `API_HOST` - FastAPI host
- `API_PORT` - FastAPI port
- `LOG_LEVEL` - Logging verbosity

**Tools:**
- `python-dotenv` for .env file support
- `.env.example` for documentation
- `.gitignore` to exclude .env

**Consequences:**
- More flexible deployment
- Easier testing with different configs
- Better security (no hardcoded values)
- Production-ready configuration pattern

---

### ADR-6: State Management

**Status:** ACCEPTED

**Context:**
Application has minimal state:
- Chat message history (frontend only)
- Health status (polled, not cached)
- No persistent session data

**Decision:**
Implement **stateless backend** with **frontend-only session storage**.

**Rationale:**
- Stateless design allows horizontal scaling
- No database needed (v1.0)
- Chat history cleared on page refresh (acceptable for MVP)
- Health checks are read-only

**Consequences:**
- No conversation history persistence
- Scaling is simple (any instance can handle any request)
- Chat lost on browser tab close (acceptable)
- Future database addition is straightforward

---

### ADR-7: Extensibility Design

**Status:** PROPOSED (for future)

**Context:**
While v1.0 is simple, future versions might need:
- Custom system prompts
- Multiple conversation threads
- Conversation export
- Plugin system

**Decision:**
Design with **extensibility in mind** using:
- Modular endpoints (each concern separate)
- Clear API contracts (input/output schemas)
- Plugin hooks (future-proofed)
- Configuration-driven features

**Example Structure:**
```
app/
├── main.py (app setup, endpoints)
├── handlers/ (endpoint logic)
│   ├── chat.py
│   ├── models.py
│   └── health.py
├── schemas/ (request/response models)
│   └── chat.py
├── utils/ (helpers)
│   ├── ollama.py
│   └── validators.py
└── plugins/ (future hook system)
```

**Consequences:**
- Ready for feature additions
- Clear separation of concerns
- Easier testing of components
- Maintainable codebase

---

## API Specifications

### API Endpoints Reference

#### 1. Health Check
```
GET /api/health
```

**Purpose:** Verify service connectivity with Ollama

**Response (200 OK):**
```json
{
  "status": "healthy",
  "ollama": "connected",
  "model": "tinyllama"
}
```

**Error Responses:**
- **503 Service Unavailable:** Ollama not running
- **Timeout:** Check if `ollama serve` is running

---

#### 2. List Models
```
GET /api/models
```

**Purpose:** Get available models from Ollama

**Response (200 OK):**
```json
{
  "models": ["tinyllama", "llama2", "mistral"],
  "current_model": "tinyllama",
  "available": true
}
```

**Error Responses:**
- **503 Service Unavailable:** Ollama connection failed

---

#### 3. Chat (Main Endpoint)
```
POST /api/chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What is Python?",
  "stream": true
}
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| message | string | Yes | - | User's chat message (max 4000 chars) |
| stream | boolean | No | true | Enable streaming response |

**Response (Streaming - 200 OK):**
```
Content-Type: text/event-stream
Transfer-Encoding: chunked

Python is a high-level programming language...
```

**Response (Non-Streaming - 200 OK):**
```json
{
  "response": "Python is a high-level programming language...",
  "model": "tinyllama",
  "stream": false
}
```

**Error Responses:**
- **400 Bad Request:**
  - Invalid JSON: `{"detail": "Invalid JSON in request body"}`
  - Empty message: `{"detail": "Message cannot be empty"}`
- **503 Service Unavailable:** `{"detail": "Cannot connect to Ollama service"}`
- **500 Server Error:** `{"detail": "Server error: ..."}`

**Ollama Parameters (Hardcoded):**
```python
{
  "temperature": 0.7,    # Randomness (0=deterministic, 1=creative)
  "top_p": 0.9,         # Nucleus sampling
  "top_k": 40,          # Vocab limiting
}
```

---

#### 4. Application Info
```
GET /api/info
```

**Purpose:** Get application metadata

**Response (200 OK):**
```json
{
  "app_name": "Ollama Chat Application",
  "version": "1.0.0",
  "model": "tinyllama",
  "description": "A modern web-based chat interface for local LLM inference"
}
```

---

#### 5. Serve UI
```
GET /
```

**Purpose:** Serve the main chat application page

**Response (200 OK):**
- Content-Type: text/html
- Returns `app/templates/index.html`

**Error Responses:**
- **404 Not Found:** index.html missing

---

## Data Flow Diagrams

### Happy Path: Successful Chat Message

```
User Browser                FastAPI Backend                Ollama Service
     │                              │                              │
     │  1. Type message             │                              │
     ├─────────────────────────────►│                              │
     │  POST /api/chat              │                              │
     │  {message: "...", stream: true}
     │                              │  2. Validate message        │
     │                              ├──►                          │
     │                              │  3. Send to Ollama          │
     │                              ├─────────────────────────────►
     │                              │  4. Generate tokens         │
     │                              │◄─────────────────────────────┤
     │                              │  (streaming response)       │
     │  5. Stream tokens            │                              │
     │◄─────────────────────────────┤                              │
     │  (text/event-stream)         │                              │
     │                              │                              │
     │  6. Display in real-time     │                              │
     ├─────────────────────────────►│                              │
     │  Auto-scroll, update UI      │                              │
     │                              │                              │
     │  7. Response complete        │                              │
     │◄─────────────────────────────┤                              │
```

### Error Path: Ollama Not Running

```
User Browser                FastAPI Backend                Ollama Service
     │                              │                              │
     │  1. Type message             │                              │
     ├─────────────────────────────►│                              │
     │  POST /api/chat              │                              │
     │                              │  2. Try to connect          │
     │                              ├─────────────────────────────►
     │                              │  CONNECTION FAILED           │
     │                              │◄─────────────────────────────┤
     │  3. 503 Error                │                              │
     │◄─────────────────────────────┤                              │
     │  {detail: "Cannot connect"}  │                              │
     │                              │                              │
     │  4. Show error in UI         │                              │
     │  Inform user to start Ollama │                              │
     │                              │                              │
```

---

## Deployment Architecture

### Local Development Setup

```
Developer Machine
├─ Terminal 1: ollama serve
│  └─ Ollama Service (localhost:11434)
│     └─ TinyLLaMA Model (loaded in memory)
│
├─ Terminal 2: uv run src/main.py
│  └─ FastAPI (localhost:8000)
│     ├─ src/main.py (backend)
│     └─ src/templates/index.html (frontend)
│
└─ Browser: http://localhost:8000
   └─ User interacts via web UI
```

### Production Considerations (Future)

```
Internet
    │
    ▼
┌─────────────┐
│ Load Balancer
│ (nginx/HAProxy)
└──────┬──────┘
       │ HTTPS
       ▼
┌──────────────────┐
│ Multiple FastAPI │  (Stateless, can scale horizontally)
│ Instances        │
└────┬─────┬──────┘
     │     │ HTTP
     │     └──────────────┐
     │                    ▼
     └──────────────┐  ┌─────────────┐
                    └─►│ Ollama      │
                       │ Service     │
                       │ (Shared)    │
                       └─────────────┘
```

---

## Summary of Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Backend Framework** | FastAPI | Type hints, async, streaming support |
| **Frontend** | Vanilla JS | No build step, simple, educational |
| **Streaming** | HTTP + text/event-stream | Real-time UX, simple implementation |
| **State** | Stateless backend | Horizontal scaling ready |
| **Error Handling** | HTTPException + Try/Catch | Graceful degradation |
| **Configuration** | Environment variables (ADR-5) | Flexibility, security |
| **Extensibility** | Modular design (ADR-7) | Ready for feature growth |

---

**Document Status:** FINAL

