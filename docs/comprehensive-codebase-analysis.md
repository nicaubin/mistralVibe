# Mistral Vibe: Comprehensive Codebase Analysis

**Version Analyzed:** 2.1.0
**Analysis Date:** February 13, 2026
**Total Python Files:** 139 (in vibe/ directory)

---

## 1. Project Overview

### What is Mistral Vibe?

Mistral Vibe is an open-source command-line coding assistant powered by Mistral's AI models. It provides a conversational interface to interact with codebases using natural language, equipped with a powerful toolset for file manipulation, code searching, version control, and command execution.

### Core Purpose

- **Interactive Coding Assistant**: Provide developers with an AI pair programmer that understands project context
- **Multi-modal Interface**: Support both CLI (via Textual TUI) and IDE integration (via Agent Client Protocol)
- **Extensible Architecture**: Allow customization through agents, tools, skills, and MCP servers
- **Production-Ready**: Built with safety features, session logging, and enterprise considerations

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
│  ┌──────────────────┐          ┌─────────────────────┐     │
│  │  CLI (Textual)   │          │  ACP (IDE Plugin)   │     │
│  │  - vibe          │          │  - vibe-acp         │     │
│  └──────────────────┘          └─────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      AgentLoop Core                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Message Management & Conversation Flow              │  │
│  │  - Middleware Pipeline (compaction, limits, etc.)    │  │
│  │  - Tool Execution & Approval                         │  │
│  │  - Streaming & Event Handling                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Backend Layer                           │
│  ┌──────────────┐        ┌──────────────────────────────┐  │
│  │   Mistral    │        │   Generic OpenAI-compatible  │  │
│  │   Backend    │        │   Backend (llama.cpp, etc.)  │  │
│  └──────────────┘        └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Tool & Extension System                         │
│  ┌──────────┐  ┌───────┐  ┌──────┐  ┌────────────────┐    │
│  │ Builtin  │  │ MCP   │  │Skills│  │ Custom Tools   │    │
│  │ Tools    │  │Servers│  │      │  │                │    │
│  └──────────┘  └───────┘  └──────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Features

### 2.1 CLI Interface and Commands

**Entry Point:** `vibe/cli/entrypoint.py` → `vibe/cli/cli.py`

#### Command-Line Arguments
- **Basic**: `vibe [PROMPT]` - Start interactive session with optional initial prompt
- **Programmatic Mode**: `--prompt TEXT` - Non-interactive mode with auto-approve
- **Session Management**:
  - `--continue` / `-c` - Resume most recent session
  - `--resume SESSION_ID` - Resume specific session
- **Agent Selection**: `--agent NAME` - Choose agent profile (default, plan, accept-edits, auto-approve)
- **Programmatic Options**:
  - `--max-turns N` - Limit assistant turns
  - `--max-price DOLLARS` - Set cost limit
  - `--enabled-tools TOOL` - Filter tools (glob/regex supported)
  - `--output FORMAT` - text/json/streaming output
- **Setup**: `--setup` - Configure API keys
- **Working Directory**: `--workdir DIR` - Set working directory

#### Slash Commands (Built-in)
**Implementation:** `vibe/cli/commands.py`

The system uses a `CommandRegistry` to manage built-in commands:

- `/help` - Display available commands
- `/status` - Show agent statistics (tokens, cost, steps)
- `/config` - Open configuration editor
- `/clear` - Clear conversation history
- `/exit` - Exit the application
- `/reload` - Reload configuration
- `/log` - Display current session log path
- `/compact` - Manually compact conversation history
- `/setup-terminal` - Configure terminal keybindings
- `/teleport` - (if enabled) Teleport session to Vibe Nuage

**Custom Slash Commands:**
Users can create custom slash commands via the Skills system by setting `user-invocable: true` in skill metadata.

#### Special Input Prefixes
- `!command` - Execute shell command directly (bypasses agent)
- `&prompt` - Teleport command (if Nuage enabled)
- `@path` - File path autocompletion trigger

#### Key Bindings
**File:** `vibe/cli/textual_ui/app.py` - `BINDINGS` class variable

- `Ctrl+C` / `Ctrl+D` - Quit
- `Escape` - Interrupt agent / Clear input (double-tap)
- `Ctrl+O` - Toggle tool output visibility
- `Ctrl+Y` / `Ctrl+Shift+C` - Copy selection to clipboard
- `Shift+Tab` - Cycle agent mode (auto-approve toggle)
- `Shift+Up/Down` - Scroll chat history
- `Ctrl+J` / `Shift+Enter` - Insert newline (terminal-dependent)
- `Ctrl+G` - Open external editor for input

---

### 2.2 UI Components (Textual-based)

**Main App:** `vibe/cli/textual_ui/app.py` - `VibeApp` class

#### Architecture Overview

```
VibeApp (App)
├── ChatScroll (VerticalScroll) [#chat]
│   ├── Banner - Welcome banner with animations
│   └── VerticalGroup [#messages]
│       ├── UserMessage
│       ├── AssistantMessage (streaming support)
│       ├── ReasoningMessage (thinking content)
│       ├── ToolCallMessage
│       ├── ToolResultMessage
│       ├── ErrorMessage
│       ├── CompactMessage
│       └── ...
├── Horizontal [#loading-area]
│   └── LoadingWidget (spinner with status)
├── Static [#bottom-app-container]
│   ├── ChatInputContainer (default)
│   ├── ApprovalApp (tool approval UI)
│   ├── QuestionApp (ask_user_question UI)
│   └── ConfigApp (configuration editor)
└── Horizontal [#bottom-bar]
    ├── PathDisplay - Current working directory
    ├── NoMarkupStatic [#spacer]
    └── ContextProgress - Token usage bar
```

#### Key Widgets

**Chat Input Container** (`vibe/cli/textual_ui/widgets/chat_input/`)
- `ChatInputContainer` - Main input area
- `CompletionManager` - Handles autocompletion logic
- `CompletionPopup` - Displays completion suggestions
- Features:
  - Multi-line input support
  - Path autocompletion with `@` prefix
  - Slash command autocompletion
  - Skill command suggestions
  - External editor integration (Ctrl+G)

**Message Widgets** (`vibe/cli/textual_ui/widgets/messages.py`)
- `UserMessage` - User input display
- `AssistantMessage` - AI responses with streaming
- `ReasoningMessage` - Model's reasoning/thinking process
- `ToolCallMessage` / `ToolResultMessage` - Tool execution display
- `ErrorMessage` / `WarningMessage` - Error/warning display
- `CompactMessage` - Compaction status
- `WhatsNewMessage` - Version update notifications

**Approval System** (`vibe/cli/textual_ui/widgets/approval_app.py`)
- Interactive tool approval UI
- Shows tool name, arguments, and description
- Options: Approve once, Approve always, Reject
- Supports saving "always" permission permanently

**Question System** (`vibe/cli/textual_ui/widgets/question_app.py`)
- Multi-question tabbed interface
- Support for 2-4 options per question
- Automatic "Other" option for free-text input
- Used by `ask_user_question` tool

**Configuration Editor** (`vibe/cli/textual_ui/widgets/config_app.py`)
- In-app TOML editor
- Real-time validation
- Saves changes to config file

#### UI Optimizations

**Performance Features:**
1. **ChatScroll** - Custom scroll container that skips style recalculations
2. **Cached DOM Queries** - Pre-cached widget references for frequently accessed elements
3. **Batch Updates** - Group widget mutations to reduce reflows
4. **Pruning** - Auto-remove old messages when virtual height exceeds thresholds (1000-1500 lines)
5. **Windowing** - Load history in batches (20 messages) with "Load more" button
6. **Streaming Layout** - Efficient content appending for streaming responses

---

### 2.3 LLM Integration

**Location:** `vibe/core/llm/`

#### Backend Architecture

**Factory Pattern** (`vibe/core/llm/backend/factory.py`)
```python
BACKEND_FACTORY = {
    Backend.MISTRAL: MistralBackend,
    Backend.GENERIC: GenericBackend,
}
```

#### Mistral Backend (`vibe/core/llm/backend/mistral.py`)
- **SDK:** Uses official `mistralai` SDK (v1.9.11)
- **Features:**
  - Native tool calling support
  - Streaming completion
  - Reasoning content extraction
  - Session affinity (x-affinity header)
  - Prompt caching awareness
- **Models:** Supports all Mistral models (devstral-2, devstral-small, etc.)

#### Generic Backend (`vibe/core/llm/backend/generic.py`)
- **Protocol:** OpenAI-compatible API
- **Use Cases:** llama.cpp, Ollama, other OpenAI-compatible servers
- **Features:**
  - Standard tool calling
  - Streaming support
  - Configurable via `ProviderConfig`

#### Format Handler (`vibe/core/llm/format.py`)
**Class:** `APIToolFormatHandler`

Responsibilities:
- Convert tool definitions to API format
- Parse LLM responses for tool calls
- Validate tool arguments against Pydantic schemas
- Create tool response messages
- Handle reasoning content extraction

#### Message Flow

```
User Input
    ↓
LLMMessage (role=user, content=prompt)
    ↓
Backend.complete() or Backend.complete_streaming()
    ↓
APIToolFormatHandler.process_api_response_message()
    ↓
LLMMessage (role=assistant, content=..., tool_calls=[...])
    ↓
APIToolFormatHandler.parse_message()
    ↓
APIToolFormatHandler.resolve_tool_calls()
    ↓
Tool Execution
    ↓
LLMMessage (role=tool, content=result, tool_call_id=...)
```

---

### 2.4 Configuration System

**Main Config:** `vibe/core/config.py` - `VibeConfig` class

#### Configuration Sources (Priority Order)
1. **Init settings** - Programmatic overrides
2. **Environment variables** - `VIBE_*` prefixed
3. **TOML file** - `config.toml`
4. **File secrets** - (Pydantic settings default)

#### Configuration File Locations
- **Primary:** `.vibe/config.toml` (project-local)
- **Fallback:** `~/.vibe/config.toml` (global)
- **Custom:** `$VIBE_HOME/config.toml` (if VIBE_HOME set)

#### Key Configuration Sections

**Models Configuration**
```toml
[[models]]
name = "mistral-vibe-cli-latest"
provider = "mistral"
alias = "devstral-2"
temperature = 0.2
input_price = 0.4
output_price = 2.0
```

**Provider Configuration**
```toml
[[providers]]
name = "mistral"
api_base = "https://api.mistral.ai/v1"
api_key_env_var = "MISTRAL_API_KEY"
backend = "mistral"
```

**Tool Configuration**
```toml
[tools.bash]
permission = "ask"  # always | never | ask
allowlist = ["git *", "ls *"]
denylist = ["rm -rf *"]
```

**MCP Server Configuration**
```toml
[[mcp_servers]]
name = "fetch_server"
transport = "stdio"
command = "uvx"
args = ["mcp-server-fetch"]
startup_timeout_sec = 10.0
tool_timeout_sec = 60.0
```

**Session Logging**
```toml
[session_logging]
enabled = true
save_dir = "~/.vibe/logs"
session_prefix = "session"
```

**Project Context**
```toml
[project_context]
max_chars = 40000
max_files = 1000
max_depth = 3
timeout_seconds = 2.0
```

#### Environment Variables

**API Keys** (`~/.vibe/.env`)
```bash
MISTRAL_API_KEY=your_key_here
```

**Vibe Settings** (env vars override config)
```bash
VIBE_ACTIVE_MODEL=devstral-2
VIBE_AUTO_APPROVE=true
VIBE_ENABLE_AUTO_UPDATE=false
```

**Special Variables**
- `VIBE_HOME` - Custom Vibe home directory
- `DEBUG_MODE=true` - Enable debugpy for ACP mode

---

### 2.5 Onboarding Flow

**Location:** `vibe/setup/onboarding/`

#### Flow Steps

1. **Welcome Screen** (`screens/welcome.py`)
   - Display Mistral Vibe branding
   - Introduction to features
   - Navigation to next step

2. **API Key Setup** (`screens/api_key.py`)
   - Prompt for Mistral API key
   - Validate key format
   - Save to `~/.vibe/.env`
   - Secure storage using keyring (optional)

3. **Configuration Creation**
   - Generate default `config.toml`
   - Discover and configure default tools
   - Create history file

#### Trigger Conditions
- First run (no config file exists)
- `--setup` flag provided
- Missing API key when required

**Implementation:** `vibe/setup/onboarding/base.py`

Uses Textual-based UI for interactive screens with keyboard navigation.

---

### 2.6 Session Management

**Location:** `vibe/core/session/`

#### Session Logger (`session_logger.py`)

**Responsibilities:**
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

**Metadata Fields:**
```json
{
  "session_id": "abc123...",
  "start_time": "2026-02-13T14:30:22Z",
  "end_time": "2026-02-13T14:45:10Z",
  "git_commit": "51fecc6...",
  "git_branch": "main",
  "username": "user",
  "environment": {
    "working_directory": "/path/to/project"
  }
}
```

#### Session Loader (`session_loader.py`)

**Features:**
- Load session by ID (supports partial matching)
- Find most recent session
- Validate session integrity
- Restore messages and metadata

#### Session Migration (`session_migration.py`)

**Purpose:** Update old session formats to new schema
- Runs in background thread on startup
- Handles schema version changes
- Non-blocking operation

#### Session Continuation

**CLI Options:**
- `--continue` - Resume last session
- `--resume abc123` - Resume specific session (partial ID match)

**Behavior:**
- Loads message history
- Restores agent configuration
- Maintains session stats
- Displays "Load more" for long histories

---

### 2.7 Tool/Function Calling Capabilities

**Location:** `vibe/core/tools/`

#### Tool System Architecture

**Base Classes** (`base.py`)
```python
class BaseTool[ToolArgs, ToolResult, ToolConfig, ToolState]:
    description: ClassVar[str]
    prompt_path: ClassVar[Path] | None

    async def run(args, ctx) -> AsyncGenerator[ToolStreamEvent | ToolResult]:
        ...

    async def invoke(ctx, **raw) -> AsyncGenerator[...]:
        # Validates args via Pydantic
        # Calls run()
        ...
```

**Tool Configuration:**
- `ToolPermission` - ALWAYS | NEVER | ASK
- `allowlist` / `denylist` - Pattern-based auto-approval/rejection
- Per-tool config in `config.toml`

**Invoke Context:**
```python
@dataclass
class InvokeContext:
    tool_call_id: str
    approval_callback: ApprovalCallback | None
    agent_manager: AgentManager | None
    user_input_callback: UserInputCallback | None
```

#### Tool Manager (`manager.py`)

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

**Pattern Matching:**
Supports:
- Exact names: `"bash"`
- Glob patterns: `"mcp_*"`, `"serena_*"`
- Regex: `"re:^serena_.*$"`

Applied to:
- `enabled_tools` (allowlist mode)
- `disabled_tools` (blocklist mode)

---

### 2.8 Built-in Tools

**Location:** `vibe/core/tools/builtins/`

#### 1. Bash Tool (`bash.py`)
**Description:** Execute shell commands in a stateful terminal

**Features:**
- Persistent shell session (uses `pexpect`)
- Maintains environment variables, cwd across calls
- Captures stdout/stderr
- Exit code reporting
- Timeout support (default 2 minutes)
- Windows support (uses PowerShell on Windows)

**Example:**
```python
bash(command="git status && git diff")
```

**Prompt:** `prompts/bash.md` - Instructions for safe usage

---

#### 2. Read File (`read_file.py`)
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

#### 3. Write File (`write_file.py`)
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

#### 4. Search & Replace (`search_replace.py`)
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

**Result Model:**
```python
class SearchReplaceResult:
    success: bool
    message: str
    occurrences: int
```

---

#### 5. Grep (`grep.py`)
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

#### 6. Task Tool (`task.py`)
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

#### 7. Todo Tool (`todo.py`)
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

#### 8. Ask User Question (`ask_user_question.py`)
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

### 2.9 MCP (Model Context Protocol) Integration

**Location:** `vibe/core/tools/mcp.py`

#### Overview

MCP allows Vibe to connect to external tool servers, extending capabilities without modifying core code.

#### Supported Transports

1. **HTTP** (`transport = "http"`)
   - Standard HTTP connection
   - Custom headers support
   - API key authentication

2. **Streamable HTTP** (`transport = "streamable-http"`)
   - HTTP with streaming support
   - Same features as HTTP

3. **STDIO** (`transport = "stdio"`)
   - Launch subprocess
   - Communicate via stdin/stdout
   - Environment variable support

#### Configuration Examples

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

#### Tool Naming

MCP tools are prefixed with server name:
- Server: `fetch_server`
- Tool: `get`
- Full name: `fetch_server_get`

#### Tool Discovery

**Implementation:** `MCPToolManager` in `mcp.py`

Process:
1. Connect to MCP server
2. List available tools
3. Convert MCP tool schemas to Vibe tool format
4. Register as available tools
5. Apply enabled/disabled filters

#### Lifecycle Management

- **Startup:** Connect on first tool access
- **Timeout:** Configurable startup and execution timeouts
- **Cleanup:** Auto-disconnect on shutdown
- **Error Handling:** Graceful fallback on server failures

---

### 2.10 Agent Capabilities

**Location:** `vibe/core/agents/`

#### Agent System Architecture

**Agent Manager** (`manager.py`)
- Manages multiple agent profiles
- Switches between agents dynamically
- Merges agent-specific config with base config
- Supports agent cycling (Shift+Tab)

**Agent Profile** (`models.py`)
```python
class AgentProfile:
    name: str
    display_name: str
    system_prompt_id: str
    auto_approve: bool
    enabled_tools: list[str]
    disabled_tools: list[str]
    tools_config: dict[str, BaseToolConfig]
    agent_type: AgentType  # MAIN | SUBAGENT
    safety: SafetyLevel  # UNSAFE | SAFE
```

#### Built-in Agents

**1. Default Agent** (`BuiltinAgentName.DEFAULT`)
- **Safety:** UNSAFE (asks for approval)
- **Auto-approve:** False
- **Use Case:** General-purpose coding assistant
- **Behavior:** Requires approval for all tools

**2. Plan Agent** (`BuiltinAgentName.PLAN`)
- **Safety:** SAFE (read-only)
- **Auto-approve:** True for safe tools
- **Tools:** Auto-approves `grep`, `read_file`
- **Use Case:** Codebase exploration and planning
- **Behavior:** Cannot modify files or execute commands

**3. Accept-Edits Agent** (`BuiltinAgentName.ACCEPT_EDITS`)
- **Safety:** UNSAFE
- **Auto-approve:** True for edit tools
- **Tools:** Auto-approves `write_file`, `search_replace`
- **Use Case:** Batch refactoring
- **Behavior:** Asks for approval for bash, auto-approves edits

**4. Auto-Approve Agent** (`BuiltinAgentName.AUTO_APPROVE`)
- **Safety:** UNSAFE
- **Auto-approve:** True
- **Use Case:** Trusted automation, CI/CD
- **Behavior:** Auto-approves all tools

**5. Explore Subagent** (`BuiltinAgentName.EXPLORE`)
- **Type:** SUBAGENT
- **Safety:** SAFE
- **Use Case:** Internal delegation for codebase analysis
- **Behavior:** Read-only, used by `task` tool

#### Custom Agents

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

#### Agent Discovery

**Paths Searched:**
1. Custom paths from `agent_paths` config
2. Project-local: `.vibe/agents/`
3. Global: `~/.vibe/agents/`

**Filtering:**
- `enabled_agents` - Allowlist patterns
- `disabled_agents` - Blocklist patterns

---

### 2.11 Skills System

**Location:** `vibe/core/skills/`

#### Overview

Skills extend Vibe functionality through reusable components that can:
- Add custom slash commands
- Provide specialized system prompts
- Restrict tool access
- Package domain-specific knowledge

#### Skill Format

**Specification:** Follows [Agent Skills specification](https://agentskills.io/specification)

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

#### Metadata Fields

```python
class SkillMetadata:
    name: str
    description: str
    license: str | None
    compatibility: str | None
    user_invocable: bool = False
    allowed_tools: list[str] = []
```

#### Skill Discovery

**Skill Manager** (`manager.py`)

**Search Paths:**
1. Custom paths from `skill_paths` config
2. Project-local: `.vibe/skills/`
3. Global: `~/.vibe/skills/`

**Discovery Process:**
1. Scan directories for `SKILL.md` files
2. Parse YAML frontmatter
3. Validate metadata
4. Register available skills
5. Apply enabled/disabled filters

#### User-Invocable Skills

When `user-invocable: true`, the skill appears as a slash command:

**Invocation:**
```
/code-review
```

**Behavior:**
- Skill content is loaded
- Injected as user message
- Agent acts according to skill instructions
- Tool restrictions applied if specified

#### Skill Integration with System Prompt

Skills are included in the universal system prompt to inform the agent about available capabilities.

---

### 2.12 File Handling

#### Path Resolution

**Autocompletion** (`vibe/core/autocompletion/`)

**File Indexer** (`file_indexer/indexer.py`)
- Watches filesystem for changes (`watchfiles` library)
- Builds index of all files in project
- Respects `.gitignore` patterns
- Incremental updates
- LRU cache for performance

**Path Completer** (`completers.py`)
- Fuzzy matching on file paths
- Recursive directory traversal
- Smart filtering (ignores binaries, .git, etc.)
- Ranked by relevance

**Usage in UI:**
```
> Read the file @src/ma[TAB]
> Read the file @src/main.py
```

#### File Operations Safety

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

### 2.13 Error Handling

#### Exception Hierarchy

**Core Exceptions:**
```python
# Agent Loop
class AgentLoopError(Exception)
class AgentLoopStateError(AgentLoopError)
class AgentLoopLLMResponseError(AgentLoopError)
class TeleportError(AgentLoopError)

# Tools
class ToolError(Exception)
class ToolPermissionError(Exception)

# Config
class MissingAPIKeyError(RuntimeError)
class MissingPromptFileError(RuntimeError)
class WrongBackendError(RuntimeError)

# LLM
class BackendError(Exception)
class RateLimitError(Exception)
```

#### Error Handling Patterns

**Tool Execution:**
```python
try:
    result = await tool.run(args, ctx)
except ToolError as e:
    # Logged to LLM as tool error
    # Displayed in UI as ErrorMessage
    # Agent can retry or abort
except ToolPermissionError as e:
    # User denied permission
    # Tool call skipped
    # Feedback sent to agent
```

**LLM Errors:**
```python
try:
    result = await backend.complete(...)
except BackendError as e:
    if e.status == HTTP 429:  # Rate limit
        raise RateLimitError(...)
    else:
        raise RuntimeError(f"API error: {e}")
```

**User-Facing Errors:**
- Displayed as `ErrorMessage` widget in UI
- Logged to session if enabled
- Can be collapsed (Ctrl+O)
- Agent receives error in next turn

**Cancellation Handling:**
```python
try:
    async for event in agent_loop.act(prompt):
        ...
except asyncio.CancelledError:
    # Graceful shutdown
    # Cleanup loading widgets
    # Display InterruptMessage
    # Agent loop stopped
```

---

### 2.14 Testing Infrastructure

**Location:** `tests/`

#### Test Structure

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

#### Testing Stack

**Frameworks:**
- `pytest` (8.3.5+) - Test runner
- `pytest-asyncio` - Async test support
- `pytest-timeout` - Test timeout enforcement
- `pytest-xdist` - Parallel test execution
- `pytest-textual-snapshot` - UI snapshot testing

**Mocking:**
- `respx` - HTTP mocking for API tests
- Custom mock factories in `tests/mock/`

**Coverage Tools:**
- Test configuration in `pyproject.toml`
- Parallel execution: `-n auto`
- Max runtime: 10 seconds per test

#### Test Categories

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

**Example Test:**
```python
# tests/tools/test_bash.py
@pytest.mark.asyncio
async def test_bash_execution():
    tool = BashTool.from_config(BashConfig())
    args = BashArgs(command="echo 'hello'")

    result = None
    async for item in tool.run(args):
        if isinstance(item, BashResult):
            result = item

    assert result is not None
    assert "hello" in result.output
    assert result.exit_code == 0
```

**Snapshot Test:**
```python
# tests/snapshots/test_ui_snapshot_basic_conversation.py
async def test_basic_message_display(snap_compare):
    app = create_test_app()
    await app.mount_message(UserMessage("Hello"))
    await app.mount_message(AssistantMessage("Hi there!"))

    assert await snap_compare(app)
```

---

## 3. Architecture Deep Dive

### 3.1 Entry Points and Flow

#### CLI Entry Point

**File:** `vibe/cli/entrypoint.py` → `main()`

**Flow:**
```
main()
├── parse_arguments()
├── check working directory exists
├── change to --workdir if specified
├── check_and_resolve_trusted_folder()
│   ├── Check if .vibe/ exists in cwd
│   ├── Check trusted_folders.toml
│   └── Show trust dialog if needed
├── unlock_config_paths()
│   └── Set VIBE_HOME and config paths
└── run_cli(args)
    ├── load_dotenv_values()  # Load .env file
    ├── VibeConfig.load()     # Load config.toml
    ├── Handle --setup flag
    │   └── run_onboarding()
    ├── Handle session continuation
    │   ├── --continue: load last session
    │   └── --resume ID: load specific session
    ├── Create AgentLoop
    │   ├── Select agent profile
    │   ├── Initialize ToolManager
    │   ├── Initialize SkillManager
    │   ├── Initialize LLM backend
    │   ├── Build system prompt
    │   └── Set up middleware pipeline
    ├── Programmatic mode?
    │   └── run_programmatic(...)
    └── Interactive mode
        └── run_textual_ui(agent_loop, initial_prompt)
```

**Programmatic Mode Flow:**
```python
async def run_programmatic(agent_loop, prompt, args):
    """Non-interactive execution."""
    output_handler = create_output_handler(args.output)

    async for event in agent_loop.act(prompt):
        output_handler.handle(event)

    output_handler.finalize()
```

#### ACP Entry Point

**File:** `vibe/acp/entrypoint.py` → `main()`

**Flow:**
```
main()
├── handle_debug_mode()  # Attach debugpy if DEBUG_MODE=true
├── unlock_config_paths()
├── bootstrap_config_files()
│   ├── Create default config.toml
│   └── Create history file
├── Handle --setup flag
│   └── run_onboarding()
└── run_acp_server()
    ├── Initialize ACP router
    ├── Load config
    ├── Set up tool adapters
    ├── Listen on stdio
    └── Handle ACP messages
        ├── initialize
        ├── new_session
        ├── send_message
        ├── set_model
        └── set_mode
```

---

### 3.2 Agent Loop Flow

**File:** `vibe/core/agent_loop.py` - `AgentLoop` class

#### Initialization

```python
AgentLoop.__init__(config, agent_name, message_observer, ...)
├── Initialize managers
│   ├── AgentManager (agent profiles)
│   ├── ToolManager (tool discovery)
│   └── SkillManager (skill discovery)
├── Initialize backend
│   ├── Select backend (Mistral or Generic)
│   └── Set API timeout
├── Build system prompt
│   ├── Load agent-specific prompt
│   ├── Include project context
│   ├── List available tools
│   └── Include active skills
├── Create message list
│   └── [LLMMessage(role=system, content=system_prompt)]
├── Initialize stats
│   └── AgentStats (tokens, cost, steps)
├── Set up middleware
│   ├── TurnLimitMiddleware (if max_turns set)
│   ├── PriceLimitMiddleware (if max_price set)
│   ├── AutoCompactMiddleware (if threshold > 0)
│   └── PlanAgentMiddleware
└── Create SessionLogger
```

#### Conversation Turn

```python
async def act(msg: str) -> AsyncGenerator[BaseEvent]:
    """Main conversation loop."""

    # 1. Add user message
    messages.append(LLMMessage(role=user, content=msg))
    yield UserMessageEvent(...)

    # 2. Loop until no tool calls
    while True:
        # 3. Pre-turn middleware
        result = await middleware.run_before_turn()
        if result.action == STOP:
            return
        if result.action == COMPACT:
            await compact()

        # 4. LLM turn
        if streaming:
            async for event in stream_assistant_events():
                yield event  # AssistantEvent, ReasoningEvent
        else:
            event = await get_assistant_event()
            yield event

        # 5. Parse tool calls
        parsed = format_handler.parse_message(last_message)
        resolved = format_handler.resolve_tool_calls(parsed)

        # 6. Execute tool calls
        for tool_call in resolved.tool_calls:
            yield ToolCallEvent(...)

            # 7. Get approval
            decision = await should_execute_tool(tool_call)
            if decision.verdict == SKIP:
                yield ToolResultEvent(skipped=True)
                continue

            # 8. Run tool
            try:
                async for item in tool.invoke(**args):
                    if isinstance(item, ToolStreamEvent):
                        yield item
                    else:
                        result = item

                messages.append(LLMMessage(role=tool, content=result))
                yield ToolResultEvent(result=result)
            except ToolError as e:
                messages.append(LLMMessage(role=tool, content=error))
                yield ToolResultEvent(error=error)

        # 9. Post-turn middleware
        result = await middleware.run_after_turn()
        if result.action == STOP:
            return

        # 10. Check if should continue
        if last_message.role != tool:
            break  # No tool calls, conversation complete
```

---

### 3.3 Middleware Pipeline

**File:** `vibe/core/middleware.py`

#### Middleware Architecture

```python
class MiddlewarePipeline:
    middlewares: list[BaseMiddleware]

    async def run_before_turn(ctx) -> MiddlewareResult:
        for middleware in self.middlewares:
            result = await middleware.before_turn(ctx)
            if result.action != CONTINUE:
                return result
        return MiddlewareResult(action=CONTINUE)

    async def run_after_turn(ctx) -> MiddlewareResult:
        for middleware in self.middlewares:
            result = await middleware.after_turn(ctx)
            if result.action != CONTINUE:
                return result
        return MiddlewareResult(action=CONTINUE)
```

#### Built-in Middleware

**1. TurnLimitMiddleware**
```python
class TurnLimitMiddleware:
    max_turns: int
    current_turn: int = 0

    async def before_turn(ctx):
        if current_turn >= max_turns:
            return MiddlewareResult(
                action=STOP,
                reason=f"Reached max turns ({max_turns})"
            )
        current_turn += 1
        return MiddlewareResult(action=CONTINUE)
```

**2. PriceLimitMiddleware**
```python
class PriceLimitMiddleware:
    max_price: float

    async def before_turn(ctx):
        cost = ctx.stats.session_cost
        if cost >= max_price:
            return MiddlewareResult(
                action=STOP,
                reason=f"Exceeded price limit (${cost:.2f} >= ${max_price:.2f})"
            )
        return MiddlewareResult(action=CONTINUE)
```

**3. AutoCompactMiddleware**
```python
class AutoCompactMiddleware:
    threshold: int  # Token count

    async def after_turn(ctx):
        if ctx.stats.context_tokens >= threshold:
            return MiddlewareResult(
                action=COMPACT,
                metadata={"threshold": threshold}
            )
        return MiddlewareResult(action=CONTINUE)
```

**4. ContextWarningMiddleware**
```python
class ContextWarningMiddleware:
    warn_fraction: float  # e.g., 0.5 for 50%
    threshold: int

    async def after_turn(ctx):
        warn_at = threshold * warn_fraction
        if ctx.stats.context_tokens >= warn_at:
            return MiddlewareResult(
                action=INJECT_MESSAGE,
                message=f"⚠ Context is {ctx.stats.context_tokens} tokens "
                        f"(will auto-compact at {threshold})"
            )
        return MiddlewareResult(action=CONTINUE)
```

**5. PlanAgentMiddleware**
```python
class PlanAgentMiddleware:
    """Offers to switch to plan mode for codebase exploration."""

    async def after_turn(ctx):
        if should_suggest_plan_mode(ctx):
            return MiddlewareResult(
                action=INJECT_MESSAGE,
                message="💡 Tip: Use the 'plan' agent for exploration tasks"
            )
        return MiddlewareResult(action=CONTINUE)
```

---

### 3.4 System Prompt Generation

**File:** `vibe/core/system_prompt.py`

#### Universal System Prompt Builder

```python
def get_universal_system_prompt(
    tool_manager: ToolManager,
    config: VibeConfig,
    skill_manager: SkillManager,
    agent_manager: AgentManager
) -> str:
    """Build complete system prompt with all context."""

    parts = []

    # 1. Base agent prompt
    if config.include_prompt_detail:
        base_prompt = config.system_prompt  # From cli.md or custom
        parts.append(base_prompt)

    # 2. Model information
    if config.include_model_info:
        model = config.get_active_model()
        parts.append(f"Active model: {model.alias}")

    # 3. Commit signature
    if config.include_commit_signature:
        parts.append("Co-authored-by: Claude <...>")

    # 4. Tool descriptions
    tools_section = []
    for tool_name, tool in tool_manager.available_tools.items():
        tool_info = tool.get_info()

        # Add tool prompt if exists
        tool_prompt = tool.get_tool_prompt()

        desc = f"## {tool_info.name}\n{tool_info.description}"
        if tool_prompt:
            desc += f"\n\n{tool_prompt}"

        tools_section.append(desc)

    if tools_section:
        parts.append("# Available Tools\n\n" + "\n\n".join(tools_section))

    # 5. Skills information
    skills_section = []
    for name, skill in skill_manager.available_skills.items():
        if skill.user_invocable:
            skills_section.append(f"/{name} - {skill.description}")

    if skills_section:
        parts.append("# Skills\n\n" + "\n".join(skills_section))

    # 6. Project context
    if config.include_project_context:
        context = get_project_context(config.project_context)
        if context:
            parts.append(f"# Project Context\n\n{context}")

    return "\n\n".join(parts)
```

#### Project Context Provider

**File:** `vibe/core/system_prompt.py` - `ProjectContextProvider`

**Responsibilities:**
- Generate directory tree (respecting .gitignore)
- Extract git information (branch, commit, status)
- Read project documentation (README, CONTRIBUTING, etc.)
- Provide recent commit history

**Limits:**
- Max characters: 40,000 (configurable)
- Max files: 1000
- Max depth: 3
- Timeout: 2.0 seconds

**Example Output:**
```
# Project Context

## Git Information
Branch: main
Commit: 51fecc6
Status: Clean

## Recent Commits
51fecc6 2.1.0 (#317)
9809cfc v2.0.2
bd3497b v2.0.1

## Directory Tree
.
├── vibe/
│   ├── cli/
│   ├── core/
│   └── setup/
├── tests/
├── docs/
├── pyproject.toml
└── README.md

## Project Documentation
[Content from README.md if exists]
```

---

### 3.5 UI Event Handling

**File:** `vibe/cli/textual_ui/handlers/event_handler.py`

#### Event Handler Architecture

```python
class EventHandler:
    """Centralized event handling for all agent events."""

    current_tool_call: ToolCallMessage | None
    current_compact: CompactMessage | None

    async def handle_event(event, loading_active, loading_widget):
        match event:
            case UserMessageEvent():
                await mount(UserMessage(event.content))

            case AssistantEvent():
                await mount(AssistantMessage(event.content))

            case ReasoningEvent():
                await mount(ReasoningMessage(event.content))

            case ToolCallEvent():
                tool_msg = ToolCallMessage(
                    tool_name=event.tool_name,
                    args=event.args
                )
                self.current_tool_call = tool_msg
                await mount(tool_msg)
                if loading_widget:
                    loading_widget.set_status(f"Running {event.tool_name}...")

            case ToolStreamEvent():
                if self.current_tool_call:
                    self.current_tool_call.append_stream(event.content)

            case ToolResultEvent():
                await mount(ToolResultMessage(
                    tool_name=event.tool_name,
                    result=event.result,
                    error=event.error,
                    duration=event.duration
                ))
                self.current_tool_call = None

            case CompactStartEvent():
                compact_msg = CompactMessage()
                self.current_compact = compact_msg
                await mount(compact_msg)

            case CompactEndEvent():
                if self.current_compact:
                    self.current_compact.set_complete(
                        old_tokens=event.old_context_tokens,
                        new_tokens=event.new_context_tokens
                    )
                self.current_compact = None
```

---

### 3.6 Configuration Resolution

**File:** `vibe/core/config.py`

#### Configuration Merging

**Agent-Specific Config:**
```python
class AgentManager:
    def get_merged_config(agent_name: str) -> VibeConfig:
        """Merge base config with agent-specific overrides."""

        base = self.base_config_getter()
        agent_config = self.load_agent_config(agent_name)

        if not agent_config:
            return base

        # Create new config with agent overrides
        merged = VibeConfig.model_copy(base)

        # Override model
        if agent_config.active_model:
            merged.active_model = agent_config.active_model

        # Override system prompt
        if agent_config.system_prompt_id:
            merged.system_prompt_id = agent_config.system_prompt_id

        # Override auto-approve
        if agent_config.auto_approve is not None:
            merged.auto_approve = agent_config.auto_approve

        # Merge tool configs (agent-specific takes precedence)
        for tool_name, tool_config in agent_config.tools.items():
            merged.tools[tool_name] = tool_config

        # Override enabled/disabled tools
        if agent_config.enabled_tools:
            merged.enabled_tools = agent_config.enabled_tools
        if agent_config.disabled_tools:
            merged.disabled_tools = agent_config.disabled_tools

        return merged
```

**Tool Permission Resolution:**
```python
def get_effective_permission(tool_name: str) -> ToolPermission:
    """Resolve tool permission from multiple sources."""

    # Priority order:
    # 1. Agent-specific tool config
    # 2. Global tool config
    # 3. Tool default

    if tool_name in agent_config.tools:
        return agent_config.tools[tool_name].permission

    if tool_name in base_config.tools:
        return base_config.tools[tool_name].permission

    return ToolPermission.ASK  # Default
```

---

### 3.7 Streaming Architecture

**File:** `vibe/core/agent_loop.py`

#### Streaming Flow

```python
async def _stream_assistant_events() -> AsyncGenerator[...]:
    """Stream LLM responses in batches for smooth UI updates."""

    content_buffer = ""
    reasoning_buffer = ""
    chunks_with_content = 0
    chunks_with_reasoning = 0
    BATCH_SIZE = 5  # Batch 5 chunks before yielding

    async for chunk in backend.complete_streaming(...):
        # Handle reasoning content
        if chunk.message.reasoning_content:
            if content_buffer:
                yield AssistantEvent(content=content_buffer)
                content_buffer = ""

            reasoning_buffer += chunk.message.reasoning_content
            chunks_with_reasoning += 1

            if chunks_with_reasoning >= BATCH_SIZE:
                yield ReasoningEvent(content=reasoning_buffer)
                reasoning_buffer = ""
                chunks_with_reasoning = 0

        # Handle regular content
        if chunk.message.content:
            if reasoning_buffer:
                yield ReasoningEvent(content=reasoning_buffer)
                reasoning_buffer = ""

            content_buffer += chunk.message.content
            chunks_with_content += 1

            if chunks_with_content >= BATCH_SIZE:
                yield AssistantEvent(content=content_buffer)
                content_buffer = ""
                chunks_with_content = 0

    # Flush remaining
    if reasoning_buffer:
        yield ReasoningEvent(content=reasoning_buffer)
    if content_buffer:
        yield AssistantEvent(content=content_buffer)
```

**UI Streaming Handling:**
```python
# vibe/cli/textual_ui/app.py
async def _mount_and_scroll(widget):
    if isinstance(widget, AssistantMessage):
        if current_streaming_message:
            # Append to existing message
            await current_streaming_message.append_content(widget.content)
        else:
            # Start new streaming message
            await messages_area.mount(widget)
            await widget.write_initial_content()
            current_streaming_message = widget
```

---

## 4. Extension Points

### 4.1 Custom Tools

**How to Create:**

1. **Define Tool Class:**
```python
# ~/.vibe/tools/my_tool.py
from vibe.core.tools.base import BaseTool, BaseToolConfig, BaseToolState
from pydantic import BaseModel

class MyToolArgs(BaseModel):
    input: str

class MyToolResult(BaseModel):
    output: str

class MyToolConfig(BaseToolConfig):
    api_key: str = ""

class MyToolState(BaseToolState):
    counter: int = 0

class MyTool(
    BaseTool[MyToolArgs, MyToolResult, MyToolConfig, MyToolState]
):
    description = "My custom tool that does something useful"

    async def run(self, args: MyToolArgs, ctx=None):
        self.state.counter += 1
        result = f"Processed: {args.input} (count: {self.state.counter})"
        yield MyToolResult(output=result)
```

2. **Configure Tool:**
```toml
# config.toml
tool_paths = ["~/.vibe/tools"]

[tools.my_tool]
permission = "ask"
api_key = "secret"
```

3. **Use Tool:**
```
> Use my_tool to process "hello world"
```

### 4.2 Custom Agents

**How to Create:**

1. **Create Agent Config:**
```toml
# ~/.vibe/agents/researcher.toml
system_prompt_id = "researcher"
auto_approve = false

enabled_tools = [
    "read_file",
    "grep",
    "ask_user_question"
]

[tools.read_file]
permission = "always"

[tools.grep]
permission = "always"
```

2. **Create System Prompt:**
```markdown
# ~/.vibe/prompts/researcher.md
You are a research assistant focused on code analysis.
Your goal is to help users understand codebases without
making any modifications.

Always:
- Ask clarifying questions before searching
- Provide detailed explanations
- Suggest related areas to explore
```

3. **Use Agent:**
```bash
vibe --agent researcher
```

### 4.3 Custom Skills

**How to Create:**

1. **Create Skill Directory:**
```bash
mkdir -p ~/.vibe/skills/code-metrics
```

2. **Create SKILL.md:**
```markdown
# ~/.vibe/skills/code-metrics/SKILL.md
---
name: code-metrics
description: Analyze code metrics and complexity
user-invocable: true
allowed-tools:
  - grep
  - read_file
  - bash
---

# Code Metrics Skill

You are tasked with analyzing code metrics for the current project.

Steps:
1. Use grep to find all code files
2. Count lines of code
3. Identify complex functions (>50 lines)
4. Calculate cyclomatic complexity estimates
5. Present findings in a table

Present results as:
| Metric | Value |
|--------|-------|
| Total Files | X |
| Total LOC | Y |
...
```

3. **Use Skill:**
```
/code-metrics
```

### 4.4 MCP Server Integration

**How to Integrate:**

1. **Install MCP Server:**
```bash
npm install -g @modelcontextprotocol/server-fetch
```

2. **Configure in Vibe:**
```toml
[[mcp_servers]]
name = "web"
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-fetch"]
startup_timeout_sec = 15
tool_timeout_sec = 120
```

3. **Configure Tool Permissions:**
```toml
[tools.web_fetch]
permission = "ask"

[tools.web_search]
permission = "always"
```

4. **Use Tools:**
```
> Use web_fetch to get https://example.com
```

### 4.5 Custom Themes (Limited)

**Note:** Vibe uses a fixed theme (`textual-ansi`) for consistency. Custom theming is limited to:

**TCSS Customization:**
```css
/* ~/.vibe/custom.tcss */
AssistantMessage {
    background: $surface;
    border: solid $primary;
}

ToolCallMessage {
    border: solid $success;
}
```

**Apply via Textual:**
Not currently supported through Vibe CLI directly, but could be added as a feature.

---

## 5. Potential Improvement Areas

### 5.1 Architecture & Design

**1. Plugin Architecture**
- **Current:** Tools/Skills/Agents are discovered from filesystem
- **Opportunity:** Formal plugin system with:
  - Plugin registry
  - Version management
  - Dependency resolution
  - Marketplace integration

**2. Event Bus**
- **Current:** Direct coupling between AgentLoop and UI
- **Opportunity:** Pub-sub event bus for:
  - Multiple observers
  - Plugin event subscriptions
  - Better separation of concerns
  - Easier testing

**3. Tool Composition**
- **Current:** Tools are independent
- **Opportunity:** Tool composition/chaining:
  - Define tool workflows
  - Sequential tool execution
  - Conditional branching
  - Error recovery strategies

**4. Modular Backend System**
- **Current:** Backend factory with two implementations
- **Opportunity:** Plugin-based backend system:
  - Register custom backends at runtime
  - Backend-specific optimizations
  - Multi-backend routing (cheap models for simple tasks)

### 5.2 Performance Optimizations

**1. Lazy Loading**
- **Current:** All tools/skills loaded at startup
- **Opportunity:**
  - Lazy tool discovery
  - On-demand skill loading
  - Faster startup time

**2. Caching**
- **Current:** Limited caching (tool prompts, file index)
- **Opportunity:**
  - LRU cache for LLM responses (identical prompts)
  - Tool result caching (deterministic tools)
  - Session snapshot caching

**3. Streaming Optimizations**
- **Current:** Fixed batch size (5 chunks)
- **Opportunity:**
  - Adaptive batching based on chunk size
  - Parallel streaming (multiple tools)
  - Streaming compression for network

**4. Virtual Scrolling**
- **Current:** Pruning after 1500 lines
- **Opportunity:**
  - True virtual scrolling (only render visible)
  - Infinite scroll
  - Better memory management

### 5.3 Feature Enhancements

**1. Advanced Search**
- **Current:** Grep-based search
- **Opportunity:**
  - Semantic code search
  - AST-based search
  - Cross-reference analysis
  - Symbol navigation

**2. Multi-Session Management**
- **Current:** One session at a time
- **Opportunity:**
  - Tabbed sessions
  - Session switching
  - Session merging
  - Session comparison

**3. Collaborative Features**
- **Current:** Single-user only
- **Opportunity:**
  - Multi-user sessions
  - Session sharing
  - Real-time collaboration
  - Code review workflows

**4. Advanced Tool Approval**
- **Current:** Simple yes/no approval
- **Opportunity:**
  - Modify tool arguments before execution
  - Dry-run mode for all tools
  - Conditional approval (if X then approve Y)
  - Approval policies (RBAC)

**5. Diff Preview**
- **Current:** Tools execute immediately after approval
- **Opportunity:**
  - Show diffs before file writes
  - Interactive diff approval
  - Batch diff review
  - Undo/redo support

**6. Context Management**
- **Current:** Auto-compact at threshold
- **Opportunity:**
  - Smart context pruning (keep important messages)
  - Context summarization with importance scoring
  - Context branches (explore different paths)
  - Context snapshots

**7. Testing Integration**
- **Current:** Tests run manually
- **Opportunity:**
  - Agent-driven test execution
  - Test generation based on code changes
  - TDD workflow support
  - Coverage analysis

**8. Documentation Generation**
- **Current:** Manual documentation
- **Opportunity:**
  - Auto-generate docstrings
  - Generate README sections
  - Update documentation on code changes
  - API documentation generation

**9. Refactoring Assistance**
- **Current:** Basic search-replace
- **Opportunity:**
  - AST-based refactoring
  - Rename symbol across files
  - Extract function/class
  - Inline function
  - Move to file

**10. Git Integration**
- **Current:** Git via bash tool
- **Opportunity:**
  - Native git operations
  - Interactive commit creation
  - Pull request generation
  - Merge conflict resolution
  - Branch management

### 5.4 User Experience

**1. Onboarding**
- **Current:** Basic API key setup
- **Opportunity:**
  - Interactive tutorial
  - Sample projects
  - Feature discovery
  - Configuration wizard

**2. Help System**
- **Current:** /help command
- **Opportunity:**
  - Contextual help
  - Interactive documentation
  - Video tutorials
  - Tool examples

**3. Input Enhancements**
- **Current:** Text input with basic features
- **Opportunity:**
  - Rich text editing
  - Syntax highlighting
  - Code snippets
  - Inline images
  - File attachments

**4. Visualization**
- **Current:** Text-only output
- **Opportunity:**
  - ASCII graphs
  - Dependency diagrams
  - Call graphs
  - Metrics dashboards

**5. Keyboard Shortcuts**
- **Current:** Basic shortcuts
- **Opportunity:**
  - Customizable keybindings
  - Vim/Emacs modes
  - Command palette
  - Quick actions

**6. Accessibility**
- **Current:** Basic terminal accessibility
- **Opportunity:**
  - Screen reader support
  - High contrast themes
  - Font size controls
  - Color blind modes

### 5.5 Integration & Extensibility

**1. IDE Integration**
- **Current:** ACP support
- **Opportunity:**
  - VS Code extension
  - JetBrains plugin enhancements
  - Neovim plugin improvements
  - Sublime Text plugin

**2. CI/CD Integration**
- **Current:** Programmatic mode
- **Opportunity:**
  - GitHub Actions integration
  - GitLab CI templates
  - Pre-commit hooks
  - Automated code review

**3. Monitoring & Analytics**
- **Current:** Session stats
- **Opportunity:**
  - Usage analytics
  - Cost tracking dashboard
  - Performance metrics
  - Error monitoring

**4. API for Extensions**
- **Current:** Python-based tools only
- **Opportunity:**
  - REST API for tool development
  - WebSocket for real-time tools
  - Language-agnostic tool protocol
  - Tool marketplace

### 5.6 Security & Privacy

**1. Sandboxing**
- **Current:** Direct command execution
- **Opportunity:**
  - Containerized tool execution
  - Permission model (filesystem, network)
  - Resource limits
  - Audit logging

**2. Secret Management**
- **Current:** .env file, keyring
- **Opportunity:**
  - Integration with 1Password, Bitwarden
  - Vault integration
  - Secret scanning
  - Automatic secret redaction

**3. Privacy**
- **Current:** Sessions logged locally
- **Opportunity:**
  - Encrypted session storage
  - PII detection and redaction
  - Compliance modes (GDPR, SOC2)
  - Data retention policies

**4. Code Review**
- **Current:** Manual review of changes
- **Opportunity:**
  - Security scanning before execution
  - Static analysis integration
  - Vulnerability detection
  - License compliance checking

### 5.7 Testing & Quality

**1. Test Coverage**
- **Current:** Good coverage, some gaps
- **Opportunity:**
  - Increase to 90%+
  - Property-based testing
  - Mutation testing
  - Fuzz testing

**2. Integration Testing**
- **Current:** Limited integration tests
- **Opportunity:**
  - End-to-end test suite
  - Multi-agent scenarios
  - Performance benchmarks
  - Regression test suite

**3. UI Testing**
- **Current:** Snapshot tests
- **Opportunity:**
  - Visual regression testing
  - Automated UI interaction tests
  - Accessibility tests
  - Cross-terminal testing

### 5.8 Documentation

**1. User Documentation**
- **Current:** README, docs/
- **Opportunity:**
  - Video tutorials
  - Interactive guides
  - Use case examples
  - Best practices guide

**2. Developer Documentation**
- **Current:** Code comments, AGENTS.md
- **Opportunity:**
  - Architecture diagrams
  - API reference (Sphinx/MkDocs)
  - Plugin development guide
  - Contributing guide improvements

**3. Code Documentation**
- **Current:** Good docstrings
- **Opportunity:**
  - More inline comments for complex logic
  - Design decision documentation
  - Performance notes
  - Security considerations

### 5.9 Observability

**1. Logging**
- **Current:** Basic logging
- **Opportunity:**
  - Structured logging
  - Log levels per component
  - Log aggregation
  - Real-time log viewer

**2. Metrics**
- **Current:** Session stats only
- **Opportunity:**
  - Prometheus metrics
  - Custom metrics API
  - Performance profiling
  - Resource usage tracking

**3. Tracing**
- **Current:** No distributed tracing
- **Opportunity:**
  - OpenTelemetry integration
  - Request tracing
  - Performance bottleneck identification
  - Distributed tool execution tracking

### 5.10 Specific Code Improvements

**1. Type Safety**
- **Current:** Good type hints
- **Opportunity:**
  - Stricter mypy configuration
  - Runtime type checking for APIs
  - Exhaustive pattern matching
  - Generic type improvements

**2. Error Handling**
- **Current:** Good exception hierarchy
- **Opportunity:**
  - Error recovery strategies
  - User-friendly error messages
  - Error reporting (Sentry)
  - Graceful degradation

**3. Code Organization**
- **Current:** Well-organized
- **Opportunity:**
  - Extract shared utilities
  - Reduce circular dependencies
  - Better module boundaries
  - Cleaner imports

**4. Dependency Management**
- **Current:** uv-based
- **Opportunity:**
  - Optional dependencies
  - Lighter base installation
  - Plugin dependencies
  - Version pinning strategy

---

## Appendix A: Key File Reference

### Entry Points
- `vibe/cli/entrypoint.py` - CLI entry point
- `vibe/acp/entrypoint.py` - ACP server entry point

### Core Logic
- `vibe/core/agent_loop.py` - Main agent loop (1030 lines)
- `vibe/core/config.py` - Configuration system (618 lines)
- `vibe/core/system_prompt.py` - System prompt builder (550 lines)

### UI Layer
- `vibe/cli/textual_ui/app.py` - Main Textual app (1475 lines)
- `vibe/cli/textual_ui/handlers/event_handler.py` - Event handling
- `vibe/cli/textual_ui/widgets/` - UI widget components

### Tool System
- `vibe/core/tools/base.py` - Base tool abstractions (350 lines)
- `vibe/core/tools/manager.py` - Tool discovery and management (420 lines)
- `vibe/core/tools/builtins/` - Built-in tool implementations

### LLM Integration
- `vibe/core/llm/backend/mistral.py` - Mistral backend
- `vibe/core/llm/backend/generic.py` - Generic backend
- `vibe/core/llm/format.py` - Message formatting and parsing

### Agent System
- `vibe/core/agents/manager.py` - Agent profile management
- `vibe/core/agents/models.py` - Agent data models

### Skills System
- `vibe/core/skills/manager.py` - Skill discovery and management
- `vibe/core/skills/models.py` - Skill data models
- `vibe/core/skills/parser.py` - YAML frontmatter parsing

### Session Management
- `vibe/core/session/session_logger.py` - Session persistence (300 lines)
- `vibe/core/session/session_loader.py` - Session restoration
- `vibe/core/session/session_migration.py` - Schema migrations

### Configuration & Paths
- `vibe/core/paths/config_paths.py` - Config path resolution
- `vibe/core/paths/global_paths.py` - Global path constants

### Utilities
- `vibe/core/utils.py` - Common utilities (400 lines)
- `vibe/core/types.py` - Type definitions (300 lines)
- `vibe/core/middleware.py` - Middleware implementations

---

## Appendix B: Technology Stack

### Core Dependencies

**UI/Terminal:**
- `textual` (1.0.0+) - TUI framework
- `textual-speedups` (0.2.1+) - Performance optimizations
- `rich` (14.0.0+) - Rich text formatting

**LLM Integration:**
- `mistralai` (1.9.11) - Mistral SDK
- `httpx` (0.28.1+) - HTTP client for API calls

**Configuration:**
- `pydantic` (2.12.4+) - Data validation
- `pydantic-settings` (2.12.0+) - Settings management
- `pyyaml` (6.0.0+) - YAML parsing
- `python-dotenv` (1.0.0+) - Environment variable loading
- `tomli-w` (1.2.0+) - TOML writing

**Process Management:**
- `pexpect` (4.9.0+) - Interactive process control (bash tool)
- `anyio` (4.12.0+) - Async I/O

**Utilities:**
- `watchfiles` (1.1.1+) - Filesystem watching
- `pyperclip` (1.11.0+) - Clipboard integration
- `keyring` (25.6.0+) - Secure credential storage
- `cryptography` (44.0.0+) - Encryption
- `zstandard` (0.25.0+) - Compression

**Git:**
- `gitpython` (3.1.46+) - Git integration
- `giturlparse` (0.14.0+) - Git URL parsing

**Code Parsing:**
- `tree-sitter` (0.25.2+) - Syntax tree parsing
- `tree-sitter-bash` (0.25.1+) - Bash grammar

**MCP:**
- `mcp` (1.14.0+) - Model Context Protocol SDK

**ACP:**
- `agent-client-protocol` (0.8.0) - Agent Client Protocol

### Development Dependencies

**Testing:**
- `pytest` (8.3.5+) - Test framework
- `pytest-asyncio` (1.2.0+) - Async testing
- `pytest-timeout` (2.4.0+) - Test timeouts
- `pytest-textual-snapshot` (1.1.0+) - UI snapshot testing
- `pytest-xdist` (3.8.0+) - Parallel testing
- `respx` (0.22.0+) - HTTP mocking

**Code Quality:**
- `pyright` (1.1.403+) - Type checking
- `ruff` (0.14.5+) - Linting and formatting
- `pre-commit` (4.2.0+) - Git hooks
- `vulture` (2.14+) - Dead code detection
- `typos` (1.34.0+) - Spell checking

**Build:**
- `twine` (5.0.0+) - Package publishing
- `pyinstaller` (6.17.0+) - Binary packaging
- `hatchling` - Build backend

**Debugging:**
- `debugpy` (1.8.19+) - Debug adapter

### Python Version
- **Minimum:** Python 3.12+
- **Recommended:** Python 3.12 or 3.13

---

## Appendix C: Project Statistics

**Code Size:**
- Total Python files: 139 (in vibe/)
- Test files: ~50+ (in tests/)
- Lines of code: ~30,000+ (estimated)

**Architecture:**
- Modules: 8 (cli, core, setup, acp, etc.)
- Built-in tools: 8
- Built-in agents: 5
- UI widgets: 20+

**Configuration:**
- Config options: 30+
- Environment variables: 10+
- File locations: 8+

**Testing:**
- Test categories: 11
- Testing frameworks: 7
- Test timeout: 10 seconds

---

**End of Document**
