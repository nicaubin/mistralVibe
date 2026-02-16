"""Thread indicator widget for the UI bottom bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

if TYPE_CHECKING:
    from vibe.core.session.conv_thread_manager import ConvThreadManager


class ConvThreadDisplay(NoMarkupStatic):
    """Displays the current active thread in the UI bottom bar."""

    def __init__(self, conv_thread_manager: ConvThreadManager) -> None:
        super().__init__()
        self.can_focus = False
        self._conv_thread_manager = conv_thread_manager
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with current thread info."""
        active_thread = self._conv_thread_manager.active_thread
        name = active_thread.name
        msgs = active_thread.total_messages
        files = active_thread.total_file_changes
        self.update(f"thread: {name} ({msgs} msgs, {files} files)")

    def refresh_display(self) -> None:
        """Refresh the display (call after thread operations)."""
        self._update_display()
