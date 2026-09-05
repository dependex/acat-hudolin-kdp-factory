"""Typesetter Engine.

Renders manuscripts into print-ready PDFs using Typst or Paged.js.
Supports 6x9 inch KDP format with proper margins, typography, and pagination.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class TypesetConfig:
    """Typesetting configuration for KDP books."""
    trim_width: float = 6.0    # inches
    trim_height: float = 9.0   # inches
    margin_top: float = 0.75
    margin_bottom: float = 0.75
    margin_inside: float = 0.875  # gutter
    margin_outside: float = 0.625
    bleed: float = 0.125
    font_body: str = "Libertinus Serif"
    font_heading: str = "Libertinus Sans"
    font_size: str = "11pt"
    line_height: float = 1.4

    @classmethod
    def for_trim(cls, trim_size: str) -> TypesetConfig:
        configs = {
            "6x9": cls(),
            "5.5x8.5": cls(trim_width=5.5, trim_height=8.5, margin_inside=0.75),
            "5x8": cls(trim_width=5.0, trim_height=8.0, margin_inside=0.75, margin_outside=0.5),
        }
        return configs.get(trim_size, cls())


class TypesetterAdapter(Protocol):
    """Protocol for typesetting backend adapters."""
    def render(self, source: str, config: TypesetConfig, output: Path) -> Path: ...
    def validate(self) -> bool: ...


class Typesetter:
    """Main typesetter that delegates to backend adapters."""

    def __init__(self, adapter: TypesetterAdapter, config: TypesetConfig) -> None:
        self.adapter = adapter
        self.config = config

    def typeset(self, manuscript: Any, output_dir: Path) -> Path:
        """Typeset a manuscript into a PDF."""
        output_dir.mkdir(parents=True, exist_ok=True)
        source = self._generate_source(manuscript)
        output_path = output_dir / f"{manuscript.product_id}_interior.pdf"
        return self.adapter.render(source, self.config, output_path)

    def _generate_source(self, manuscript: Any) -> str:
        """Generate typesetting source from manuscript."""
        return self._generate_typst_source(manuscript)

    def _generate_typst_source(self, manuscript: Any) -> str:
        """Generate Typst source code."""
        c = self.config
        parts = [
            f'''#set page(
  width: {c.trim_width}in,
  height: {c.trim_height}in,
  margin: (
    top: {c.margin_top}in,
    bottom: {c.margin_bottom}in,
    inside: {c.margin_inside}in,
    outside: {c.margin_outside}in,
  ),
)

#set text(
  font: "{c.font_body}",
  size: {c.font_size},
)

#set par(leading: {c.line_height}em)

#show heading.where(level: 1): set text(font: "{c.font_heading}", size: 18pt)
#show heading.where(level: 2): set text(font: "{c.font_heading}", size: 14pt)
''',
        ]

        # Title page
        parts.append(f"""
#align(center + horizon)[
  #text(size: 24pt, font: "{c.font_heading}", weight: "bold")[{manuscript.title}]
  #v(1em)
  #text(size: 16pt, style: "italic")[{manuscript.subtitle}]
  #v(3em)
  #text(size: 12pt)[ACAT Hudolin]
]
#pagebreak()
""")

        # Copyright page
        parts.append("""
#set text(size: 9pt)
Copyright ACAT Hudolin. Tutti i diritti riservati.

Metodo Hudolin per i Club Alcologici Territoriali.

Pubblicato tramite DEPENDEX KDP Factory.
#pagebreak()
""")

        # Table of contents
        parts.append("#outline(title: [Indice], indent: 1em)\n#pagebreak()\n")

        # Chapters
        for chapter in manuscript.chapters:
            typst_content = self._markdown_to_typst(chapter.content)
            parts.append(f"""
= Capitolo {chapter.number}: {chapter.title}
#v(1em)

{typst_content}

#pagebreak()
""")

        return "\n".join(parts)

    def _markdown_to_typst(self, md: str) -> str:
        """Convert standard markdown syntax into clean Typst markup."""
        import re
        lines = []
        for line in md.splitlines():
            # Convert headings:
            if line.startswith("#### "):
                line = "==== " + line[5:]
            elif line.startswith("### "):
                line = "=== " + line[4:]
            elif line.startswith("## "):
                line = "== " + line[3:]
            elif line.startswith("# "):
                line = "= " + line[2:]

            # Convert bold **text** to *text*
            line = re.sub(r"\*\*(.+?)\*\*", r"*\1*", line)

            # Escape hashes (like hex colors #FFD166, hashtags, etc) so Typst treats them as literal characters
            line = re.sub(r"#([0-9A-Fa-f]{3,8})\b", r"\\#\1", line)
            line = re.sub(r"(?<!\\)#(?!set|show|let|align|text|v|h|pagebreak|line|rect|box|place|rotate|image|link|outline|list|enum)", r"\\#", line)

            # Convert numbered lists 1. item to + item
            line = re.sub(r"^\s*\d+\.\s+", "+ ", line)

            lines.append(line)
        return "\n".join(lines)
