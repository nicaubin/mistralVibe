"""Branch indicator widget for the UI bottom bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

if TYPE_CHECKING:
    from vibe.core.session.branch_manager import BranchManager


class BranchDisplay(NoMarkupStatic):
    """Displays the current active branch in the UI bottom bar."""

    def __init__(self, branch_manager: BranchManager) -> None:
        super().__init__()
        self.can_focus = False
        self._branch_manager = branch_manager
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with current branch info."""
        active_branch = self._branch_manager.active_branch
        name = active_branch.name
        msgs = active_branch.total_messages
        files = active_branch.total_file_changes
        self.update(f"branch: {name} ({msgs} msgs, {files} files)")

    def refresh_display(self) -> None:
        """Refresh the display (call after branch operations)."""
        self._update_display()
