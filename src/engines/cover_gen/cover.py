"""Cover Generator Engine.

Creates KDP-compliant book covers with proper dimensions,
spine width calculation, and bleed areas.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CoverDimensions:
    """KDP cover dimensions in inches."""
    trim_width: float
    trim_height: float
    spine_width: float
    bleed: float = 0.125
    wrap: float = 0.0  # For hardcover

    @property
    def full_width(self) -> float:
        return (self.trim_width * 2) + self.spine_width + (self.bleed * 2) + (self.wrap * 2)

    @property
    def full_height(self) -> float:
        return self.trim_height + (self.bleed * 2)

    @classmethod
    def calculate(
        cls, trim_width: float, trim_height: float,
        page_count: int, paper_type: str = "cream",
        binding: str = "paperback"
    ) -> CoverDimensions:
        """Calculate cover dimensions based on page count and paper type."""
        # KDP spine width formula
        ppi = {"white": 0.002252, "cream": 0.0025}
        spine = page_count * ppi.get(paper_type, 0.002252)
        wrap = 0.625 if binding == "hardcover" else 0.0
        return cls(
            trim_width=trim_width, trim_height=trim_height,
            spine_width=spine, wrap=wrap,
        )


class CoverGenerator:
    """Generates KDP-compliant book covers."""

    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir

    def generate(self, book_dna: dict[str, Any], page_count: int, output_dir: Path) -> Path:
        """Generate cover PDF from Book DNA."""
        fmt = book_dna.get("format", {})
        cover_config = book_dna.get("stages", {}).get("cover", {})
        colors = cover_config.get("colors", {})

        dims = CoverDimensions.calculate(
            trim_width=float(fmt.get("trim_size", "6x9").split("x")[0]),
            trim_height=float(fmt.get("trim_size", "6x9").split("x")[1]),
            page_count=page_count,
            paper_type=fmt.get("paper_type", "cream"),
            binding=fmt.get("binding", "paperback"),
        )

        source = self._generate_cover_source(book_dna, dims, colors)
        output_path = output_dir / f"{book_dna['id']}_cover.typ"
        output_path.write_text(source, encoding="utf-8")
        return output_path

    def _generate_cover_source(
        self, book_dna: dict[str, Any],
        dims: CoverDimensions, colors: dict[str, str],
    ) -> str:
        """Generate Typst source for the cover."""
        primary = colors.get("primary", "#2E7D32")
        secondary = colors.get("secondary", "#F57C00")
        bg = colors.get("background", "#FAFAFA")

        return f"""// KDP Cover - {book_dna["title"]}
// Full cover: {dims.full_width:.3f} x {dims.full_height:.3f} inches
// Spine width: {dims.spine_width:.3f} inches

#set page(
  width: {dims.full_width:.3f}in,
  height: {dims.full_height:.3f}in,
  margin: 0in,
)

#let primary = rgb("{primary}")
#let secondary = rgb("{secondary}")
#let bg = rgb("{bg}")

// Background
#rect(width: 100%, height: 100%, fill: bg)

// Front cover area (right side)
#place(right + horizon, dx: -{dims.bleed}in)[
  #box(width: {dims.trim_width}in, height: {dims.trim_height}in)[
    #align(center + horizon)[
      #text(size: 28pt, fill: primary, weight: "bold")[{book_dna["title"]}]
      #v(0.5em)
      #text(size: 16pt, fill: secondary, style: "italic")[{book_dna.get("subtitle", "")}]
      #v(3em)
      #line(length: 40%, stroke: secondary)
      #v(1em)
      #text(size: 12pt, fill: primary)[ACAT Hudolin]
      #v(5em)
      #text(size: 10pt, fill: luma(120))[DEPENDEX]
    ]
  ]
]

// Spine
#place(center + horizon)[
  #rotate(-90deg)[
    #text(size: 9pt, fill: primary, weight: "bold")[{book_dna["title"]} — ACAT Hudolin]
  ]
]

// Back cover area (left side)
#place(left + bottom, dx: {dims.bleed}in, dy: -{dims.bleed + 1.0}in)[
  #box(width: {dims.trim_width - 1.0}in, inset: 0.5in)[
    #text(size: 10pt, fill: luma(80))[
      {book_dna.get("metadata", {}).get("description", "")}
    ]
  ]
]
"""
