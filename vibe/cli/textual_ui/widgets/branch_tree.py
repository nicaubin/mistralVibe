"""Branch tree visualization widget for /branches --status command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from vibe.core.session.branch_manager import BranchManager


class BranchTreeWidget(Static):
    """Display branch tree with ASCII art visualization."""

    def __init__(self, branch_manager: BranchManager) -> None:
        self._branch_manager = branch_manager
        content = self._render_tree()
        super().__init__(content, classes="branch-tree")

    def _render_tree(self) -> str:
        """Render branch tree as markdown-formatted text."""
        branches = self._branch_manager.list_branches()
        active_name = self._branch_manager.active_branch_name

        lines = ["## Branch Tree\n"]

        # Build parent-child relationships
        children_map: dict[str | None, list[str]] = {}
        for branch in branches:
            parent = branch.parent
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(branch.name)

        # Render tree starting from main (which has no parent)
        def render_branch(name: str, prefix: str = "", is_last: bool = True) -> None:
            branch = self._branch_manager.get_branch(name)
            is_active = " **[active]**" if name == active_name else ""

            # Branch info
            msg_info = f"+{branch.total_messages} msgs" if branch.total_messages > 0 else "0 msgs"
            file_info = f"{branch.total_file_changes} files" if branch.total_file_changes > 0 else "0 files"

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
                render_branch(child, child_prefix, is_last_child)

        # Start rendering from main branch
        render_branch("main")

        # Add snapshots section if any exist
        snapshots = self._branch_manager.list_snapshots()
        if snapshots:
            lines.append("\n## Snapshots\n")
            for snapshot in snapshots:
                desc = f": {snapshot.description}" if snapshot.description else ""
                lines.append(
                    f"- **{snapshot.name}** ({snapshot.branch_name} @ msg #{snapshot.message_id}){desc}"
                )

        return "\n".join(lines)
