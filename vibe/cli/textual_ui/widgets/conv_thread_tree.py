"""Thread tree visualization widget for /threads --status command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from vibe.core.session.conv_thread_manager import ConvThreadManager


class ConvThreadTreeWidget(Static):
    """Display thread tree with ASCII art visualization."""

    def __init__(self, conv_thread_manager: ConvThreadManager) -> None:
        self._conv_thread_manager = conv_thread_manager
        content = self._render_tree()
        super().__init__(content, classes="thread-tree")

    def _render_tree(self) -> str:
        """Render thread tree as markdown-formatted text."""
        threads = self._conv_thread_manager.list_threads()
        active_name = self._conv_thread_manager.active_thread_name

        lines = ["## Thread Tree\n"]

        # Build parent-child relationships
        children_map: dict[str | None, list[str]] = {}
        for thread in threads:
            parent = thread.parent
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(thread.name)

        # Render tree starting from main (which has no parent)
        def render_thread(name: str, prefix: str = "", is_last: bool = True) -> None:
            thread = self._conv_thread_manager.get_thread(name)
            is_active = " **[active]**" if name == active_name else ""

            # Thread info
            msg_info = f"+{thread.total_messages} msgs" if thread.total_messages > 0 else "0 msgs"
            file_info = f"{thread.total_file_changes} files" if thread.total_file_changes > 0 else "0 files"

            # Tree structure
            if name == "main":
                lines.append(f"**{name}**{is_active} ({msg_info}, {file_info})")
            else:
                connector = "└─" if is_last else "├─"
                lines.append(f"{prefix}{connector} **{name}**{is_active} ({msg_info}, {file_info})")

            # Render children
            children = children_map.get(name, [])
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                child_prefix = prefix + ("   " if is_last else "│  ")
                render_thread(child, child_prefix, is_last_child)

        # Start rendering from main thread
        render_thread("main")

        return "\n".join(lines)
