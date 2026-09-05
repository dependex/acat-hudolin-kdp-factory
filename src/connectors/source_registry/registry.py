"""Source Registry Connector.

Maps source references from Book DNA to actual file locations
on Drive or local filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SourceEntry:
    """A resolved source entry."""
    ref: str
    source_type: str
    local_path: Path | None = None
    drive_id: str = ""
    resolved: bool = False


class SourceRegistry:
    """Resolves source references to actual file paths."""

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir
        self._registry: dict[str, SourceEntry] = {}

    def resolve_sources(self, sources: list[dict[str, Any]]) -> list[SourceEntry]:
        """Resolve a list of source references."""
        entries = []
        for source in sources:
            entry = self._resolve_single(source)
            entries.append(entry)
            self._registry[entry.ref] = entry
        return entries

    def _resolve_single(self, source: dict[str, Any]) -> SourceEntry:
        """Resolve a single source reference."""
        ref = source.get("ref", "")
        source_type = source.get("type", "")
        drive_id = source.get("drive_id", "")

        # Try to find local path
        local_path = self._find_local(ref)

        return SourceEntry(
            ref=ref,
            source_type=source_type,
            local_path=local_path,
            drive_id=drive_id,
            resolved=local_path is not None or bool(drive_id),
        )

    def _find_local(self, ref: str) -> Path | None:
        """Search knowledge directory for a matching file or folder."""
        if not self.knowledge_dir.exists():
            return None

        # Direct match
        for pattern in [ref, ref.lower(), ref.replace(" ", "_")]:
            for item in self.knowledge_dir.rglob(f"*{pattern}*"):
                return item

        return None
