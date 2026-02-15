# Mistral Vibe: Current Features

**Version:** 2.1.0
**Last Updated:** February 13, 2026

This document provides a comprehensive overview of Mistral Vibe's current capabilities. It serves as a reference for understanding what the product can do today.

---

## 1. Core Product Description

Mistral Vibe is an open-source command-line coding assistant powered by Mistral's AI models. It provides developers with an AI pair programmer that:

- Interacts with codebases using natural language
- Executes commands and manipulates files through a powerful toolset
- Supports both CLI (Terminal UI) and IDE integration (via Agent Client Protocol)
- Offers extensibility through agents, tools, skills, and MCP servers
- Maintains session history and provides conversation continuity

**Key Differentiators:**
- Built specifically for Mistral AI models (Devstral, Mistral Large, etc.)
- Rich terminal-based UI using Textual framework
- Production-ready with session logging, safety features, and enterprise considerations
- Extensible architecture supporting custom tools, agents, and skills

---

## 2. CLI Interface and Commands

### 2.1 Command-Line Arguments

**Basic Usage:**
```bash
# Start interactive session
vibe

# Start with initial prompt
vibe "Explain the architecture of this project"
```

**Session Management:**
```bash
# Resume most recent session
vibe --continue
vibe -c

# Resume specific session
vibe --resume abc123
```

**Agent Selection:**
```bash
# Choose agent profile
vibe --agent plan          # Read-only exploration agent
vibe --agent accept-edits  # Auto-approve file edits
vibe --agent auto-approve  # Auto-approve all tools
```

**Programmatic Mode:**
```bash
# Non-interactive execution with auto-approve
vibe --prompt "List all Python files" --max-turns 5 --output json

# Set cost limit
vibe --max-price 0.50

# Filter available tools
vibe --enabled-tools "read_file,grep,bash"
```

**Other Options:**
```bash
# Configure API keys
vibe --setup

# Set working directory
vibe --workdir /path/to/project
```

### 2.2 Slash Commands

Built-in commands available during interactive sessions:

| Command | Description |
|---------|-------------|
| `/help` | Display available commands |
| `/status` | Show agent statistics (tokens, cost, steps) |
| `/config` | Open in-app configuration editor |
| `/clear` | Clear conversation history |
| `/exit` | Exit the application |
| `/reload` | Reload configuration from disk |
| `/log` | Display current session log path |
| `/compact` | Manually compact conversation history |
| `/setup-terminal` | Configure terminal keybindings |
| `/teleport` | Teleport session to Vibe Nuage (if enabled) |

**Custom Slash Commands:**
- User-invocable skills automatically appear as slash commands
- Example: `/code-review` (if you create a code-review skill)

### 2.3 Special Input Prefixes

```bash
# Execute shell command directly (bypasses agent)
!ls -la

# File path autocompletion
@src/main.py

# Teleport command (if Nuage enabled)
&analyze this codebase
```

### 2.4 Key Bindings

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` / `Ctrl+D` | Quit application |
| `Escape` | Interrupt agent / Clear input (double-tap) |
| `Ctrl+O` | Toggle tool output visibility |
| `Ctrl+Y` / `Ctrl+Shift+C` | Copy selection to clipboard |
| `Shift+Tab` | Cycle agent mode (toggle auto-approve) |
| `Shift+Up/Down` | Scroll chat history |
| `Ctrl+J` / `Shift+Enter` | Insert newline (terminal-dependent) |
| `Ctrl+G` | Open external editor for input |

---

## 3. UI Components and Capabilities

### 3.1 Terminal User Interface

Built on the Textual framework, providing a rich terminal experience with:

**Main Components:**
- **Chat Area** - Scrollable conversation history with syntax highlighting
- **Input Area** - Multi-line input with autocompletion
- **Status Bar** - Current working directory and token usage
- **Loading Indicators** - Animated spinners with status messages
- **Context Progress** - Visual token usage bar

### 3.2 Message Types

The UI displays different message types with distinct styling:

- **UserMessage** - User input display
- **AssistantMessage** - AI responses with streaming support
- **ReasoningMessage** - Model's internal reasoning/thinking process
- **ToolCallMessage** - Tool execution display with arguments
- **ToolResultMessage** - Tool execution results and errors
- **ErrorMessage** / **WarningMessage** - Error and warning display
- **CompactMessage** - Compaction status and statistics
- **WhatsNewMessage** - Version update notifications

### 3.3 Interactive Features

**Tool Approval System:**
- Interactive UI for approving tool execution
- Shows tool name, arguments, and description
- Options: Approve once, Approve always, Reject
- Supports saving "always" permission permanently

**Question System:**
- Multi-question tabbed interface
- Support for 2-4 options per question
- Automatic "Other" option for free-text input
- Used by `ask_user_question` tool

**Configuration Editor:**
- In-app TOML editor
- Real-time validation
- Saves changes directly to config file

### 3.4 Chat Input Features

- **Multi-line input** - Supports complex prompts
- **Path autocompletion** - Type `@` prefix to trigger file path suggestions
- **Slash command autocompletion** - Type `/` to see available commands
- **Skill suggestions** - Autocomplete for user-invocable skills
- **External editor** - Press `Ctrl+G` to edit in your preferred editor

### 3.5 Performance Optimizations

The UI includes several optimizations for smooth performance:

1. **Custom ChatScroll** - Skips unnecessary style recalculations
2. **Cached DOM Queries** - Pre-cached widget references
3. **Batch Updates** - Groups widget mutations to reduce reflows
4. **Message Pruning** - Auto-removes old messages when exceeding thresholds (1000-1500 lines)
5. **Windowed History** - Loads history in batches (20 messages) with "Load more" button
6. **Efficient Streaming** - Optimized content appending for streaming responses

---

## 4. LLM Integration

### 4.1 Supported Backends

**Mistral Backend** (Primary)
- Uses official Mistral AI SDK (v1.9.11)
- Native tool calling support
- Streaming completion
- Reasoning content extraction
- Session affinity (x-affinity header)
- Prompt caching awareness
- Supports all Mistral models: devstral-2, devstral-small, mistral-large-latest, etc.

**Generic Backend** (OpenAI-compatible)
- Compatible with OpenAI API format
- Works with: llama.cpp, Ollama, and other OpenAI-compatible servers
- Standard tool calling support
- Streaming support
- Configurable via provider settings

### 4.2 Model Configuration

Models are configured in `config.toml`:

```toml
[[models]]
name = "mistral-vibe-cli-latest"
provider = "mistral"
alias = "devstral-2"
temperature = 0.2
input_price = 0.4
output_price = 2.0
```

### 4.3 Message Flow

1. User input → LLMMessage (role=user)
2. Backend processes → complete() or complete_streaming()
3. Response parsed → LLMMessage (role=assistant, tool_calls=[...])
4. Tool calls resolved and executed
5. Tool results → LLMMessage (role=tool)
6. Loop continues until no tool calls remain

### 4.4 Streaming Support

- **Batched Streaming** - Groups chunks (default: 5 chunks) before yielding for smooth UI updates
- **Separate Reasoning** - Handles reasoning content separately from regular content
- **Adaptive Rendering** - UI appends content efficiently without full re-renders

---

## 5. Configuration System

### 5.1 Configuration Sources (Priority Order)

1. **Init settings** - Programmatic overrides
2. **Environment variables** - `VIBE_*` prefixed
3. **TOML file** - `config.toml`
4. **File secrets** - Pydantic settings default

### 5.2 Configuration File Locations

- **Primary:** `.vibe/config.toml` (project-local)
- **Fallback:** `~/.vibe/config.toml` (global)
- **Custom:** `$VIBE_HOME/config.toml` (if VIBE_HOME set)

### 5.3 Key Configuration Sections

**Models Configuration:**
```toml
[[models]]
name = "mistral-vibe-cli-latest"
provider = "mistral"
alias = "devstral-2"
temperature = 0.2
input_price = 0.4
output_price = 2.0
```

**Provider Configuration:**
```toml
[[providers]]
name = "mistral"
api_base = "https://api.mistral.ai/v1"
api_key_env_var = "MISTRAL_API_KEY"
backend = "mistral"
```

**Tool Configuration:**
```toml
[tools.bash]
permission = "ask"  # always | never | ask
allowlist = ["git *", "ls *"]
denylist = ["rm -rf *"]
```

**Session Logging:**
```toml
[session_logging]
enabled = true
save_dir = "~/.vibe/logs"
session_prefix = "session"
```

**Project Context:**
```toml
[project_context]
max_chars = 40000
max_files = 1000
max_depth = 3
timeout_seconds = 2.0
```

### 5.4 Environment Variables

**API Keys** (`~/.vibe/.env`):
```bash
MISTRAL_API_KEY=your_key_here
```

**Vibe Settings** (override config):
```bash
VIBE_ACTIVE_MODEL=devstral-2
VIBE_AUTO_APPROVE=true
VIBE_ENABLE_AUTO_UPDATE=false
```

**Special Variables:**
- `VIBE_HOME` - Custom Vibe home directory
- `DEBUG_MODE=true` - Enable debugpy for ACP mode

---

## 6. Onboarding Flow

### 6.1 Steps

1. **Welcome Screen**
   - Display Mistral Vibe branding
   - Introduction to features
   - Navigation to next step

2. **API Key Setup**
   - Prompt for Mistral API key
   - Validate key format
   - Save to `~/.vibe/.env`
   - Optional secure storage using keyring

3. **Configuration Creation**
   - Generate default `config.toml`
   - Discover and configure default tools
   - Create history file

### 6.2 Trigger Conditions

- First run (no config file exists)
- `--setup` flag provided
- Missing API key when required

---

## 7. Session Management

### 7.1 Session Logger

**Capabilities:**
- Create session directories with timestamps
- Log all messages to JSONL format
- Track session metadata (git status, environment, stats)
- Support session resumption

**Session Directory Structure:**
```
~/.vibe/logs/
└── session_20260213_143022_abc12345/
    ├── meta.json       # Session metadata
    └── messages.jsonl  # Message history (one per line)
```

**Metadata Tracked:**
- Session ID
- Start and end times
- Git commit and branch
- Username
- Working directory
- Environment details

### 7.2 Session Loader

**Features:**
- Load session by ID (supports partial matching)
- Find most recent session
- Validate session integrity
- Restore messages and metadata

### 7.3 Session Continuation

**CLI Options:**
```bash
# Resume last session
vibe --continue

# Resume specific session (partial ID match)
vibe --resume abc123
```

**Behavior:**
- Loads message history
- Restores agent configuration
- Maintains session stats
- Displays "Load more" for long histories

### 7.4 Session Migration

Runs in background thread on startup to update old session formats to new schema. Non-blocking operation that handles schema version changes.

---

## 8. Tool/Function Calling System

### 8.1 Tool System Architecture

**Base Tool Structure:**
- Generic tool class supporting typed arguments and results
- Pydantic-based argument validation
- Configuration support per tool
- Stateful tool execution
- Streaming support via async generators

**Tool Configuration Options:**
- `permission` - ALWAYS | NEVER | ASK (default: ASK)
- `allowlist` - Pattern-based auto-approval
- `denylist` - Pattern-based auto-rejection
- Per-tool config in `config.toml`

**Invoke Context:**
- Tool call ID
- Approval callback
- Agent manager reference
- User input callback

### 8.2 Tool Manager

**Responsibilities:**
- Discover tools from multiple sources
- Apply enabled/disabled patterns
- Cache tool instances
- Manage tool permissions
- Provide tool metadata to LLM

**Discovery Order:**
1. Custom tool paths (from config)
2. Project-local tools (`.vibe/tools/`)
3. Global tools (`~/.vibe/tools/`)
4. Built-in tools
5. MCP server tools

**Pattern Matching Support:**
- Exact names: `"bash"`
- Glob patterns: `"mcp_*"`, `"serena_*"`
- Regex: `"re:^serena_.*$"`

---

## 9. Built-in Tools

### 9.1 Bash Tool

**Description:** Execute shell commands in a stateful terminal

**Features:**
- Persistent shell session (uses `pexpect`)
- Maintains environment variables and cwd across calls
- Captures stdout/stderr
- Exit code reporting
- Timeout support (default: 2 minutes)
- Windows support (uses PowerShell on Windows)

**Example:**
```python
bash(command="git status && git diff")
```

**Safety:** Includes prompt with instructions for safe usage

---

### 9.2 Read File

**Description:** Read file contents with optional line range

**Features:**
- Absolute path enforcement
- Line offset and limit for large files
- UTF-8 encoding with error handling
- Line-numbered output (cat -n format)
- Truncation of very long lines (2000 chars)

**Example:**
```python
read_file(path="/path/to/file.py", offset=10, limit=50)
```

---

### 9.3 Write File

**Description:** Create or overwrite files

**Features:**
- Automatic parent directory creation
- UTF-8 encoding
- Backup prevention (no .bak files)
- Path expansion (~ support)

**Example:**
```python
write_file(path="/path/to/new.py", content="print('hello')")
```

---

### 9.4 Search & Replace

**Description:** Perform precise text replacements in files

**Features:**
- Exact string matching (not regex)
- Single-occurrence safety check (prevents ambiguous replacements)
- `replace_all=true` for multiple replacements
- Preserves file encoding
- Returns before/after context

**Example:**
```python
search_replace(
    path="/path/to/file.py",
    old_str="def old_name():",
    new_str="def new_name():",
    replace_all=false
)
```

**Result:**
```python
class SearchReplaceResult:
    success: bool
    message: str
    occurrences: int
```

---

### 9.5 Grep

**Description:** Search for patterns in files (powered by ripgrep)

**Features:**
- Regex pattern matching
- File type filtering (`-t py`, `-t js`)
- Glob filtering (`*.py`, `**/*.tsx`)
- Context lines (`-A`, `-B`, `-C`)
- Case-insensitive search (`-i`)
- Multiple output modes:
  - `content` - Matching lines with line numbers
  - `files_with_matches` - File paths only
  - `count` - Match counts per file
- Head/offset support for pagination
- Multiline matching support

**Example:**
```python
grep(
    pattern=r"class \w+:",
    path=".",
    type="py",
    output_mode="content",
    head_limit=100
)
```

---

### 9.6 Task Tool

**Description:** Delegate work to subagents

**Features:**
- Spawn independent agent sessions
- Parallel task execution
- Task-specific agent profiles
- Isolated context (prevents main session bloat)
- Built-in `explore` subagent for codebase analysis

**Example:**
```python
task(
    task="Analyze the architecture and create a diagram",
    agent="explore"
)
```

**Subagent Types:**
- `explore` - Read-only, auto-approves safe tools
- Custom subagents via `agent_type = "subagent"` in config

---

### 9.7 Todo Tool

**Description:** Manage task list for tracking work

**Features:**
- Add/remove/list tasks
- Per-session task state
- Helps agent organize complex work

**Example:**
```python
todo(action="add", task="Refactor authentication module")
todo(action="list")
todo(action="remove", task_id=1)
```

---

### 9.8 Ask User Question

**Description:** Interactively gather user input during execution

**Features:**
- Multiple questions in tabs
- 2-4 options per question
- Automatic "Other" option for free text
- Header and description support
- Cancellation support

**Example:**
```python
ask_user_question(
    questions=[{
        "question": "What's the priority?",
        "header": "Priority",
        "options": [
            {"label": "High", "description": "Critical bug"},
            {"label": "Medium", "description": "Important feature"},
            {"label": "Low", "description": "Nice to have"}
        ]
    }]
)
```

**Result:**
```python
class AskUserQuestionResult:
    answers: list[Answer]
    cancelled: bool

class Answer:
    answer: str  # Selected option label or free text
```

---

## 10. MCP (Model Context Protocol) Integration

### 10.1 Overview

MCP allows Vibe to connect to external tool servers, extending capabilities without modifying core code.

### 10.2 Supported Transports

**1. HTTP** (`transport = "http"`)
- Standard HTTP connection
- Custom headers support
- API key authentication

**2. Streamable HTTP** (`transport = "streamable-http"`)
- HTTP with streaming support
- Same features as HTTP

**3. STDIO** (`transport = "stdio"`)
- Launch subprocess
- Communicate via stdin/stdout
- Environment variable support

### 10.3 Configuration Examples

**HTTP Server:**
```toml
[[mcp_servers]]
name = "my_http_server"
transport = "http"
url = "http://localhost:8000"
headers = { "Authorization" = "Bearer token" }
api_key_env = "MY_API_KEY"
api_key_header = "Authorization"
api_key_format = "Bearer {token}"
startup_timeout_sec = 10
tool_timeout_sec = 60
```

**STDIO Server:**
```toml
[[mcp_servers]]
name = "fetch_server"
transport = "stdio"
command = "uvx"
args = ["mcp-server-fetch"]
env = { "DEBUG" = "1" }
```

### 10.4 Tool Naming

MCP tools are prefixed with server name:
- Server: `fetch_server`
- Tool: `get`
- Full name: `fetch_server_get`

### 10.5 Lifecycle Management

- **Startup:** Connect on first tool access
- **Timeout:** Configurable startup and execution timeouts
- **Cleanup:** Auto-disconnect on shutdown
- **Error Handling:** Graceful fallback on server failures

---

## 11. Agent System

### 11.1 Agent Architecture

**Agent Manager:**
- Manages multiple agent profiles
- Switches between agents dynamically
- Merges agent-specific config with base config
- Supports agent cycling (Shift+Tab)

**Agent Profile Components:**
- Name and display name
- System prompt ID
- Auto-approve settings
- Enabled/disabled tools
- Tool-specific configurations
- Agent type (MAIN | SUBAGENT)
- Safety level (UNSAFE | SAFE)

### 11.2 Built-in Agents

**1. Default Agent**
- **Safety:** UNSAFE (asks for approval)
- **Auto-approve:** False
- **Use Case:** General-purpose coding assistant
- **Behavior:** Requires approval for all tools

**2. Plan Agent**
- **Safety:** SAFE (read-only)
- **Auto-approve:** True for safe tools
- **Tools:** Auto-approves `grep`, `read_file`
- **Use Case:** Codebase exploration and planning
- **Behavior:** Cannot modify files or execute commands

**3. Accept-Edits Agent**
- **Safety:** UNSAFE
- **Auto-approve:** True for edit tools
- **Tools:** Auto-approves `write_file`, `search_replace`
- **Use Case:** Batch refactoring
- **Behavior:** Asks for approval for bash, auto-approves edits

**4. Auto-Approve Agent**
- **Safety:** UNSAFE
- **Auto-approve:** True
- **Use Case:** Trusted automation, CI/CD
- **Behavior:** Auto-approves all tools

**5. Explore Subagent**
- **Type:** SUBAGENT
- **Safety:** SAFE
- **Use Case:** Internal delegation for codebase analysis
- **Behavior:** Read-only, used by `task` tool

### 11.3 Custom Agents

**Location:** `~/.vibe/agents/my_agent.toml`

**Example:**
```toml
# Custom red-teaming agent
active_model = "devstral-2"
system_prompt_id = "redteam"
auto_approve = false

disabled_tools = ["write_file", "search_replace"]

[tools.bash]
permission = "always"

[tools.read_file]
permission = "always"
```

**Usage:**
```bash
vibe --agent my_agent
```

### 11.4 Agent Discovery

**Search Paths:**
1. Custom paths from `agent_paths` config
2. Project-local: `.vibe/agents/`
3. Global: `~/.vibe/agents/`

**Filtering:**
- `enabled_agents` - Allowlist patterns
- `disabled_agents` - Blocklist patterns

---

## 12. Skills System

### 12.1 Overview

Skills extend Vibe functionality through reusable components that can:
- Add custom slash commands
- Provide specialized system prompts
- Restrict tool access
- Package domain-specific knowledge

### 12.2 Skill Format

**File Structure:**
```
~/.vibe/skills/code-review/
└── SKILL.md
```

**SKILL.md Format:**
```markdown
---
name: code-review
description: Perform automated code reviews
license: MIT
compatibility: Python 3.12+
user-invocable: true
allowed-tools:
  - read_file
  - grep
  - ask_user_question
---

# Code Review Skill

This skill helps analyze code quality and suggest improvements.

[Detailed instructions for the AI agent...]
```

### 12.3 Metadata Fields

- `name` - Skill identifier
- `description` - Brief description
- `license` - License type (optional)
- `compatibility` - Compatibility notes (optional)
- `user_invocable` - If true, creates slash command (default: false)
- `allowed_tools` - Restricted tool list (optional)

### 12.4 User-Invocable Skills

When `user-invocable: true`, the skill appears as a slash command:

```bash
/code-review
```

**Behavior:**
- Skill content is loaded
- Injected as user message
- Agent acts according to skill instructions
- Tool restrictions applied if specified

### 12.5 Skill Discovery

**Search Paths:**
1. Custom paths from `skill_paths` config
2. Project-local: `.vibe/skills/`
3. Global: `~/.vibe/skills/`

**Filtering:**
- `enabled_skills` - Allowlist patterns
- `disabled_skills` - Blocklist patterns

---

## 13. File Handling and Autocompletion

### 13.1 File Indexer

**Features:**
- Watches filesystem for changes (using `watchfiles` library)
- Builds index of all files in project
- Respects `.gitignore` patterns
- Incremental updates
- LRU cache for performance

### 13.2 Path Completer

**Features:**
- Fuzzy matching on file paths
- Recursive directory traversal
- Smart filtering (ignores binaries, .git, etc.)
- Ranked by relevance

**Usage:**
```
> Read the file @src/ma[TAB]
> Read the file @src/main.py
```

### 13.3 File Operations Safety

**Read Protection:**
- Absolute paths only (prevents directory traversal)
- Line limits (prevent OOM on huge files)
- Binary file detection
- Encoding error handling

**Write Protection:**
- Parent directory auto-creation
- Atomic writes (via temp file + rename)
- No overwrite of critical files (.git/, etc.)

**Search & Replace Safety:**
- Uniqueness check (fails if old_string appears multiple times)
- `replace_all` flag for intentional mass replacement
- Dry-run capability (returns occurrences without changing)

---

## 14. Error Handling

### 14.1 Exception Hierarchy

**Core Exceptions:**
- `AgentLoopError` - General agent loop errors
- `AgentLoopStateError` - Invalid state errors
- `AgentLoopLLMResponseError` - LLM response errors
- `TeleportError` - Teleport-related errors
- `ToolError` - Tool execution errors
- `ToolPermissionError` - Permission denied errors
- `MissingAPIKeyError` - Missing API key
- `MissingPromptFileError` - Missing prompt file
- `WrongBackendError` - Backend mismatch
- `BackendError` - General backend errors
- `RateLimitError` - Rate limit exceeded

### 14.2 Error Handling Patterns

**Tool Execution:**
- Errors logged to LLM as tool error messages
- Displayed in UI as ErrorMessage widget
- Agent can retry or abort
- Permission errors skip tool execution with feedback to agent

**LLM Errors:**
- HTTP 429 → RateLimitError
- Other errors → RuntimeError with details

**User-Facing Errors:**
- Displayed as `ErrorMessage` widget in UI
- Logged to session if enabled
- Can be collapsed (Ctrl+O)
- Agent receives error in next turn

**Cancellation Handling:**
- Graceful shutdown on asyncio.CancelledError
- Cleanup loading widgets
- Display InterruptMessage
- Agent loop stopped cleanly

---

## 15. Testing Infrastructure

### 15.1 Testing Stack

**Frameworks:**
- `pytest` (8.3.5+) - Test runner
- `pytest-asyncio` - Async test support
- `pytest-timeout` - Test timeout enforcement (10 seconds)
- `pytest-xdist` - Parallel test execution
- `pytest-textual-snapshot` - UI snapshot testing

**Mocking:**
- `respx` - HTTP mocking for API tests
- Custom mock factories in `tests/mock/`

### 15.2 Test Categories

**Unit Tests:**
- Tool argument validation
- Configuration parsing
- Message formatting
- Path resolution

**Integration Tests:**
- Agent loop with mock backend
- Tool execution end-to-end
- Session save/load
- MCP server integration

**UI Tests:**
- Textual snapshot tests
- Widget rendering
- Event handling
- Keyboard interactions

### 15.3 Test Organization

```
tests/
├── acp/                    # ACP protocol tests
├── autocompletion/         # Autocompletion tests
├── backend/                # LLM backend tests
├── cli/                    # CLI-specific tests
├── core/                   # Core functionality tests
├── mock/                   # Mock factories and utilities
├── onboarding/             # Onboarding flow tests
├── session/                # Session management tests
├── skills/                 # Skills system tests
├── snapshots/              # UI snapshot tests
├── stubs/                  # Test stubs
└── tools/                  # Tool tests
```

---

## 16. Middleware Pipeline

### 16.1 Architecture

The middleware pipeline runs before and after each conversation turn, allowing for:
- Turn and cost limits
- Auto-compaction
- Context warnings
- Agent suggestions

### 16.2 Built-in Middleware

**1. TurnLimitMiddleware**
- Enforces maximum number of turns
- Stops agent when limit reached
- Configurable via `--max-turns`

**2. PriceLimitMiddleware**
- Enforces maximum cost limit
- Stops agent when cost exceeded
- Configurable via `--max-price`

**3. AutoCompactMiddleware**
- Automatically compacts conversation history
- Triggers when token count exceeds threshold
- Preserves important context

**4. ContextWarningMiddleware**
- Warns when approaching token limit
- Configurable warning fraction (e.g., 50%)
- Injects warning messages to UI

**5. PlanAgentMiddleware**
- Suggests switching to plan mode
- Triggers on exploration-heavy tasks
- Helps users discover plan agent

---

## 17. Streaming Architecture

### 17.1 Streaming Flow

**Batched Streaming:**
- Groups chunks (default: 5) before yielding
- Separate handling for reasoning vs. regular content
- Smooth UI updates without flicker

**Buffer Management:**
- `content_buffer` - Regular assistant content
- `reasoning_buffer` - Model reasoning/thinking
- Automatic flushing when switching content types

### 17.2 UI Streaming Handling

**Efficient Rendering:**
- Appends to existing AssistantMessage widget
- No full re-renders during streaming
- Smooth scrolling as content arrives
- Syntax highlighting applied progressively

---

## 18. Extension Points

Mistral Vibe provides multiple extension points for customization:

### 18.1 Custom Tools

**How to Create:**
1. Define tool class in `~/.vibe/tools/my_tool.py`
2. Extend `BaseTool` with typed arguments and results
3. Configure in `config.toml`

**Capabilities:**
- Pydantic-based argument validation
- Stateful execution
- Streaming support
- Custom permissions and configuration

### 18.2 Custom Agents

**How to Create:**
1. Create agent config in `~/.vibe/agents/my_agent.toml`
2. Create custom system prompt in `~/.vibe/prompts/`
3. Configure tool permissions and model settings

**Usage:**
```bash
vibe --agent my_agent
```

### 18.3 Custom Skills

**How to Create:**
1. Create skill directory: `~/.vibe/skills/my_skill/`
2. Create `SKILL.md` with YAML frontmatter
3. Set `user-invocable: true` for slash command

**Usage:**
```bash
/my_skill
```

### 18.4 MCP Server Integration

**How to Integrate:**
1. Install MCP server (npm, uvx, etc.)
2. Configure in `config.toml` with transport type
3. Set tool permissions
4. Tools automatically available with server prefix

**Supported Transports:**
- HTTP
- Streamable HTTP
- STDIO

### 18.5 Custom System Prompts

**How to Create:**
1. Create prompt file in `~/.vibe/prompts/my_prompt.md`
2. Reference in agent config: `system_prompt_id = "my_prompt"`

**Usage:**
- Agent loads prompt automatically
- Can include tool instructions
- Markdown formatting supported

---

## 19. System Prompt Generation

### 19.1 Universal System Prompt Builder

The system prompt is dynamically generated from multiple sources:

1. **Base Agent Prompt**
   - Loaded from prompt file (e.g., `cli.md`)
   - Can be customized per agent

2. **Model Information**
   - Active model name and alias
   - Included if `include_model_info: true`

3. **Tool Descriptions**
   - Automatically includes all available tools
   - Includes tool-specific prompts if available

4. **Skills Information**
   - Lists user-invocable skills
   - Shows descriptions for discovery

5. **Project Context**
   - Directory tree (respecting .gitignore)
   - Git information (branch, commit, status)
   - Recent commit history
   - Project documentation (README, etc.)

### 19.2 Project Context Provider

**Capabilities:**
- Generate directory tree
- Extract git information
- Read project documentation
- Provide recent commit history

**Configurable Limits:**
- Max characters: 40,000 (default)
- Max files: 1000
- Max depth: 3
- Timeout: 2.0 seconds

---

## 20. Agent Loop Flow

### 20.1 Initialization

1. Initialize managers (AgentManager, ToolManager, SkillManager)
2. Initialize backend (Mistral or Generic)
3. Build system prompt
4. Create message list with system message
5. Initialize stats tracking
6. Set up middleware pipeline
7. Create SessionLogger

### 20.2 Conversation Turn

1. Add user message to history
2. Run pre-turn middleware (turn limits, price limits, etc.)
3. LLM generates response (streaming or non-streaming)
4. Parse response for tool calls
5. For each tool call:
   - Display tool call in UI
   - Get approval (if required)
   - Execute tool
   - Stream tool output
   - Add tool result to history
6. Run post-turn middleware (auto-compact, warnings, etc.)
7. Loop continues if tool calls present, otherwise complete

### 20.3 Middleware Execution

**Before Turn:**
- Check turn limit
- Check price limit
- Run custom middleware

**After Turn:**
- Check auto-compact threshold
- Display context warnings
- Suggest agent mode changes
- Run custom middleware

---

## 21. ACP (Agent Client Protocol) Support

### 21.1 Overview

Mistral Vibe includes ACP server support for IDE integration, enabling:
- VS Code extension integration
- JetBrains plugin support
- Neovim integration
- Other IDE plugins

### 21.2 ACP Entry Point

**Command:**
```bash
vibe-acp
```

**Features:**
- Listens on stdio
- Handles ACP messages
- Debug mode support (DEBUG_MODE=true)

### 21.3 ACP Messages

Supported message types:
- `initialize` - Initialize session
- `new_session` - Create new session
- `send_message` - Send user message
- `set_model` - Change active model
- `set_mode` - Change agent mode

---

## 22. Programmatic Mode

### 22.1 Overview

Non-interactive execution mode for automation and CI/CD:

```bash
vibe --prompt "List all Python files" --max-turns 5 --output json
```

### 22.2 Features

- **Auto-approve:** Automatically approves all tool calls
- **Output formats:** text, json, streaming
- **Turn limits:** `--max-turns N`
- **Price limits:** `--max-price DOLLARS`
- **Tool filtering:** `--enabled-tools PATTERN`

### 22.3 Output Formats

**Text:**
- Human-readable output
- Suitable for logs and debugging

**JSON:**
- Structured output
- Parseable by scripts
- Includes all events

**Streaming:**
- Real-time event stream
- JSONL format
- One event per line

---

## 23. Git Integration

### 23.1 Capabilities

Git operations are available through the bash tool:
- Status, diff, log
- Commit, push, pull
- Branch management
- Merge operations
- Stash operations

### 23.2 Project Context

Git information automatically included in system prompt:
- Current branch
- Latest commit hash
- Repository status
- Recent commit history

---

## 24. Technology Stack

### 24.1 Core Dependencies

**UI/Terminal:**
- `textual` (1.0.0+) - TUI framework
- `rich` (14.0.0+) - Rich text formatting

**LLM Integration:**
- `mistralai` (1.9.11) - Mistral SDK
- `httpx` (0.28.1+) - HTTP client

**Configuration:**
- `pydantic` (2.12.4+) - Data validation
- `pyyaml` (6.0.0+) - YAML parsing
- `python-dotenv` (1.0.0+) - Environment variables
- `tomli-w` (1.2.0+) - TOML writing

**Process Management:**
- `pexpect` (4.9.0+) - Interactive process control
- `anyio` (4.12.0+) - Async I/O

**Utilities:**
- `watchfiles` (1.1.1+) - Filesystem watching
- `pyperclip` (1.11.0+) - Clipboard integration
- `keyring` (25.6.0+) - Secure credential storage

**Protocols:**
- `mcp` (1.14.0+) - Model Context Protocol
- `agent-client-protocol` (0.8.0) - Agent Client Protocol

### 24.2 Python Version

- **Minimum:** Python 3.12+
- **Recommended:** Python 3.12 or 3.13

---

## 25. Security and Safety Features

### 25.1 Tool Permissions

Three-level permission system:
- `ALWAYS` - Auto-approve (use with caution)
- `NEVER` - Always block
- `ASK` - Prompt user (default)

### 25.2 Allowlist/Denylist

Pattern-based auto-approval and rejection:
```toml
[tools.bash]
permission = "ask"
allowlist = ["git *", "ls *"]
denylist = ["rm -rf *"]
```

### 25.3 Safe Agents

Pre-configured read-only agents:
- **Plan agent** - Only uses grep and read_file
- **Explore subagent** - Read-only operations

### 25.4 Path Safety

- Absolute path enforcement
- Directory traversal prevention
- No modification of critical files (.git/, etc.)

### 25.5 Secret Management

- API keys stored in `~/.vibe/.env`
- Optional keyring integration for secure storage
- Environment variable support

---

## Summary

Mistral Vibe is a production-ready AI coding assistant with:

- **8 built-in tools** for file manipulation, code search, and command execution
- **5 pre-configured agents** for different use cases
- **Extensible architecture** supporting custom tools, agents, skills, and MCP servers
- **Rich terminal UI** built on Textual framework
- **Session management** with full conversation history and resumption
- **Streaming support** for smooth real-time responses
- **Safety features** including tool permissions, allowlists, and read-only agents
- **IDE integration** via Agent Client Protocol
- **Programmatic mode** for automation and CI/CD

The product is designed for professional developers who want an AI assistant that:
- Understands their codebase
- Executes commands safely
- Maintains conversation context
- Extends easily through plugins
- Works in both interactive and automated workflows
