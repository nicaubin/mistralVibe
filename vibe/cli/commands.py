from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Command:
    aliases: frozenset[str]
    description: str
    handler: str
    exits: bool = False


class CommandRegistry:
    def __init__(self, excluded_commands: list[str] | None = None) -> None:
        if excluded_commands is None:
            excluded_commands = []
        self.commands = {
            "help": Command(
                aliases=frozenset(["/help"]),
                description="Show help message",
                handler="_show_help",
            ),
            "config": Command(
                aliases=frozenset(["/config", "/model"]),
                description="Edit config settings",
                handler="_show_config",
            ),
            "reload": Command(
                aliases=frozenset(["/reload"]),
                description="Reload configuration from disk",
                handler="_reload_config",
            ),
            "clear": Command(
                aliases=frozenset(["/clear"]),
                description="Clear conversation history",
                handler="_clear_history",
            ),
            "log": Command(
                aliases=frozenset(["/log"]),
                description="Show path to current interaction log file",
                handler="_show_log_path",
            ),
            "compact": Command(
                aliases=frozenset(["/compact"]),
                description="Compact conversation history by summarizing",
                handler="_compact_history",
            ),
            "exit": Command(
                aliases=frozenset(["/exit"]),
                description="Exit the application",
                handler="_exit_app",
                exits=True,
            ),
            "terminal-setup": Command(
                aliases=frozenset(["/terminal-setup"]),
                description="Configure Shift+Enter for newlines",
                handler="_setup_terminal",
            ),
            "status": Command(
                aliases=frozenset(["/status"]),
                description="Display agent statistics",
                handler="_show_status",
            ),
            "teleport": Command(
                aliases=frozenset(["/teleport"]),
                description="Teleport session to Vibe Nuage",
                handler="_teleport_command",
            ),
            "branch-create": Command(
                aliases=frozenset(["/branch-create"]),
                description="Create a new conversation branch",
                handler="_branch_create",
            ),
            "branch-list": Command(
                aliases=frozenset(["/branch-list"]),
                description="List all conversation branches",
                handler="_branch_list",
            ),
            "branch-switch": Command(
                aliases=frozenset(["/branch-switch"]),
                description="Switch to a different branch",
                handler="_branch_switch",
            ),
            "branch-merge": Command(
                aliases=frozenset(["/branch-merge"]),
                description="Merge a branch (not yet implemented)",
                handler="_branch_merge",
            ),
            "branch-snapshot": Command(
                aliases=frozenset(["/branch-snapshot"]),
                description="Create a snapshot of current state",
                handler="_snapshot_create",
            ),
            "branch-snapshots": Command(
                aliases=frozenset(["/branch-snapshots"]),
                description="List all snapshots",
                handler="_snapshot_list",
            ),
            "branch-restore": Command(
                aliases=frozenset(["/branch-restore"]),
                description="Restore from a snapshot",
                handler="_snapshot_restore",
            ),
            "branch-delete": Command(
                aliases=frozenset(["/branch-delete"]),
                description="Delete a branch",
                handler="_branch_delete",
            ),
            "branch-history": Command(
                aliases=frozenset(["/branch-history"]),
                description="List branches from past sessions",
                handler="_branch_history",
            ),
            "branch-import": Command(
                aliases=frozenset(["/branch-import"]),
                description="Import a branch from a past session",
                handler="_branch_import",
            ),
        }

        for command in excluded_commands:
            self.commands.pop(command, None)

        self._alias_map = {}
        for cmd_name, cmd in self.commands.items():
            for alias in cmd.aliases:
                self._alias_map[alias] = cmd_name

    def find_command(self, user_input: str) -> tuple[Command, str] | None:
        """Find a command matching the input, returning (command, args) or None."""
        stripped = user_input.strip()
        lower = stripped.lower()

        # Try exact match first (commands with no args)
        cmd_name = self._alias_map.get(lower)
        if cmd_name:
            return self.commands[cmd_name], ""

        # Try prefix match: split on first space to extract command and args
        first_space = lower.find(" ")
        if first_space > 0:
            cmd_part = lower[:first_space]
            cmd_name = self._alias_map.get(cmd_part)
            if cmd_name:
                args = stripped[first_space:].strip()
                return self.commands[cmd_name], args

        return None

    def get_help_text(self) -> str:
        lines: list[str] = [
            "### Keyboard Shortcuts",
            "",
            "- `Enter` Submit message",
            "- `Ctrl+J` / `Shift+Enter` Insert newline",
            "- `Escape` Interrupt agent or close dialogs",
            "- `Ctrl+C` Quit (or clear input if text present)",
            "- `Ctrl+G` Edit input in external editor",
            "- `Ctrl+O` Toggle tool output view",
            "- `Shift+Tab` Toggle auto-approve mode",
            "",
            "### Special Features",
            "",
            "- `!<command>` Execute bash command directly",
            "- `@path/to/file/` Autocompletes file paths",
            "",
            "### Commands",
            "",
        ]

        for cmd in self.commands.values():
            aliases = ", ".join(f"`{alias}`" for alias in sorted(cmd.aliases))
            lines.append(f"- {aliases}: {cmd.description}")
        return "\n".join(lines)
