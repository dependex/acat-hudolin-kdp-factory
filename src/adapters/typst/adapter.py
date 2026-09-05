"""Typst Adapter.

Wraps the Typst binary for PDF rendering.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ...engines.typesetter.typesetter import TypesetConfig


class TypstAdapter:
    """Adapter for the Typst typesetting engine."""

    def __init__(self) -> None:
        self._binary: str | None = shutil.which("typst")
        if not self._binary:
            local_appdata = Path(os.environ.get("LOCALAPPDATA", ""))
            candidates = [
                local_appdata / "Microsoft" / "WinGet" / "Links" / "typst.exe",
                local_appdata / "Programs" / "typst" / "typst.exe",
            ]
            for c in candidates:
                if c.exists():
                    self._binary = str(c)
                    break
            if not self._binary and local_appdata.exists():
                pkg_dir = local_appdata / "Microsoft" / "WinGet" / "Packages"
                if pkg_dir.exists():
                    found = list(pkg_dir.glob("**/typst.exe"))
                    if found:
                        self._binary = str(found[0])

    def validate(self) -> bool:
        """Check if Typst is available."""
        return self._binary is not None

    def render(self, source: str, config: TypesetConfig, output: Path) -> Path:
        """Render Typst source to PDF."""
        # Write source to temporary .typ file
        typ_file = output.with_suffix(".typ")
        typ_file.write_text(source, encoding="utf-8")

        if not self._binary or not self.validate():
            # Fallback: just save the source, warn about missing binary
            return typ_file

        # Run Typst compile
        result = subprocess.run(
            [self._binary, "compile", str(typ_file), str(output)],
            capture_output=True, text=True, timeout=120, check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Typst compilation failed: {result.stderr}")

        return output
