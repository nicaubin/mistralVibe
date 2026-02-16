"""Thread management for conversation threading feature.

This module provides the ThreadManager class which orchestrates all threading
operations including creating threads, switching between them, managing snapshots,
and tracking file changes.
"""

from __future__ import annotations

import copy
from datetime import datetime
from pathlib import Path
from typing import Any

from vibe.core.session.thread import Thread, FileDelta, Snapshot

MAX_FILE_CONTENT_SIZE = 100 * 1024  # 100KB


class ThreadManagerError(Exception):
    """Base exception for ThreadManager errors."""


class ThreadNotFoundError(ThreadManagerError):
    """Raised when attempting to access a non-existent thread."""


class ThreadAlreadyExistsError(ThreadManagerError):
    """Raised when attempting to create a thread with a duplicate name."""


class SnapshotNotFoundError(ThreadManagerError):
    """Raised when attempting to access a non-existent snapshot."""


class ThreadManager:
    """Manages conversation threads and snapshots.

    The ThreadManager is responsible for:
    - Creating and deleting threads
    - Switching between threads
    - Tracking file changes per thread
    - Managing snapshots
    - Providing thread state for persistence
    """

    def __init__(self, session_id: str) -> None:
        """Initialize ThreadManager with a main thread.

        Args:
            session_id: Unique identifier for the session
        """
        self.session_id = session_id
        self.threads: dict[str, Thread] = {}
        self.active_thread_name: str = "main"
        self.snapshots: dict[str, Snapshot] = {}

        # Initialize main thread
        self.threads["main"] = Thread(
            name="main",
            parent=None,
            fork_point=0,
            created_at=datetime.now(),
        )

    @property
    def active_thread(self) -> Thread:
        """Get the currently active thread."""
        return self.threads[self.active_thread_name]

    def get_thread(self, name: str) -> Thread:
        """Get a thread by name.

        Args:
            name: Thread name

        Returns:
            Thread instance

        Raises:
            ThreadNotFoundError: If thread does not exist
        """
        if name not in self.threads:
            raise ThreadNotFoundError(f"Thread '{name}' does not exist")
        return self.threads[name]

    def create_thread(
        self,
        name: str,
        parent: str | None = None,
        fork_point: int | None = None,
        description: str = "",
    ) -> Thread:
        """Create a new thread.

        Args:
            name: Name for the new thread
            parent: Parent thread name (defaults to current active thread)
            fork_point: Message index to fork from (defaults to parent's message count)
            description: Optional description of the thread

        Returns:
            Newly created Thread instance

        Raises:
            ThreadAlreadyExistsError: If thread name already exists
            ThreadNotFoundError: If parent thread does not exist
        """
        if name in self.threads:
            raise ThreadAlreadyExistsError(f"Thread '{name}' already exists")

        parent = parent or self.active_thread_name
        if parent not in self.threads:
            raise ThreadNotFoundError(f"Parent thread '{parent}' does not exist")

        parent_thread = self.threads[parent]

        # Default fork point is current message count in parent
        if fork_point is None:
            fork_point = len(parent_thread.messages)

        thread = Thread(
            name=name,
            parent=parent,
            fork_point=fork_point,
            created_at=datetime.now(),
            description=description,
            file_deltas=copy.deepcopy(parent_thread.file_deltas),
        )

        self.threads[name] = thread
        return thread

    def switch_thread(self, name: str) -> Thread:
        """Switch to a different thread.

        Args:
            name: Name of thread to switch to

        Returns:
            The newly active Thread instance

        Raises:
            ThreadNotFoundError: If thread does not exist
        """
        if name not in self.threads:
            raise ThreadNotFoundError(f"Thread '{name}' does not exist")

        self.active_thread_name = name
        return self.threads[name]

    def list_threads(self) -> list[Thread]:
        """Get list of all threads.

        Returns:
            List of all Thread instances
        """
        return list(self.threads.values())

    def import_thread(
        self, thread: Thread, new_name: str | None = None
    ) -> Thread:
        """Import a thread from another session.

        The imported thread is made standalone (no parent, fork_point=0).

        Args:
            thread: Thread instance to import
            new_name: Optional new name for the thread

        Returns:
            The imported Thread instance

        Raises:
            ThreadAlreadyExistsError: If a thread with the same name already exists
        """
        name = new_name or thread.name
        if name in self.threads:
            raise ThreadAlreadyExistsError(f"Thread '{name}' already exists")

        thread.name = name
        thread.parent = None
        thread.fork_point = 0
        self.threads[name] = thread
        return thread

    def delete_thread(self, name: str) -> None:
        """Delete a thread.

        Args:
            name: Name of thread to delete

        Raises:
            ThreadNotFoundError: If thread does not exist
            ThreadManagerError: If trying to delete main or active thread
        """
        if name not in self.threads:
            raise ThreadNotFoundError(f"Thread '{name}' does not exist")

        if name == "main":
            raise ThreadManagerError("Cannot delete the main thread")

        if name == self.active_thread_name:
            raise ThreadManagerError(
                f"Cannot delete active thread '{name}'. Switch to another thread first."
            )

        del self.threads[name]

    def track_file_change(
        self,
        file_path: str,
        operation: str,
        line_changes: tuple[int, int] = (0, 0),
    ) -> None:
        """Track a file change in the current thread.

        Preserves original_content and current_content from existing deltas
        so that content captured before/after tool execution is not lost.

        Args:
            file_path: Path to the file that changed
            operation: Type of operation ('modified', 'created', 'deleted')
            line_changes: Tuple of (additions, deletions)
        """
        existing = self.active_thread.file_deltas.get(file_path)
        delta = FileDelta(
            path=file_path,
            operation=operation,
            timestamp=datetime.now(),
            line_changes=line_changes,
            original_content=existing.original_content if existing else None,
            current_content=existing.current_content if existing else None,
            content_too_large=existing.content_too_large if existing else False,
        )
        self.active_thread.file_deltas[file_path] = delta

    def _read_file_content(self, file_path: str) -> tuple[str | None, bool]:
        """Read file content if it exists and is within size limits.

        Returns:
            Tuple of (content_or_none, too_large_flag)
        """
        try:
            path = Path(file_path)
            if not path.is_file():
                return None, False
            size = path.stat().st_size
            if size > MAX_FILE_CONTENT_SIZE:
                return None, True
            return path.read_text(encoding="utf-8"), False
        except (OSError, UnicodeDecodeError):
            return None, False

    def capture_file_before_modification(self, file_path: str) -> None:
        """Capture original file content before first modification on this thread.

        No-op if a delta already exists for this file (original already captured).
        """
        if file_path in self.active_thread.file_deltas:
            return
        content, too_large = self._read_file_content(file_path)
        # Create a placeholder delta to store the original content.
        # The real operation/line_changes will be set by track_file_change later.
        delta = FileDelta(
            path=file_path,
            operation="pending",
            original_content=content,
            content_too_large=too_large,
        )
        self.active_thread.file_deltas[file_path] = delta

    def update_file_current_content(self, file_path: str) -> None:
        """Read modified file from disk and update delta's current_content."""
        delta = self.active_thread.file_deltas.get(file_path)
        if delta is None:
            return
        content, too_large = self._read_file_content(file_path)
        delta.current_content = content
        if too_large:
            delta.content_too_large = True

    def save_current_thread_files(self) -> None:
        """Re-read all tracked files from disk into current_content.

        Call before switching away from a thread to capture any manual edits.
        """
        for file_path, delta in self.active_thread.file_deltas.items():
            if delta.content_too_large:
                continue
            content, too_large = self._read_file_content(file_path)
            delta.current_content = content
            if too_large:
                delta.content_too_large = True

    def restore_thread_files(self, thread_name: str) -> list[str]:
        """Write current_content to disk for all tracked files in the given thread.

        Args:
            thread_name: Name of thread whose files to restore

        Returns:
            List of warning messages for files that couldn't be restored
        """
        warnings: list[str] = []
        thread = self.get_thread(thread_name)
        for file_path, delta in thread.file_deltas.items():
            if delta.content_too_large:
                warnings.append(f"Skipped '{file_path}': file too large to restore")
                continue
            if delta.current_content is None:
                continue
            try:
                path = Path(file_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(delta.current_content, encoding="utf-8")
            except OSError as e:
                warnings.append(f"Failed to restore '{file_path}': {e}")
        return warnings

    def restore_files_for_leaving_thread(
        self, old_thread_name: str, new_thread_name: str
    ) -> list[str]:
        """For files only in the OLD thread, restore original state.

        - If file was created on old thread: delete it
        - If file was modified on old thread: restore original_content

        Args:
            old_thread_name: Thread we're leaving
            new_thread_name: Thread we're switching to

        Returns:
            List of warning messages
        """
        warnings: list[str] = []
        old_thread = self.get_thread(old_thread_name)
        new_thread = self.get_thread(new_thread_name)
        new_files = set(new_thread.file_deltas.keys())

        for file_path, delta in old_thread.file_deltas.items():
            if file_path in new_files:
                continue
            if delta.content_too_large:
                warnings.append(
                    f"Skipped reverting '{file_path}': file too large"
                )
                continue
            try:
                path = Path(file_path)
                if delta.operation == "created":
                    if path.is_file():
                        path.unlink()
                elif delta.original_content is not None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(delta.original_content, encoding="utf-8")
            except OSError as e:
                warnings.append(f"Failed to revert '{file_path}': {e}")
        return warnings

    def create_snapshot(
        self,
        name: str,
        description: str = "",
        thread_name: str | None = None,
    ) -> Snapshot:
        """Create a snapshot of a thread at its current state.

        Args:
            name: Name for the snapshot
            description: Optional description
            thread_name: Thread to snapshot (defaults to active thread)

        Returns:
            Created Snapshot instance

        Raises:
            ThreadManagerError: If snapshot name already exists
            ThreadNotFoundError: If thread does not exist
        """
        if name in self.snapshots:
            raise ThreadManagerError(f"Snapshot '{name}' already exists")

        thread_name = thread_name or self.active_thread_name
        if thread_name not in self.threads:
            raise ThreadNotFoundError(f"Thread '{thread_name}' does not exist")

        thread = self.threads[thread_name]

        snapshot = Snapshot(
            name=name,
            thread_name=thread_name,
            message_id=len(thread.messages),
            created_at=datetime.now(),
            description=description,
        )

        self.snapshots[name] = snapshot
        return snapshot

    def list_snapshots(self) -> list[Snapshot]:
        """Get list of all snapshots.

        Returns:
            List of all Snapshot instances
        """
        return list(self.snapshots.values())

    def restore_snapshot(self, name: str) -> Thread:
        """Restore to a snapshot by creating a new thread.

        Creates a new thread from the snapshot point with name "{snapshot_name}-restored".

        Args:
            name: Name of snapshot to restore

        Returns:
            Newly created Thread instance

        Raises:
            SnapshotNotFoundError: If snapshot does not exist
        """
        if name not in self.snapshots:
            raise SnapshotNotFoundError(f"Snapshot '{name}' does not exist")

        snapshot = self.snapshots[name]

        # Create unique thread name for restored snapshot
        restored_thread_name = f"{name}-restored"
        counter = 1
        while restored_thread_name in self.threads:
            restored_thread_name = f"{name}-restored-{counter}"
            counter += 1

        thread = self.create_thread(
            name=restored_thread_name,
            parent=snapshot.thread_name,
            fork_point=snapshot.message_id,
            description=f"Restored from snapshot: {name}",
        )

        # Switch to the restored thread
        self.switch_thread(restored_thread_name)
        return thread

    def get_thread_info(self, name: str) -> dict[str, Any]:
        """Get detailed information about a thread.

        Args:
            name: Thread name

        Returns:
            Dictionary with thread metadata and stats
        """
        thread = self.get_thread(name)
        return {
            "name": thread.name,
            "parent": thread.parent,
            "fork_point": thread.fork_point,
            "created_at": thread.created_at.isoformat(),
            "description": thread.description,
            "total_messages": thread.total_messages,
            "total_file_changes": thread.total_file_changes,
            "is_active": name == self.active_thread_name,
        }

    def serialize(self) -> dict[str, Any]:
        """Serialize thread manager state for persistence.

        Returns:
            Dictionary containing all threads, snapshots, and active thread
        """
        return {
            "session_id": self.session_id,
            "active_thread": self.active_thread_name,
            "threads": {
                name: thread.model_dump(mode="json")
                for name, thread in self.threads.items()
            },
            "snapshots": {
                name: snapshot.model_dump(mode="json")
                for name, snapshot in self.snapshots.items()
            },
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> ThreadManager:
        """Deserialize thread manager state from persistence.

        Args:
            data: Serialized thread manager state

        Returns:
            Reconstructed ThreadManager instance
        """
        manager = cls.__new__(cls)
        manager.session_id = data["session_id"]
        manager.active_thread_name = data["active_thread"]

        # Reconstruct threads
        manager.threads = {
            name: Thread.model_validate(thread_data)
            for name, thread_data in data["threads"].items()
        }

        # Reconstruct snapshots
        manager.snapshots = {
            name: Snapshot.model_validate(snapshot_data)
            for name, snapshot_data in data["snapshots"].items()
        }

        return manager
