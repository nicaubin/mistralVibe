from __future__ import annotations

from collections.abc import Callable

from textual import events

from vibe.cli.autocompletion.base import CompletionResult, CompletionView

_BRANCH_COMMANDS = ("/branch-switch ", "/branch-delete ")

MAX_SUGGESTIONS_COUNT = 10


class BranchCompletionController:
    """Autocompletes branch names for /branch-switch and /branch-delete."""

    def __init__(
        self,
        branch_names_getter: Callable[[], list[str]],
        view: CompletionView,
    ) -> None:
        self._get_branch_names = branch_names_getter
        self._view = view
        self._suggestions: list[tuple[str, str]] = []
        self._selected_index = 0
        self._command_prefix = ""

    def can_handle(self, text: str, cursor_index: int) -> bool:
        lower = text[:cursor_index].lower()
        return any(lower.startswith(cmd) for cmd in _BRANCH_COMMANDS)

    def reset(self) -> None:
        if self._suggestions:
            self._suggestions.clear()
            self._selected_index = 0
            self._view.clear_completion_suggestions()

    def _parse_prefix_and_partial(
        self, text: str, cursor_index: int
    ) -> tuple[str, str] | None:
        lower = text[:cursor_index].lower()
        for cmd in _BRANCH_COMMANDS:
            if lower.startswith(cmd):
                prefix = text[: len(cmd)]
                partial = text[len(cmd) : cursor_index]
                return prefix, partial
        return None

    def on_text_changed(self, text: str, cursor_index: int) -> None:
        if cursor_index < 0 or cursor_index > len(text):
            self.reset()
            return

        parsed = self._parse_prefix_and_partial(text, cursor_index)
        if parsed is None:
            self.reset()
            return

        self._command_prefix, partial = parsed
        partial_lower = partial.lower()

        branches = self._get_branch_names()
        suggestions = [
            (name, "")
            for name in branches
            if name.lower().startswith(partial_lower)
        ]

        if len(suggestions) > MAX_SUGGESTIONS_COUNT:
            suggestions = suggestions[:MAX_SUGGESTIONS_COUNT]

        if suggestions:
            self._suggestions = suggestions
            self._selected_index = 0
            self._view.render_completion_suggestions(
                self._suggestions, self._selected_index
            )
        else:
            self.reset()

    def on_key(
        self, event: events.Key, text: str, cursor_index: int
    ) -> CompletionResult:
        if not self._suggestions:
            return CompletionResult.IGNORED

        match event.key:
            case "tab":
                if self._apply_selected(text, cursor_index):
                    return CompletionResult.HANDLED
                return CompletionResult.IGNORED
            case "enter":
                if self._apply_selected(text, cursor_index):
                    return CompletionResult.SUBMIT
                return CompletionResult.HANDLED
            case "down":
                self._move_selection(1)
                return CompletionResult.HANDLED
            case "up":
                self._move_selection(-1)
                return CompletionResult.HANDLED
            case _:
                return CompletionResult.IGNORED

    def _move_selection(self, delta: int) -> None:
        if not self._suggestions:
            return
        count = len(self._suggestions)
        self._selected_index = (self._selected_index + delta) % count
        self._view.render_completion_suggestions(
            self._suggestions, self._selected_index
        )

    def _apply_selected(self, text: str, cursor_index: int) -> bool:
        if not self._suggestions:
            return False
        branch_name, _ = self._suggestions[self._selected_index]
        # Replace the argument portion (everything after the command prefix)
        start = len(self._command_prefix)
        replacement = self._command_prefix + branch_name
        self._view.replace_completion_range(0, cursor_index, replacement)
        self.reset()
        return True
