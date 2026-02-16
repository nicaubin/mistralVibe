"""Unit tests for ConvThreadManager and threading functionality."""

from __future__ import annotations

import pytest

from vibe.core.session.conv_thread_manager import (
    ConvThreadAlreadyExistsError,
    ConvThreadManager,
    ConvThreadManagerError,
    ConvThreadNotFoundError,
    SnapshotNotFoundError,
)
from vibe.core.types import LLMMessage, Role


class TestConvThreadManager:
    """Test suite for ConvThreadManager."""

    def test_init_creates_main_thread(self):
        """Test that initialization creates a main thread."""
        manager = ConvThreadManager("test-session")
        assert "main" in manager.threads
        assert manager.active_thread_name == "main"
        assert manager.active_thread.name == "main"
        assert manager.active_thread.parent is None

    def test_create_thread_basic(self):
        """Test creating a basic thread."""
        manager = ConvThreadManager("test-session")

        # Add some messages to main
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Hello")
        )
        manager.active_thread.messages.append(
            LLMMessage(role=Role.assistant, content="Hi there")
        )

        # Create branch
        branch = manager.create_thread("feature-1")

        assert branch.name == "feature-1"
        assert branch.parent == "main"
        assert branch.fork_point == 2  # Forked after 2 messages
        assert len(branch.messages) == 0  # New branch has no messages yet

    def test_create_thread_with_description(self):
        """Test creating a branch with description."""
        manager = ConvThreadManager("test-session")
        branch = manager.create_thread("feature-1", description="Test feature")

        assert branch.description == "Test feature"

    def test_create_thread_duplicate_name_fails(self):
        """Test that creating a branch with duplicate name fails."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")

        with pytest.raises(ConvThreadAlreadyExistsError):
            manager.create_thread("feature-1")

    def test_create_thread_from_specific_parent(self):
        """Test creating a branch from a specific parent."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")
        manager.switch_thread("feature-1")

        # Create branch from feature-1
        branch = manager.create_thread("feature-2", parent="feature-1")

        assert branch.parent == "feature-1"

    def test_create_thread_nonexistent_parent_fails(self):
        """Test that creating a branch from nonexistent parent fails."""
        manager = ConvThreadManager("test-session")

        with pytest.raises(ConvThreadNotFoundError):
            manager.create_thread("feature-1", parent="nonexistent")

    def test_switch_thread(self):
        """Test switching between threads."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")

        assert manager.active_thread_name == "main"

        branch = manager.switch_thread("feature-1")

        assert manager.active_thread_name == "feature-1"
        assert branch.name == "feature-1"

    def test_switch_to_nonexistent_branch_fails(self):
        """Test that switching to nonexistent branch fails."""
        manager = ConvThreadManager("test-session")

        with pytest.raises(ConvThreadNotFoundError):
            manager.switch_thread("nonexistent")

    def test_list_threads(self):
        """Test listing all threads."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")
        manager.create_thread("feature-2")

        threads = manager.list_threads()

        assert len(threads) == 3  # main + feature-1 + feature-2
        thread_names = {b.name for b in threads}
        assert thread_names == {"main", "feature-1", "feature-2"}

    def test_delete_thread(self):
        """Test deleting a branch."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")

        manager.delete_thread("feature-1")

        assert "feature-1" not in manager.threads

    def test_delete_main_branch_fails(self):
        """Test that deleting main branch fails."""
        manager = ConvThreadManager("test-session")

        with pytest.raises(ConvThreadManagerError):
            manager.delete_thread("main")

    def test_delete_active_thread_fails(self):
        """Test that deleting active branch fails without force."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")
        manager.switch_thread("feature-1")

        with pytest.raises(ConvThreadManagerError):
            manager.delete_thread("feature-1")

    def test_delete_active_thread_always_fails(self):
        """Test that deleting active branch always fails."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1")
        manager.switch_thread("feature-1")

        with pytest.raises(ConvThreadManagerError):
            manager.delete_thread("feature-1")

    def test_delete_nonexistent_branch_fails(self):
        """Test that deleting nonexistent branch fails."""
        manager = ConvThreadManager("test-session")

        with pytest.raises(ConvThreadNotFoundError):
            manager.delete_thread("nonexistent")

    def test_track_file_change(self):
        """Test tracking file changes."""
        manager = ConvThreadManager("test-session")

        manager.track_file_change(
            "test.py",
            "modified",
            line_changes=(10, 5),
        )

        assert "test.py" in manager.active_thread.file_deltas
        delta = manager.active_thread.file_deltas["test.py"]
        assert delta.path == "test.py"
        assert delta.operation == "modified"
        assert delta.line_changes == (10, 5)

    def test_track_file_change_overwrites(self):
        """Test that tracking same file multiple times overwrites."""
        manager = ConvThreadManager("test-session")

        manager.track_file_change("test.py", "created", (10, 0))
        manager.track_file_change("test.py", "modified", (5, 2))

        assert len(manager.active_thread.file_deltas) == 1
        delta = manager.active_thread.file_deltas["test.py"]
        assert delta.operation == "modified"
        assert delta.line_changes == (5, 2)

    def test_create_snapshot(self):
        """Test creating a snapshot."""
        manager = ConvThreadManager("test-session")
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Test")
        )

        snapshot = manager.create_snapshot("snapshot-1", description="Test snapshot")

        assert snapshot.name == "snapshot-1"
        assert snapshot.thread_name == "main"
        assert snapshot.message_id == 1
        assert snapshot.description == "Test snapshot"

    def test_create_snapshot_duplicate_name_fails(self):
        """Test that creating snapshot with duplicate name fails."""
        manager = ConvThreadManager("test-session")
        manager.create_snapshot("snapshot-1")

        with pytest.raises(ConvThreadManagerError):
            manager.create_snapshot("snapshot-1")

    def test_list_snapshots(self):
        """Test listing all snapshots."""
        manager = ConvThreadManager("test-session")
        manager.create_snapshot("snapshot-1")
        manager.create_snapshot("snapshot-2")

        snapshots = manager.list_snapshots()

        assert len(snapshots) == 2
        snapshot_names = {s.name for s in snapshots}
        assert snapshot_names == {"snapshot-1", "snapshot-2"}

    def test_restore_snapshot(self):
        """Test restoring from a snapshot."""
        manager = ConvThreadManager("test-session")

        # Add messages to main
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Message 1")
        )
        manager.active_thread.messages.append(
            LLMMessage(role=Role.assistant, content="Response 1")
        )

        # Create snapshot
        manager.create_snapshot("snapshot-1")

        # Add more messages
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Message 2")
        )

        # Restore snapshot
        restored = manager.restore_snapshot("snapshot-1")

        assert restored.name == "snapshot-1-restored"
        assert restored.parent == "main"
        assert restored.fork_point == 2  # Snapshot was at 2 messages
        assert manager.active_thread_name == "snapshot-1-restored"

    def test_restore_nonexistent_snapshot_fails(self):
        """Test that restoring nonexistent snapshot fails."""
        manager = ConvThreadManager("test-session")

        with pytest.raises(SnapshotNotFoundError):
            manager.restore_snapshot("nonexistent")

    def test_get_thread_info(self):
        """Test getting branch information."""
        manager = ConvThreadManager("test-session")
        manager.create_thread("feature-1", description="Test branch")
        manager.switch_thread("feature-1")
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Test")
        )
        manager.track_file_change("test.py", "modified")

        info = manager.get_thread_info("feature-1")

        assert info["name"] == "feature-1"
        assert info["parent"] == "main"
        assert info["description"] == "Test branch"
        assert info["total_messages"] == 1
        assert info["total_file_changes"] == 1
        assert info["is_active"] is True

    def test_serialize_deserialize(self):
        """Test serialization and deserialization."""
        manager = ConvThreadManager("test-session")

        # Add some threads and snapshots
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Message 1")
        )
        manager.create_thread("feature-1", description="Feature branch")
        manager.switch_thread("feature-1")
        manager.track_file_change("test.py", "modified", (10, 5))
        manager.create_snapshot("snapshot-1", description="Test snapshot")

        # Serialize
        data = manager.serialize()

        # Deserialize
        restored = ConvThreadManager.deserialize(data)

        assert restored.session_id == manager.session_id
        assert restored.active_thread_name == "feature-1"
        assert len(restored.threads) == 2
        assert "main" in restored.threads
        assert "feature-1" in restored.threads
        assert len(restored.snapshots) == 1
        assert "snapshot-1" in restored.snapshots

        # Verify branch details
        feature_branch = restored.threads["feature-1"]
        assert feature_branch.parent == "main"
        assert feature_branch.description == "Feature branch"
        assert len(feature_branch.file_deltas) == 1
        assert "test.py" in feature_branch.file_deltas


class TestConvThread:
    """Test suite for ConvThread model."""

    def test_get_full_history_no_parent(self):
        """Test getting full history for main branch."""
        manager = ConvThreadManager("test-session")
        main_branch = manager.active_thread

        main_branch.messages.append(LLMMessage(role=Role.user, content="Message 1"))
        main_branch.messages.append(LLMMessage(role=Role.assistant, content="Response 1"))

        history = main_branch.get_full_history(manager)

        assert len(history) == 2
        assert history[0].content == "Message 1"
        assert history[1].content == "Response 1"

    def test_get_full_history_with_parent(self):
        """Test getting full history with parent inheritance."""
        manager = ConvThreadManager("test-session")

        # Add messages to main
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Main 1")
        )
        manager.active_thread.messages.append(
            LLMMessage(role=Role.assistant, content="Main 2")
        )

        # Create branch and add messages
        manager.create_thread("feature-1")
        manager.switch_thread("feature-1")
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Feature 1")
        )

        # Get full history
        history = manager.active_thread.get_full_history(manager)

        assert len(history) == 3
        assert history[0].content == "Main 1"
        assert history[1].content == "Main 2"
        assert history[2].content == "Feature 1"

    def test_get_full_history_nested_threads(self):
        """Test getting full history with nested threads."""
        manager = ConvThreadManager("test-session")

        # Add messages to main
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Main 1")
        )

        # Create feature-1 from main
        manager.create_thread("feature-1")
        manager.switch_thread("feature-1")
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Feature 1")
        )

        # Create feature-2 from feature-1
        manager.create_thread("feature-2", parent="feature-1")
        manager.switch_thread("feature-2")
        manager.active_thread.messages.append(
            LLMMessage(role=Role.user, content="Feature 2")
        )

        # Get full history
        history = manager.active_thread.get_full_history(manager)

        assert len(history) == 3
        assert history[0].content == "Main 1"
        assert history[1].content == "Feature 1"
        assert history[2].content == "Feature 2"

    def test_total_messages_property(self):
        """Test total_messages property."""
        manager = ConvThreadManager("test-session")
        branch = manager.active_thread

        assert branch.total_messages == 0

        branch.messages.append(LLMMessage(role=Role.user, content="Test"))
        assert branch.total_messages == 1

    def test_total_file_changes_property(self):
        """Test total_file_changes property."""
        manager = ConvThreadManager("test-session")
        manager.track_file_change("test1.py", "modified")
        manager.track_file_change("test2.py", "created")

        assert manager.active_thread.total_file_changes == 2
