from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vibe.core.session.session_logger import (
    THREADS_FILENAME,
    MESSAGES_FILENAME,
    METADATA_FILENAME,
)
from vibe.core.types import LLMMessage

if TYPE_CHECKING:
    from vibe.core.config import SessionLoggingConfig
    from vibe.core.session.thread import Thread
    from vibe.core.session.thread_manager import ThreadManager


class SessionLoader:
    @staticmethod
    def _is_valid_session(session_dir: Path) -> bool:
        """Check if a session directory contains valid metadata and messages."""
        metadata_path = session_dir / METADATA_FILENAME
        messages_path = session_dir / MESSAGES_FILENAME

        if not metadata_path.is_file() or not messages_path.is_file():
            return False

        try:
            with metadata_path.open("r", encoding="utf-8", errors="ignore") as f:
                metadata = json.load(f)
            if not isinstance(metadata, dict):
                return False

            with messages_path.open("r", encoding="utf-8", errors="ignore") as f:
                has_messages = False
                for line in f:
                    has_messages = True
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        return False
            if not has_messages:
                return False
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False

        return True

    @staticmethod
    def latest_session(session_dirs: list[Path]) -> Path | None:
        sessions_with_mtime: list[tuple[Path, float]] = []
        for session in session_dirs:
            messages_path = session / MESSAGES_FILENAME
            if not messages_path.is_file():
                continue
            try:
                mtime = messages_path.stat().st_mtime
                sessions_with_mtime.append((session, mtime))
            except OSError:
                continue

        if not sessions_with_mtime:
            return None

        sessions_with_mtime.sort(key=lambda x: x[1], reverse=True)

        for session, _mtime in sessions_with_mtime:
            if SessionLoader._is_valid_session(session):
                return session

        return None

    @staticmethod
    def find_latest_session(config: SessionLoggingConfig) -> Path | None:
        save_dir = Path(config.save_dir)
        if not save_dir.exists():
            return None

        pattern = f"{config.session_prefix}_*"
        session_dirs = list(save_dir.glob(pattern))

        return SessionLoader.latest_session(session_dirs)

    @staticmethod
    def find_session_by_id(
        session_id: str, config: SessionLoggingConfig
    ) -> Path | None:
        matches = SessionLoader._find_session_dirs_by_short_id(session_id, config)

        return SessionLoader.latest_session(matches)

    @staticmethod
    def does_session_exist(
        session_id: str, config: SessionLoggingConfig
    ) -> Path | None:
        for session_dir in SessionLoader._find_session_dirs_by_short_id(
            session_id, config
        ):
            if (session_dir / MESSAGES_FILENAME).is_file():
                return session_dir
        return None

    @staticmethod
    def _find_session_dirs_by_short_id(
        session_id: str, config: SessionLoggingConfig
    ) -> list[Path]:
        save_dir = Path(config.save_dir)
        if not save_dir.exists():
            return []

        short_id = session_id[:8]
        return list(save_dir.glob(f"{config.session_prefix}_*_{short_id}"))

    @staticmethod
    def load_session(filepath: Path) -> tuple[list[LLMMessage], dict[str, Any]]:
        # Load session messages from MESSAGES_FILENAME
        messages_filepath = filepath / MESSAGES_FILENAME

        try:
            with messages_filepath.open("r", encoding="utf-8", errors="ignore") as f:
                content = f.readlines()
        except Exception as e:
            raise ValueError(
                f"Error reading session messages at {filepath}: {e}"
            ) from e

        if not content:
            raise ValueError(
                f"Session messages file is empty (may have been corrupted by interruption): "
                f"{filepath}"
            )

        try:
            data = [json.loads(line) for line in content]
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Session messages contain invalid JSON (may have been corrupted): "
                f"{filepath}\nDetails: {e}"
            ) from e

        messages = [
            LLMMessage.model_validate(msg) for msg in data if msg["role"] != "system"
        ]

        # Load session metadata from METADATA_FILENAME
        metadata_filepath = filepath / METADATA_FILENAME

        if metadata_filepath.exists():
            try:
                with metadata_filepath.open(
                    "r", encoding="utf-8", errors="ignore"
                ) as f:
                    metadata = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Session metadata contains invalid JSON (may have been corrupted): "
                    f"{filepath}\nDetails: {e}"
                ) from e
        else:
            metadata = {}

        return messages, metadata

    @staticmethod
    def load_threads(filepath: Path) -> ThreadManager | None:
        """Load thread manager state from session directory.

        Args:
            filepath: Path to session directory

        Returns:
            ThreadManager instance if threads.json exists, None otherwise
        """
        from vibe.core.session.thread_manager import ThreadManager

        threads_filepath = filepath / THREADS_FILENAME

        if not threads_filepath.exists():
            return None

        try:
            with threads_filepath.open("r", encoding="utf-8", errors="ignore") as f:
                threads_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            # If threads file is corrupted, return None to use default main thread
            return None

        try:
            return ThreadManager.deserialize(threads_data)
        except Exception:
            # If deserialization fails, return None to use default main thread
            return None

    @staticmethod
    def list_sessions_with_threads(
        config: SessionLoggingConfig, limit: int = 10
    ) -> list[dict[str, Any]]:
        """List recent sessions that contain threads.

        Args:
            config: Session logging configuration
            limit: Maximum number of sessions to return

        Returns:
            List of dicts with session_dir, session_id, title, date,
            and threads info, sorted by recency (newest first).
        """
        save_dir = Path(config.save_dir)
        if not save_dir.exists():
            return []

        pattern = f"{config.session_prefix}_*"
        session_dirs = list(save_dir.glob(pattern))

        results: list[dict[str, Any]] = []
        for session_dir in session_dirs:
            threads_path = session_dir / THREADS_FILENAME
            if not threads_path.is_file():
                continue

            # Read threads data
            try:
                with threads_path.open("r", encoding="utf-8", errors="ignore") as f:
                    threads_data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            threads_info = threads_data.get("threads", {})
            if not threads_info:
                continue

            # Read metadata for title and date
            title = "Untitled"
            date = ""
            mtime = 0.0
            metadata_path = session_dir / METADATA_FILENAME
            if metadata_path.is_file():
                try:
                    with metadata_path.open(
                        "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        metadata = json.load(f)
                    title = metadata.get("title", "Untitled")
                    date = metadata.get("start_time", "")
                    mtime = metadata_path.stat().st_mtime
                except (OSError, json.JSONDecodeError):
                    pass

            # Extract session_id from threads data or dir name
            session_id = threads_data.get("session_id", session_dir.name)

            thread_summaries = []
            for name, bdata in threads_info.items():
                thread_summaries.append(
                    {
                        "name": name,
                        "messages": len(bdata.get("messages", [])),
                        "files": len(bdata.get("file_deltas", {})),
                        "description": bdata.get("description", ""),
                    }
                )

            results.append(
                {
                    "session_dir": str(session_dir),
                    "session_id": session_id,
                    "title": title,
                    "date": date,
                    "mtime": mtime,
                    "threads": thread_summaries,
                }
            )

        # Sort by recency
        results.sort(key=lambda x: x["mtime"], reverse=True)
        return results[:limit]

    @staticmethod
    def load_thread_from_session(
        session_dir: str, thread_name: str
    ) -> Thread | None:
        """Load a specific thread from a session directory.

        Args:
            session_dir: Path to the session directory
            thread_name: Name of the thread to load

        Returns:
            Thread instance if found, None otherwise
        """
        from vibe.core.session.thread import Thread

        threads_path = Path(session_dir) / THREADS_FILENAME
        if not threads_path.is_file():
            return None

        try:
            with threads_path.open("r", encoding="utf-8", errors="ignore") as f:
                threads_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

        thread_data = threads_data.get("threads", {}).get(thread_name)
        if thread_data is None:
            return None

        try:
            return Thread.model_validate(thread_data)
        except Exception:
            return None
