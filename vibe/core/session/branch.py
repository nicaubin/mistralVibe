"""Conversation branching data models for Mistral Vibe.

This module defines the core data structures for managing conversation branches,
file deltas, and snapshots. Branches allow users to explore multiple solution
approaches in parallel without losing context.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from vibe.core.types import LLMMessage

if TYPE_CHECKING:
    from vibe.core.session.branch_manager import BranchManager


class FileDelta(BaseModel):
    """Tracks file changes in a branch.

    Uses a simple delta model to track which files were modified, created,
    or deleted in a branch. For MVP, we track operation type and basic stats.
    """

    path: str
    operation: str  # 'modified' | 'created' | 'deleted'
    timestamp: datetime = Field(default_factory=datetime.now)
    line_changes: tuple[int, int] = (0, 0)  # (additions, deletions)
    original_content: str | None = None  # file content before first modification
    current_content: str | None = None  # file content after latest modification
    content_too_large: bool = False  # True if file exceeded size limit


class Branch(BaseModel):
    """Represents a conversation branch with its own history and file changes.

    Each branch maintains:
    - Its own message history (new messages added after fork)
    - Parent branch reference for inheritance
    - Fork point (message index in parent)
    - File deltas tracking changes
    """

    name: str
    parent: str | None = None  # Parent branch name, None for main
    fork_point: int = 0  # Message index where branch was created
    created_at: datetime = Field(default_factory=datetime.now)
    description: str = ""
    messages: list[LLMMessage] = Field(default_factory=list)
    file_deltas: dict[str, FileDelta] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_full_history(self, branch_manager: BranchManager) -> list[LLMMessage]:
        """Get complete message history including inherited messages from parent.

        Args:
            branch_manager: BranchManager instance to resolve parent messages

        Returns:
            Complete list of messages (parent's messages up to fork point + this branch's messages)
        """
        if self.parent is None:
            return self.messages.copy()

        parent_branch = branch_manager.get_branch(self.parent)
        parent_full = parent_branch.get_full_history(branch_manager)
        # fork_point is relative to parent's own messages, so we need to
        # include all inherited messages plus fork_point direct messages
        inherited_count = len(parent_full) - len(parent_branch.messages)
        parent_messages = parent_full[: inherited_count + self.fork_point]
        return parent_messages + self.messages

    @property
    def total_messages(self) -> int:
        """Count of messages added in this branch (not including inherited)."""
        return len(self.messages)

    @property
    def total_file_changes(self) -> int:
        """Count of file changes in this branch."""
        return len(self.file_deltas)


class Snapshot(BaseModel):
    """Point-in-time snapshot of a branch state.

    Snapshots allow users to mark important points in their conversation
    and return to them later. For MVP, snapshots are lightweight references.
    """

    name: str
    branch_name: str
    message_id: int  # Index in branch's message list
    created_at: datetime = Field(default_factory=datetime.now)
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
