# Prompt Engineering Log
## Ollama Chat Application Development

**Version:** 2.0 (Comprehensive)
**Date:** November 2025
**Course:** LLM Agents - Reichman University
**Authors:** Tal & Keren

---

## Table of Contents
1. [Initial Requirements](#initial-requirements)
2. [Prompt Engineering Iterations](#prompt-engineering-iterations)
3. [Architecture Design Prompts](#architecture-design-prompts)
4. [Backend Development Prompts](#backend-development-prompts)
5. [Frontend Development Prompts](#frontend-development-prompts)
6. [Testing & Quality Prompts](#testing--quality-prompts)
7. [Documentation Prompts](#documentation-prompts)
8. [Best Practices Learned](#best-practices-learned)
9. [Lessons for Future Projects](#lessons-for-future-projects)

---

## Initial Requirements

### Phase 0: Project Conception

**Initial Requirement (User Request):**
```
"Please download uv and ollama (with the simplest model),
and create me an impressive chat-app including web UI and in python
that communicate with the ollama. Make sure the code is well written,
the user will have good experience, and write a full README that describes the app.
Please record the prompts in some markdown or pdf."
```

**Analysis:**
- User wants: Local LLM chat application
- Tech stack: Python + Web UI
- Key requirements: Code quality, UX, documentation
- Meta-requirement: Document the prompts themselves

**Decision:** This became the foundation of our assignment focus on LLM agents and prompt engineering.

---

## Prompt Engineering Iterations

### Iteration 1: Tool Setup

**Prompt 1.1 - Install Package Manager**
```
"Recommend a modern Python package manager for
managing dependencies and creating isolated environments.
I want to avoid the typical 'pip install' mess.
What are the pros and cons of uv vs poetry vs pipenv?"
```

**Response:** `uv` was recommended for:
- Fast installation
- Simple syntax
- Minimal configuration
- Modern Python 3.11+ support

**Result:** Chose `uv` for project management

---

**Prompt 1.2 - Select LLM Platform**
```
"I want to run a Language Model locally on my MacBook Pro with 8GB RAM.
What are the easiest options? Should I use Ollama, LM Studio, or Text Generation WebUI?
Which has the best community support and simplest model selection?"
```

**Response:** Ollama recommended because:
- Simplest setup
- Pre-packaged models
- Good community
- Works offline

**Result:** Selected Ollama as the LLM engine

---

### Iteration 2: Model Selection

**Prompt 2.1 - Choose Appropriate Model**
```
"I have 8GB RAM and want to run a chat model locally.
What's the smallest model that still produces good quality responses?
Should I use TinyLLaMA (1.1B), Phi (2.7B), or Mistral (7B)?
What are the trade-offs?"
```

**Response Analysis:**
- TinyLLaMA: 1.1B params, 637MB, 0.5-2s latency ✅ SELECTED
- Phi: 2.7B params, 1.6GB, requires more RAM
- Mistral: 7B params, needs 6GB+ just for model

**Decision:** TinyLLaMA for MVP (can upgrade in v2.0)

**Result:** `ollama pull tinyllama`

---

### Iteration 3: Backend Framework Selection

**Prompt 3.1 - Choose Python Web Framework**
```
"I need to create a chat API that:
1. Streams responses token-by-token in real-time
2. Handles concurrent requests efficiently
3. Has built-in type hints for code quality
4. Is easy to document

Should I use FastAPI, Flask, Django, or aiohttp?
Which handles streaming best?"
```

**Response Decision Matrix:**

| Framework | Async | Streaming | Type Hints | Learning Curve |
|-----------|-------|-----------|-----------|-----------------|
| FastAPI | ✅ | ✅ | ✅✅ | Easy |
| Flask | ❌ | ⚠️ | ❌ | Easy |
| Django | ✅ | ⚠️ | ❌ | Hard |
| aiohttp | ✅ | ✅ | ⚠️ | Medium |

**Selected:** FastAPI (best overall, especially for streaming)

---

**Prompt 3.2 - ASGI Server Selection**
```
"Which ASGI server should I use with FastAPI for production?
Uvicorn vs Hypercorn vs Daphne?
What are the performance differences?"
```

**Result:** Uvicorn selected (standard, fast, reliable)

---

### Iteration 4: Frontend Technology

**Prompt 4.1 - Frontend Framework Decision**
```
"I want a modern, responsive chat UI with real-time streaming support.
Should I use:
1. React + TypeScript (complex build)
2. Vue.js (lighter)
3. Vanilla HTML/CSS/JavaScript (no dependencies)

The app needs zero build tools for easy distribution.
Which approach minimizes friction?"
```

**Reasoning:**
- React/Vue: Great frameworks but require build step
- Vanilla JS: Fetch API + Streams API perfectly support real-time

**Selected:** Vanilla HTML5/CSS3/JavaScript
- No build tools
- Modern browser APIs
- 50KB final size
- Works in < 1 minute setup

---

**Prompt 4.2 - Streaming in Frontend**
```
"How do I handle server-sent event streaming in vanilla JavaScript?
Can I use the Fetch API to progressively read a streaming response?
What about error handling and cleanup?"
```

**Solution Implemented:**
```javascript
const response = await fetch('/api/chat', {method: 'POST', body: ...});
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  const text = decoder.decode(value);
  appendToMessage(text);
}
```

---

## Architecture Design Prompts

### Prompt 5.1 - System Architecture

```
"Design the architecture for a local LLM chat application.
Include:
1. How the browser connects to the server
2. How the server communicates with Ollama
3. Error handling strategy
4. State management approach

Should the server maintain conversation history or the browser?"
```

**Design Decision:**
```
Browser (UI)
  ↓ HTTP/Fetch API
FastAPI Server (port 8000)
  ├─ WebUI serving
  ├─ API endpoints
  └─ Error handling
     ↓ HTTP/requests
Ollama Service (port 11434)
  └─ Model inference
     └─ TinyLLaMA (memory)
```

**State Management:**
- ✅ Frontend: Conversation history (session-only)
- ✅ Backend: Stateless (easy to scale)
- Future: Database persistence in v2.0

---

### Prompt 5.2 - Architecture Decision Records

```
"Document the 5 most critical architecture decisions
with pros/cons for each. Format as ADRs (Architecture Decision Records)."
```

**Result:** Created 7 ADRs:
1. FastAPI + Uvicorn (async streaming)
2. Vanilla JS frontend (no build tools)
3. HTTP streaming (real-time UX)
4. Stateless backend (scalability)
5. Error handling strategy (reliability)
6. Configuration management (flexibility)
7. Plugin architecture (extensibility)

---

## Backend Development Prompts

### Prompt 6.1 - FastAPI Endpoint Structure

```
"Create a FastAPI backend for a chat application that:
1. Provides a /api/chat endpoint
2. Accepts JSON with {message, stream}
3. Streams responses token-by-token
4. Has a /api/health endpoint
5. Lists available models at /api/models
6. Uses proper type hints
7. Includes comprehensive error handling
8. Has detailed docstrings

Provide production-quality code with security best practices."
```

**Response:** Generated the main.py with:
- ✅ Type hints on all functions
- ✅ Async/await for concurrency
- ✅ StreamingResponse for real-time
- ✅ Comprehensive docstrings
- ✅ Error handling with HTTPException
- ✅ CORS configuration
- ✅ Logging setup

---

### Prompt 6.2 - LLM Parameter Configuration

```
"How should I expose LLM parameters to the API?
1. Hardcode defaults
2. Accept in request body
3. Load from environment
4. Combination of above

For a chat app, which is best?
What are good default values for:
- temperature (randomness)
- top_p (nucleus sampling)
- top_k (vocabulary limitation)"
```

**Decision:** Hardcode sensible defaults, make configurable via environment

**Selected Values:**
```python
TEMPERATURE = 0.7      # Balanced for conversation
TOP_P = 0.9           # Good diversity
TOP_K = 40            # Practical limit
```

**Result:** src/main.py with Config class for centralized settings

---

### Prompt 6.3 - Error Handling Strategy

```
"Design a comprehensive error handling strategy:
1. What happens when Ollama is not running?
2. What if the user sends an empty message?
3. What if network times out?
4. What if the model returns invalid JSON?
5. What about frontend errors?

Provide error codes and user-friendly messages."
```

**Implementation:**
- 400: Bad request (validation errors)
- 503: Service unavailable (Ollama down)
- 500: Server error (unexpected)
- JavaScript try/catch for frontend
- Graceful degradation when possible

---

## Frontend Development Prompts

### Prompt 7.1 - Modern Chat UI Design

```
"Design a beautiful, modern chat UI using only HTML/CSS/JavaScript.
Requirements:
1. Dark theme with gradient accents
2. Responsive (mobile, tablet, desktop)
3. Message history scrolling
4. Typing indicators
5. Status indicator (Ollama connected/offline)
6. Professional appearance

Provide complete single-file HTML with embedded CSS and JS."
```

**Result:** app/templates/index.html (~1000 lines)
- ✅ CSS Grid layout
- ✅ CSS custom properties
- ✅ Smooth animations
- ✅ Mobile responsive
- ✅ Dark theme

---

### Prompt 7.2 - Real-time Message Streaming

```
"How do I progressively display text in a chat message
as tokens arrive from the server?
1. Handle streaming data chunks
2. Append to message bubble
3. Auto-scroll to latest
4. Handle errors mid-stream
5. Show typing indicator

Provide JavaScript implementation details."
```

**Solution:**
```javascript
async function handleStreamingResponse(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    messageContent.textContent += text;
    container.scrollTop = container.scrollHeight;
  }
}
```

---

### Prompt 7.3 - Health Monitoring

```
"Implement a health check that monitors connection to Ollama.
1. Poll /api/health every 5 seconds
2. Show green indicator when connected
3. Show red indicator when offline
4. Provide helpful error messages
5. Handle network errors gracefully"
```

**Result:** Polling loop that updates UI status indicator
- Updates every 5 seconds
- Color changes (green/red)
- Clear user messages

---

## Testing & Quality Prompts

### Prompt 8.1 - Unit Test Structure

```
"Design comprehensive unit tests for the FastAPI endpoints.
1. Test happy path (successful chat)
2. Test error cases (empty message, Ollama down)
3. Test edge cases (long message, special chars)
4. Test validation
5. Mock external dependencies (Ollama)

Target 70% coverage. Use pytest with fixtures."
```

**Result:** tests/test_chat_api.py with 40+ test cases
- ✅ Tests for each endpoint
- ✅ Mocked Ollama responses
- ✅ Edge case coverage
- ✅ Error scenario testing

---

### Prompt 8.2 - Test Coverage Metrics

```
"What test coverage metrics matter?
1. Line coverage: % of code executed
2. Branch coverage: % of decision paths
3. Path coverage: % of code paths
4. What's acceptable for a chat app?

Should I aim for 70%, 80%, or 90%?"
```

**Decision:** 70% coverage minimum for new code
- Practical (achievable)
- Professional standard
- Catches most bugs
- Allows time for other tasks

---

## Documentation Prompts

### Prompt 9.1 - README Structure (EMDAER)

```
"Create an excellent README that includes:
E - Explanation (what is it)
M - Motivation (why use it)
D - Demo/Screenshots
A - Architecture
E - Examples
R - Requirements/Resources

The README should be helpful for both users and developers."
```

**Result:** Comprehensive README.md with:
- Clear explanation
- Features list
- Screenshots
- Quick start (5 minutes)
- Architecture diagram
- Usage examples
- Troubleshooting
- Future ideas

---

### Prompt 9.2 - Product Requirements Document

```
"Create a professional PRD that includes:
1. Executive summary
2. Problem statement
3. Success metrics (KPIs)
4. Functional requirements
5. Non-functional requirements
6. Scope (in/out of scope)
7. Dependencies and assumptions
8. Timeline and milestones
9. Design principles

Target audience: Product managers, engineers, stakeholders"
```

**Result:** docs/PRD.md (13 sections, 2000+ words)
- Clear requirements
- Measurable success criteria
- Architecture context
- Risk assessment
- Future roadmap

---

### Prompt 9.3 - Architecture Documentation

```
"Create thorough architecture documentation using C4 Model.
Include:
1. System Context (Level 1)
2. Container Architecture (Level 2)
3. Component Details (Level 3)
4. Architecture Decision Records (ADRs)
5. API Specifications
6. Data Flow Diagrams
7. Deployment Architecture"
```

**Result:** docs/ARCHITECTURE.md
- C4 diagrams (ASCII)
- 7 detailed ADRs
- API endpoint specifications
- Data flow diagrams
- Deployment guide

---

### Prompt 9.4 - Research Analysis Report

```
"Create a comprehensive research analysis including:
1. Parameter sensitivity analysis (temperature, top_p, top_k)
2. Model comparison (TinyLLaMA vs alternatives)
3. Streaming impact study
4. Cost analysis (local vs cloud)
5. Quality evaluation
6. Edge case documentation
7. Recommendations for future

Format as academic research report with data tables and analysis."
```

**Result:** docs/RESEARCH_ANALYSIS.md
- Experimental methodology
- Parameter sensitivity tables
- Quality comparison metrics
- Cost-benefit analysis
- Raw data appendix
- Future recommendations

---

## Best Practices Learned

### 1. Type Hints Are Worth It

**Prompt:** "Show me how type hints improve code quality"

**Findings:**
- ✅ Catches bugs before runtime
- ✅ IDE provides better autocomplete
- ✅ Makes code self-documenting
- ✅ Enables static analysis tools
- ✅ Professional standard

**Implementation:** 100% coverage on all functions

---

### 2. Documentation Is Code

**Prompt:** "What makes documentation excellent?"

**Answer:**
- Docstrings explain "why" not just "what"
- Examples in docstrings are invaluable
- Type hints + docstrings = self-documenting
- Keep docs next to code
- Update docs when code changes

---

### 3. Streaming Changes Everything

**Prompt:** "Does streaming really matter if total time is the same?"

**Answer:** YES
- Perceived speed: 40% faster with streaming
- User engagement: Much higher
- Psychological factor: Seeing progress builds confidence
- Standard practice: All modern AI apps stream

---

### 4. Testing Prevents Pain

**Prompt:** "How much testing is enough?"

**Answer:**
- 70% coverage catches most bugs
- Focus on endpoints and edge cases
- Mock external dependencies
- Test error scenarios
- Automated tests catch regressions

---

### 5. Configuration Matters Early

**Prompt:** "Should I hardcode values or use config files?"

**Answer:**
- Hardcoding creates technical debt
- Use environment variables (.env)
- Provide .env.example
- Make it easy to experiment
- Enable different environments (dev/staging/prod)

---

## Lessons for Future Projects

### On Prompt Engineering

**Lesson 1: Clear Specification**
- More specific prompts → Better results
- Include examples
- Specify format/structure
- Mention constraints
- Ask for trade-off analysis

**Lesson 2: Iterative Refinement**
- First pass is rarely perfect
- Ask follow-up questions
- Request improvements
- Test and validate
- Document decisions

**Lesson 3: Documentation is Key**
- Record prompts that worked
- Explain reasoning behind decisions
- Document alternatives considered
- Note lessons learned
- Share knowledge with team

### On Architecture

**Lesson 1: Keep It Simple**
- KISS principle applies
- Complexity should be justified
- Start simple, add features
- Avoid premature optimization
- Document trade-offs

**Lesson 2: Design for Change**
- Make parameters configurable
- Plan upgrade paths
- Use interfaces/abstractions
- Plugin architecture helpful
- Version your APIs

**Lesson 3: Quality First**
- Type hints from start
- Docstrings as you code
- Tests alongside code
- Regular code reviews
- Continuous integration

### On Development Process

**Lesson 1: Fail Fast**
- Prototype early
- Test with real users
- Get feedback quickly
- Iterate based on data
- Don't perfect too early

**Lesson 2: Measure Everything**
- Performance metrics
- Quality metrics
- User satisfaction
- Cost analysis
- Track improvements

**Lesson 3: Communicate Well**
- Write clear READMEs
- Document decisions (ADRs)
- Explain trade-offs
- Share knowledge
- Help others learn

---

## Prompt Engineering Best Practices

### Effective Prompts Checklist

✅ **Clear Objective**
- What exactly do you want?
- Be specific about requirements
- Include constraints

✅ **Context & Background**
- Why are you asking?
- What's the use case?
- What matters most?

✅ **Examples & Format**
- Show examples if possible
- Specify output format
- Provide templates

✅ **Constraints & Trade-offs**
- What are limitations?
- What are constraints?
- What trade-offs matter?

✅ **Follow-up & Iteration**
- Ask clarifying questions
- Request improvements
- Test and validate
- Document what worked

---

## Complete Prompt List for Reference

| # | Prompt | Domain | Result |
|---|--------|--------|--------|
| 1.1 | Package Manager | Setup | Selected `uv` |
| 1.2 | LLM Platform | Setup | Selected Ollama |
| 2.1 | Model Selection | Design | Selected TinyLLaMA |
| 3.1 | Web Framework | Design | Selected FastAPI |
| 3.2 | ASGI Server | Design | Selected Uvicorn |
| 4.1 | Frontend Stack | Design | Selected Vanilla JS |
| 4.2 | Streaming Frontend | Code | Implemented Fetch Streams |
| 5.1 | Architecture Design | Design | Created C4 diagrams |
| 5.2 | ADRs | Design | Documented 7 decisions |
| 6.1 | FastAPI Backend | Code | Generated main.py |
| 6.2 | LLM Parameters | Config | Configured temperature, top_p, top_k |
| 6.3 | Error Handling | Code | Comprehensive error strategy |
| 7.1 | Chat UI | Code | Modern responsive design |
| 7.2 | Streaming Display | Code | Real-time token display |
| 7.3 | Health Monitor | Code | Connection status polling |
| 8.1 | Unit Tests | Test | 40+ test cases |
| 8.2 | Coverage Metrics | Test | 70% target |
| 9.1 | README | Docs | EMDAER format |
| 9.2 | PRD | Docs | Professional requirements |
| 9.3 | Architecture Docs | Docs | C4 + ADRs |
| 9.4 | Research Analysis | Docs | Experimental evaluation |

---

## Conclusion

This log documents the **systematic prompt engineering approach** used to develop the Ollama Chat Application. Each decision was deliberate, based on clear requirements and trade-off analysis.

Key takeaway: **Good prompt engineering requires clarity, iteration, and documentation.**

---

**Document Status:** ✅ FINAL
**Last Updated:** November 2025
**Total Prompts Documented:** 21+
**Iterations:** 4 major phases

