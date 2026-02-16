"""Conversation threading data models for Mistral Vibe.

This module defines the core data structures for managing conversation threads,
file deltas, and snapshots. Threads allow users to explore multiple solution
approaches in parallel without losing context.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from vibe.core.types import LLMMessage

if TYPE_CHECKING:
    from vibe.core.session.thread_manager import ThreadManager


class FileDelta(BaseModel):
    """Tracks file changes in a thread.

    Uses a simple delta model to track which files were modified, created,
    or deleted in a thread. For MVP, we track operation type and basic stats.
    """

    path: str
    operation: str  # 'modified' | 'created' | 'deleted'
    timestamp: datetime = Field(default_factory=datetime.now)
    line_changes: tuple[int, int] = (0, 0)  # (additions, deletions)
    original_content: str | None = None  # file content before first modification
    current_content: str | None = None  # file content after latest modification
    content_too_large: bool = False  # True if file exceeded size limit


class Thread(BaseModel):
    """Represents a conversation thread with its own history and file changes.

    Each thread maintains:
    - Its own message history (new messages added after fork)
    - Parent thread reference for inheritance
    - Fork point (message index in parent)
    - File deltas tracking changes
    """

    name: str
    parent: str | None = None  # Parent thread name, None for main
    fork_point: int = 0  # Message index where thread was created
    created_at: datetime = Field(default_factory=datetime.now)
    description: str = ""
    messages: list[LLMMessage] = Field(default_factory=list)
    file_deltas: dict[str, FileDelta] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_full_history(self, thread_manager: ThreadManager) -> list[LLMMessage]:
        """Get complete message history including inherited messages from parent.

        Args:
            thread_manager: ThreadManager instance to resolve parent messages

        Returns:
            Complete list of messages (parent's messages up to fork point + this thread's messages)
        """
        if self.parent is None:
            return self.messages.copy()

        parent_thread = thread_manager.get_thread(self.parent)
        parent_full = parent_thread.get_full_history(thread_manager)
        # fork_point is relative to parent's own messages, so we need to
        # include all inherited messages plus fork_point direct messages
        inherited_count = len(parent_full) - len(parent_thread.messages)
        parent_messages = parent_full[: inherited_count + self.fork_point]
        return parent_messages + self.messages

    @property
    def total_messages(self) -> int:
        """Count of messages added in this thread (not including inherited)."""
        return len(self.messages)

    @property
    def total_file_changes(self) -> int:
        """Count of file changes in this thread."""
        return len(self.file_deltas)


class Snapshot(BaseModel):
    """Point-in-time snapshot of a thread state.

    Snapshots allow users to mark important points in their conversation
    and return to them later. For MVP, snapshots are lightweight references.
    """

    name: str
    thread_name: str
    message_id: int  # Index in thread's message list
    created_at: datetime = Field(default_factory=datetime.now)
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
