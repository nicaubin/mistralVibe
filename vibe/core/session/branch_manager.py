"""Branch management for conversation branching feature.

This module provides the BranchManager class which orchestrates all branching
operations including creating branches, switching between them, managing snapshots,
and tracking file changes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from vibe.core.session.branch import Branch, FileDelta, Snapshot


class BranchManagerError(Exception):
    """Base exception for BranchManager errors."""


class BranchNotFoundError(BranchManagerError):
    """Raised when attempting to access a non-existent branch."""


class BranchAlreadyExistsError(BranchManagerError):
    """Raised when attempting to create a branch with a duplicate name."""


class SnapshotNotFoundError(BranchManagerError):
    """Raised when attempting to access a non-existent snapshot."""


class BranchManager:
    """Manages conversation branches and snapshots.

    The BranchManager is responsible for:
    - Creating and deleting branches
    - Switching between branches
    - Tracking file changes per branch
    - Managing snapshots
    - Providing branch state for persistence
    """

    def __init__(self, session_id: str) -> None:
        """Initialize BranchManager with a main branch.

        Args:
            session_id: Unique identifier for the session
        """
        self.session_id = session_id
        self.branches: dict[str, Branch] = {}
        self.active_branch_name: str = "main"
        self.snapshots: dict[str, Snapshot] = {}

        # Initialize main branch
        self.branches["main"] = Branch(
            name="main",
            parent=None,
            fork_point=0,
            created_at=datetime.now(),
        )

    @property
    def active_branch(self) -> Branch:
        """Get the currently active branch."""
        return self.branches[self.active_branch_name]

    def get_branch(self, name: str) -> Branch:
        """Get a branch by name.

        Args:
            name: Branch name

        Returns:
            Branch instance

        Raises:
            BranchNotFoundError: If branch does not exist
        """
        if name not in self.branches:
            raise BranchNotFoundError(f"Branch '{name}' does not exist")
        return self.branches[name]

    def create_branch(
        self,
        name: str,
        parent: str | None = None,
        fork_point: int | None = None,
        description: str = "",
    ) -> Branch:
        """Create a new branch.

        Args:
            name: Name for the new branch
            parent: Parent branch name (defaults to current active branch)
            fork_point: Message index to fork from (defaults to parent's message count)
            description: Optional description of the branch

        Returns:
            Newly created Branch instance

        Raises:
            BranchAlreadyExistsError: If branch name already exists
            BranchNotFoundError: If parent branch does not exist
        """
        if name in self.branches:
            raise BranchAlreadyExistsError(f"Branch '{name}' already exists")

        parent = parent or self.active_branch_name
        if parent not in self.branches:
            raise BranchNotFoundError(f"Parent branch '{parent}' does not exist")

        parent_branch = self.branches[parent]

        # Default fork point is current message count in parent
        if fork_point is None:
            fork_point = len(parent_branch.messages)

        branch = Branch(
            name=name,
            parent=parent,
            fork_point=fork_point,
            created_at=datetime.now(),
            description=description,
        )

        self.branches[name] = branch
        return branch

    def switch_branch(self, name: str) -> Branch:
        """Switch to a different branch.

        Args:
            name: Name of branch to switch to

        Returns:
            The newly active Branch instance

        Raises:
            BranchNotFoundError: If branch does not exist
        """
        if name not in self.branches:
            raise BranchNotFoundError(f"Branch '{name}' does not exist")

        self.active_branch_name = name
        return self.branches[name]

    def list_branches(self) -> list[Branch]:
        """Get list of all branches.

        Returns:
            List of all Branch instances
        """
        return list(self.branches.values())

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch.

        Args:
            name: Name of branch to delete
            force: If True, allow deletion of active branch

        Raises:
            BranchNotFoundError: If branch does not exist
            BranchManagerError: If trying to delete main or active branch without force
        """
        if name not in self.branches:
            raise BranchNotFoundError(f"Branch '{name}' does not exist")

        if name == "main":
            raise BranchManagerError("Cannot delete the main branch")

        if name == self.active_branch_name and not force:
            raise BranchManagerError(
                f"Cannot delete active branch '{name}'. Switch to another branch first or use force=True"
            )

        # If deleting active branch with force, switch to main
        if name == self.active_branch_name and force:
            self.active_branch_name = "main"

        del self.branches[name]

    def track_file_change(
        self,
        file_path: str,
        operation: str,
        line_changes: tuple[int, int] = (0, 0),
    ) -> None:
        """Track a file change in the current branch.

        Args:
            file_path: Path to the file that changed
            operation: Type of operation ('modified', 'created', 'deleted')
            line_changes: Tuple of (additions, deletions)
        """
        delta = FileDelta(
            path=file_path,
            operation=operation,
            timestamp=datetime.now(),
            line_changes=line_changes,
        )
        self.active_branch.file_deltas[file_path] = delta

    def create_snapshot(
        self,
        name: str,
        description: str = "",
        branch_name: str | None = None,
    ) -> Snapshot:
        """Create a snapshot of a branch at its current state.

        Args:
            name: Name for the snapshot
            description: Optional description
            branch_name: Branch to snapshot (defaults to active branch)

        Returns:
            Created Snapshot instance

        Raises:
            BranchManagerError: If snapshot name already exists
            BranchNotFoundError: If branch does not exist
        """
        if name in self.snapshots:
            raise BranchManagerError(f"Snapshot '{name}' already exists")

        branch_name = branch_name or self.active_branch_name
        if branch_name not in self.branches:
            raise BranchNotFoundError(f"Branch '{branch_name}' does not exist")

        branch = self.branches[branch_name]

        snapshot = Snapshot(
            name=name,
            branch_name=branch_name,
            message_id=len(branch.messages),
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

    def restore_snapshot(self, name: str) -> Branch:
        """Restore to a snapshot by creating a new branch.

        Creates a new branch from the snapshot point with name "{snapshot_name}-restored".

        Args:
            name: Name of snapshot to restore

        Returns:
            Newly created Branch instance

        Raises:
            SnapshotNotFoundError: If snapshot does not exist
        """
        if name not in self.snapshots:
            raise SnapshotNotFoundError(f"Snapshot '{name}' does not exist")

        snapshot = self.snapshots[name]

        # Create unique branch name for restored snapshot
        restored_branch_name = f"{name}-restored"
        counter = 1
        while restored_branch_name in self.branches:
            restored_branch_name = f"{name}-restored-{counter}"
            counter += 1

        branch = self.create_branch(
            name=restored_branch_name,
            parent=snapshot.branch_name,
            fork_point=snapshot.message_id,
            description=f"Restored from snapshot: {name}",
        )

        # Switch to the restored branch
        self.switch_branch(restored_branch_name)
        return branch

    def get_branch_info(self, name: str) -> dict[str, Any]:
        """Get detailed information about a branch.

        Args:
            name: Branch name

        Returns:
            Dictionary with branch metadata and stats
        """
        branch = self.get_branch(name)
        return {
            "name": branch.name,
            "parent": branch.parent,
            "fork_point": branch.fork_point,
            "created_at": branch.created_at.isoformat(),
            "description": branch.description,
            "total_messages": branch.total_messages,
            "total_file_changes": branch.total_file_changes,
            "is_active": name == self.active_branch_name,
        }

    def serialize(self) -> dict[str, Any]:
        """Serialize branch manager state for persistence.

        Returns:
            Dictionary containing all branches, snapshots, and active branch
        """
        return {
            "session_id": self.session_id,
            "active_branch": self.active_branch_name,
            "branches": {
                name: branch.model_dump(mode="json")
                for name, branch in self.branches.items()
            },
            "snapshots": {
                name: snapshot.model_dump(mode="json")
                for name, snapshot in self.snapshots.items()
            },
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> BranchManager:
        """Deserialize branch manager state from persistence.

        Args:
            data: Serialized branch manager state

        Returns:
            Reconstructed BranchManager instance
        """
        manager = cls.__new__(cls)
        manager.session_id = data["session_id"]
        manager.active_branch_name = data["active_branch"]

        # Reconstruct branches
        manager.branches = {
            name: Branch.model_validate(branch_data)
            for name, branch_data in data["branches"].items()
        }

        # Reconstruct snapshots
        manager.snapshots = {
            name: Snapshot.model_validate(snapshot_data)
            for name, snapshot_data in data["snapshots"].items()
        }

        return manager
