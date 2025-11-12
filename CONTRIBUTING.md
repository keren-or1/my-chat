# Contributing to Ollama Chat Application

Thank you for your interest in contributing to the Ollama Chat Application! This document provides guidelines and instructions for contributing to this project.

---

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Project Structure](#project-structure)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:
- Be respectful and constructive in all interactions
- Provide helpful feedback
- Focus on what is best for the community
- Show empathy towards other contributors

---

## Getting Started

### Prerequisites
- Python 3.11+
- Ollama installed and running
- Git
- Basic knowledge of FastAPI and Python

### Fork & Clone
```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/ollama-chat.git
cd ollama-chat

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/ollama-chat.git
```

---

## Development Setup

### 1. Create Virtual Environment
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using Python venv
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
# Install from requirements.txt
pip install -r requirements.txt
pip install -e .

# Or using uv
uv pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy the example environment file
cp config/.env.example .env

# Edit .env with your settings
nano .env
```

### 4. Start Ollama Service
```bash
# In a separate terminal
ollama serve

# In another terminal, pull a model
ollama pull tinyllama
```

### 5. Run the Application
```bash
# Development mode with auto-reload
uv run src/main.py

# Or with uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify Setup
```bash
# Test the API
curl http://localhost:8000/api/health

# Visit the UI
open http://localhost:8000
```

---

## Making Changes

### Branch Naming Conventions

Use descriptive branch names following this pattern:
```
feature/short-description      # New features
fix/short-description          # Bug fixes
docs/short-description         # Documentation updates
test/short-description         # Test additions
refactor/short-description     # Code refactoring
chore/short-description        # Maintenance tasks
```

### Examples
```bash
git checkout -b feature/add-conversation-history
git checkout -b fix/handle-timeout-gracefully
git checkout -b docs/improve-api-documentation
git checkout -b test/add-streaming-tests
```

### Code Style Guidelines

**Type Hints**
- All functions must have complete type hints
- Use `Optional[T]` instead of `T | None` for compatibility
- Document complex types in docstrings

**Docstrings**
- Follow Google-style docstrings
- Include: description, Args, Returns, Raises, Examples
- Document edge cases and assumptions

Example:
```python
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Process a chat message and stream the response.

    Args:
        request: ChatRequest containing user message

    Returns:
        StreamingResponse with token-by-token output

    Raises:
        HTTPException: 400 if message invalid, 503 if Ollama unavailable

    Examples:
        >>> response = await chat(ChatRequest(message="Hello"))
        >>> async for token in response.body_iterator:
        >>>     print(token, end='')
    """
```

**Naming Conventions**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private variables: `_leading_underscore`
- No single-letter variables except loops

**File Organization**
- Keep functions under 50 lines when possible
- One responsibility per function
- Group related functions together
- Maximum file size: 500 lines (consider refactoring beyond this)

---

## Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html -v

# Run specific test file
pytest tests/test_chat_api.py::TestChatEndpoint -v

# Run with output
pytest tests/ -s
```

### Writing Tests

**Test File Structure**
```python
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.main import app, validate_message

class TestFeatureName:
    """Test suite for feature_name function."""

    @pytest.fixture
    def client(self):
        """Provide test client."""
        return TestClient(app)

    def test_happy_path(self, client):
        """Test normal operation."""
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 200

    def test_edge_case(self):
        """Test boundary condition."""
        with pytest.raises(ValueError):
            validate_message("")
```

**Coverage Requirements**
- Minimum 70% code coverage (target: 85%+)
- All error paths must be tested
- Edge cases should be documented
- Add tests before committing

### Running Locally
```bash
# Full test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Check coverage is above 70%
coverage report
```

---

## Commit Guidelines

### Commit Message Format

Use clear, descriptive commit messages following this format:

```
[type]: Brief description (50 chars max)

Longer explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

Fixes #123
Related #456
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/updates
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Build, CI/CD, or dependency updates

### Examples
```
feat: Add conversation history persistence with SQLite

Implements in-memory SQLite database to store chat conversations.
Users can now retrieve conversation history across sessions.

Fixes #42
```

```
fix: Handle Ollama timeout gracefully with 503 response

Previously, requests timing out would cause internal errors.
Now returns proper 503 Service Unavailable with user-friendly message.

Fixes #38
```

### Commit Best Practices
- ✅ Make one logical change per commit
- ✅ Write meaningful commit messages
- ✅ Keep commits atomic and reversible
- ✅ Reference related issues/PRs
- ❌ Don't mix formatting and logic changes
- ❌ Don't commit unrelated changes

---

## Pull Request Process

### Before Submitting
1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests locally**
   ```bash
   pytest tests/ -v --cov=src
   ```

3. **Check code style**
   ```bash
   # Install linting tools
   pip install black flake8 mypy

   # Format code
   black src/ tests/

   # Check for issues
   flake8 src/ tests/
   mypy src/
   ```

### PR Description Template
```markdown
## Description
Brief description of changes.

## Related Issue
Fixes #123

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Performance improvement

## Testing
Describe testing performed:
- [ ] Unit tests added
- [ ] All tests passing
- [ ] Tested locally
- [ ] Coverage maintained (70%+)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass and coverage maintained
```

### Review Process
1. Submit PR with complete description
2. Address reviewer feedback promptly
3. Re-request review after updates
4. PR will be merged after approval

---

## Reporting Issues

### Bug Reports
Use the bug report template when creating issues:

```markdown
## Description
Clear description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: macOS/Linux/Windows
- Python: 3.11.x
- Ollama version: x.x.x
- Model: tinyllama/llama2/etc

## Additional Context
Screenshots, logs, etc.
```

### Feature Requests
```markdown
## Description
Clear description of desired feature.

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternative Solutions
Other approaches considered.
```

---

## Project Structure

```
ollama-chat/
├── src/
│   └── main.py              # Core application (823 lines)
├── app/
│   ├── main.py              # Original implementation
│   └── templates/
│       └── index.html       # Web UI
├── tests/
│   └── test_chat_api.py     # Test suite (31+ tests)
├── docs/
│   ├── PRD.md               # Product requirements
│   ├── ARCHITECTURE.md      # System design
│   ├── RESEARCH_ANALYSIS.md # Parameter analysis
│   └── DEPLOYMENT.md        # Deployment guide
├── config/
│   └── .env.example         # Configuration template
├── README.md                # Main documentation
├── CONTRIBUTING.md          # This file
├── CHANGELOG.md             # Version history
├── PROMPTS.md               # Development log
├── requirements.txt         # Dependencies
└── Dockerfile               # Docker support
```

### Key Files
- **src/main.py**: Core FastAPI application with all endpoints
- **app/templates/index.html**: Frontend UI served by FastAPI
- **tests/test_chat_api.py**: 31+ test cases covering all functionality
- **docs/ARCHITECTURE.md**: C4 Model and architectural decisions

---

## Development Roadmap

### v1.0 (Current)
- ✅ Basic chat interface
- ✅ TinyLLaMA integration
- ✅ Streaming responses
- ✅ Health monitoring

### v2.0 (Planned)
- [ ] Conversation history (SQLite)
- [ ] User authentication
- [ ] Multi-model support
- [ ] Rate limiting
- [ ] Docker deployment

### v3.0 (Future)
- [ ] Voice input/output
- [ ] Custom system prompts
- [ ] Model fine-tuning
- [ ] Advanced analytics

---

## Getting Help

- **Documentation**: See [README.md](README.md) and [docs/](docs/)
- **Issues**: Search existing issues or create new one
- **Architecture**: Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Docs**: Run application and visit `/docs` (Swagger UI)

---

## Recognition

Contributors will be recognized in:
- [CHANGELOG.md](CHANGELOG.md) for each release
- Project README in contributors section
- Commit history

Thank you for contributing! 🙏

---

**Last Updated**: November 2025
**Maintained by**: Tal & Keren
