# Contributing to Ollama Chat Application

Thank you for your interest in contributing! This document outlines how to contribute to this project.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites
- Python 3.11+
- Ollama installed and running
- `uv` package manager
- Git

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ollama-chat.git
cd ollama-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev

# Run tests
pytest tests/ -v --cov=src

# Run linting
pylint src/
mypy src/
```

## Development Guidelines

### Code Standards

1. **Type Hints:** All functions must have complete type annotations
   ```python
   def my_function(param: str) -> Dict[str, Any]:
       """Docstring required."""
       pass
   ```

2. **Documentation:** Every module, function, and class needs docstrings
   ```python
   def process_message(message: str) -> str:
       """
       Process and validate user message.
       
       Args:
           message: Raw message from user
       
       Returns:
           Cleaned message string
       
       Raises:
           ValueError: If message is invalid
       """
   ```

3. **Code Style:** Follow PEP 8
   - Max line length: 100 characters
   - 4-space indentation
   - UPPERCASE_CONSTANTS
   - snake_case functions/variables
   - CamelCase classes

4. **Testing:** Every feature needs tests
   - Unit tests for functions
   - Integration tests for endpoints
   - Edge case coverage
   - Target: 70%+ code coverage

### File Organization

```
src/
├── main.py          # Main application
├── plugins.py       # Plugin system
└── config.py        # Configuration

tests/
├── test_chat_api.py
├── test_plugins.py
└── test_integration.py

docs/
├── README.md
├── ARCHITECTURE.md
└── CONTRIBUTING.md
```

## Making Changes

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number
```

### 2. Make Changes
- Write code following standards above
- Add tests for new features
- Update documentation if needed

### 3. Test Locally
```bash
# Run tests
pytest tests/ -v

# Check code quality
pylint src/
mypy src/

# Check formatting
black --check src/

# Run the app
python src/main.py
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: Add new feature description"
# or
git commit -m "fix: Fix bug with issue #123"
```

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request with:
- Clear title describing the change
- Description of what changed and why
- Link to any related issues
- Screenshots for UI changes

## Pull Request Review

PRs should:
- Have meaningful commit messages
- Include tests for new code
- Update documentation if needed
- Pass all automated checks
- Have clear, descriptive descriptions

Review criteria:
- ✅ Code follows project standards
- ✅ Tests pass and coverage maintained
- ✅ Documentation updated
- ✅ No breaking changes without discussion

## Reporting Issues

Use the Issue template and include:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## Plugin Development

To create a plugin:

```python
from src.plugins import Plugin

class MyPlugin(Plugin):
    def __init__(self, config):
        super().__init__("MyPlugin", config)
    
    def on_startup(self) -> None:
        # Initialize plugin
        pass
    
    def on_shutdown(self) -> None:
        # Cleanup
        pass
```

See `src/plugins.py` for examples.

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add docstrings to all code
- Keep examples up-to-date

## Questions?

- Open an issue for questions
- Check existing issues/discussions
- Email maintainers

## License

By contributing, you agree your code will be licensed under the MIT License.

---

**Thank you for contributing! 🚀**
