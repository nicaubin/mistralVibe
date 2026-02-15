# Testing and Debugging Guide

This guide covers how to test and debug the mistral-vibe project.

## Prerequisites

- Python 3.12+
- uv package manager
- ripgrep (required for grep tool tests)

### Setup

```bash
# Install all dependencies including dev
uv sync --all-extras

# Install pre-commit hooks (optional but recommended)
uv run pre-commit install
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run tests excluding snapshots (faster for regular testing)
uv run pytest --ignore tests/snapshots

# Run only snapshot tests
uv run pytest tests/snapshots

# Run a specific test file
uv run pytest tests/test_agent_tool_call.py

# Run a specific test function
uv run pytest tests/test_agents.py::TestDeepMerge::test_simple_merge

# Run tests matching a pattern
uv run pytest -k "test_bash"
```

### Debugging Tests

```bash
# Show print statements and captured logs
uv run pytest -s

# Show full diff on assertion failures
uv run pytest -vv

# Drop into debugger on failure
uv run pytest --pdb

# Drop into debugger on first failure, then exit
uv run pytest -x --pdb

# Show captured logs even for passing tests
uv run pytest --log-cli-level=DEBUG
```

### Parallel Execution

Tests run in parallel by default (`-n auto`). To control parallelism:

```bash
# Run with specific number of workers
uv run pytest -n 4

# Run sequentially (useful for debugging)
uv run pytest -n 0
```

### Snapshot Tests

Snapshot tests verify UI appearance. Update snapshots when changes are intentional:

```bash
# Update all snapshots
uv run pytest tests/snapshots --snapshot-update
```

---

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and test configuration
├── acp/                     # Agent Client Protocol tests
├── autocompletion/          # Autocompletion tests
├── backend/                 # Backend/LLM integration tests
├── cli/                     # CLI and UI tests
├── core/                    # Core functionality tests
├── mock/                    # Mock utilities
│   ├── mock_backend_factory.py
│   └── utils.py
├── session/                 # Session management tests
├── skills/                  # Skills system tests
├── snapshots/               # UI snapshot tests
├── stubs/                   # Test stubs/fakes
│   ├── fake_backend.py
│   ├── fake_client.py
│   └── fake_tool.py
├── tools/                   # Tool tests
└── update_notifier/         # Update notification tests
```

---

## Writing Tests

### Test Fixtures

Key fixtures available in all tests (from `conftest.py`):

| Fixture | Description |
|---------|-------------|
| `tmp_working_directory` | Isolated temp directory (auto) |
| `config_dir` | Isolated config directory (auto) |
| `vibe_app` | Test VibeApp instance |
| `agent_loop` | Test AgentLoop instance |
| `vibe_config` | Test VibeConfig instance |

### Using FakeBackend

Mock LLM responses without real API calls:

```python
from tests.stubs.fake_backend import FakeBackend
from tests.mock.utils import mock_llm_chunk

# Single response
backend = FakeBackend(mock_llm_chunk(content="Response"))

# Multiple responses in sequence
backend = FakeBackend([
    mock_llm_chunk(content="First"),
    mock_llm_chunk(content="Second"),
])

# Backend that raises exceptions
backend = FakeBackend(exception_to_raise=ValueError("Test error"))
```

### Async Test Example

```python
import pytest
from tests.stubs.fake_backend import FakeBackend
from tests.mock.utils import mock_llm_chunk
from tests.conftest import build_test_agent_loop

@pytest.mark.asyncio
async def test_agent_processes_response():
    backend = FakeBackend(mock_llm_chunk(content="Hello!"))
    agent_loop = build_test_agent_loop(backend=backend)

    await agent_loop.run_turn("Say hello")

    assert len(agent_loop.messages) > 0
```

### Tool Test Example

```python
from tests.mock.utils import collect_result

@pytest.mark.asyncio
async def test_bash_runs_command(bash):
    result = await collect_result(
        bash.run(BashArgs(command="echo hello"))
    )

    assert result.returncode == 0
    assert result.stdout == "hello\n"
```

---

## Debugging

### Log Files

Application logs are written to `~/.vibe/logs/vibe.log`.

Use the logger in code:

```python
from vibe.core.utils import logger

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

### Session Logging

Enable session logging to capture full conversation history. In `~/.vibe/config.toml`:

```toml
[session_logging]
enabled = true
save_dir = "~/.vibe/logs/session"
session_prefix = "vibe"
```

Session logs include:
- All messages (user, assistant, tool results)
- Tool configurations
- Agent stats (token usage, costs)
- Git commit/branch info

### Debug Mode for ACP

Enable remote debugging with debugpy:

```bash
export DEBUG_MODE=true
uv run vibe-acp
```

This starts debugpy listening on `localhost:5678`. Connect with VS Code:

```json
{
    "name": "Attach to Vibe ACP",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    }
}
```

### Testing CLI

```bash
# Test CLI startup
uv run vibe --help

# Test with programmatic mode
uv run vibe --prompt "echo test" --output text

# Test with specific agent
uv run vibe --agent plan
```

---

## Code Quality

### Linting with Ruff

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Check formatting
uv run ruff format --check .

# Format code
uv run ruff format .
```

### Type Checking with Pyright

```bash
# Run type checking
uv run pyright

# Check specific file
uv run pyright vibe/core/agent_loop.py
```

### Pre-commit Hooks

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff-check --all-files
```

### Spell Checking

```bash
# Check spelling
uv run typos

# Auto-fix typos
uv run typos --write-changes
```

---

## Troubleshooting

### Tests Failing Locally

1. **Ensure dependencies are up to date**:
   ```bash
   uv sync --all-extras
   ```

2. **Ensure ripgrep is installed**:
   ```bash
   # macOS
   brew install ripgrep

   # Ubuntu/Debian
   sudo apt-get install ripgrep

   # Windows
   choco install ripgrep
   ```

3. **Clear pytest cache**:
   ```bash
   rm -rf .pytest_cache
   ```

### Common Issues

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | Run `uv sync --all-extras` |
| Tests timeout | Increase with `--timeout=30` or use `@pytest.mark.timeout(30)` |
| Snapshot tests fail | Review changes, update with `--snapshot-update` if intentional |
| Parallel test conflicts | Run sequentially with `-n 0` |

---

## CI/CD

GitHub Actions runs tests automatically on push and PR to main branch.

**Workflow steps**:
1. Pre-commit checks (all hooks)
2. Unit tests (excluding snapshots)
3. Snapshot tests (with report upload on failure)

See `.github/workflows/ci.yml` for details.
