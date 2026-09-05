"""Editorial Engine.

Performs quality assurance on manuscripts: style checking,
tone analysis, structural validation, and readability scoring.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class EditorialIssue:
    """A single editorial issue found in the manuscript."""
    severity: Severity
    category: str
    message: str
    chapter: int | None = None
    line: int | None = None
    suggestion: str = ""


@dataclass
class EditorialReport:
    """Complete editorial review report."""
    issues: list[EditorialIssue] = field(default_factory=list)
    readability_score: float = 0.0
    word_count: int = 0
    chapter_count: int = 0
    passed: bool = False

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


class EditorialEngine:
    """Performs editorial QA on manuscripts."""

    # Italian readability - simplified Gulpease index factors
    GULPEASE_THRESHOLD = 40  # Minimum acceptable score

    def __init__(self, style_config: dict[str, Any] | None = None) -> None:
        self.config = style_config or {}
        self.tone = self.config.get("tone", "professionale, empatico, pratico")
        self.audience = self.config.get("audience", "servitori-insegnanti CAT")

    def review(self, manuscript: Any) -> EditorialReport:
        """Run full editorial review on a manuscript."""
        report = EditorialReport(
            word_count=manuscript.total_words,
            chapter_count=len(manuscript.chapters),
        )

        for chapter in manuscript.chapters:
            self._check_chapter_structure(chapter, report)
            self._check_style(chapter, report)
            self._check_readability(chapter, report)

        self._check_manuscript_structure(manuscript, report)
        report.passed = report.error_count == 0
        return report

    def _check_chapter_structure(self, chapter: Any, report: EditorialReport) -> None:
        """Validate chapter structure."""
        if chapter.word_count < 100:
            report.issues.append(EditorialIssue(
                severity=Severity.WARNING,
                category="structure",
                message=f"Capitolo {chapter.number} troppo corto ({chapter.word_count} parole)",
                chapter=chapter.number,
                suggestion="Espandere il contenuto ad almeno 500 parole",
            ))

        if chapter.word_count > 8000:
            report.issues.append(EditorialIssue(
                severity=Severity.WARNING,
                category="structure",
                message=f"Capitolo {chapter.number} troppo lungo ({chapter.word_count} parole)",
                chapter=chapter.number,
                suggestion="Considerare di dividere in sotto-capitoli",
            ))

        if not chapter.title or len(chapter.title) < 3:
            report.issues.append(EditorialIssue(
                severity=Severity.ERROR,
                category="structure",
                message=f"Capitolo {chapter.number} senza titolo valido",
                chapter=chapter.number,
            ))

    def _check_style(self, chapter: Any, report: EditorialReport) -> None:
        """Check writing style and tone."""
        content = chapter.content.lower()

        # Check for informal language in professional context
        informal_words = ["roba", "cose", "tipo", "praticamente", "fondamentalmente"]
        for word in informal_words:
            if word in content:
                report.issues.append(EditorialIssue(
                    severity=Severity.INFO,
                    category="style",
                    message=f"Parola informale \"{word}\" nel capitolo {chapter.number}",
                    chapter=chapter.number,
                    suggestion=f"Sostituire \"{word}\" con un termine piu preciso",
                ))

        # Check for passive voice overuse (simplified Italian check)
        passive_count = len(re.findall(r"\b(viene|vengono|stato|stata|stati|state)\s+\w+[ato|uto|ito]", content))
        if passive_count > 10:
            report.issues.append(EditorialIssue(
                severity=Severity.INFO,
                category="style",
                message=f"Uso eccessivo del passivo nel capitolo {chapter.number} ({passive_count} occorrenze)",
                chapter=chapter.number,
                suggestion="Preferire la forma attiva per chiarezza",
            ))

    def _check_readability(self, chapter: Any, report: EditorialReport) -> None:
        """Calculate readability score (simplified Gulpease)."""
        text = chapter.content
        sentences = len(re.split(r"[.!?]+", text))
        words = len(text.split())
        chars = len(re.sub(r"\s", "", text))

        if words > 0 and sentences > 0:
            gulpease = 89 + (300 * sentences - 10 * chars) / words
            if gulpease < self.GULPEASE_THRESHOLD:
                report.issues.append(EditorialIssue(
                    severity=Severity.WARNING,
                    category="readability",
                    message=f"Leggibilita bassa nel capitolo {chapter.number} (Gulpease: {gulpease:.0f})",
                    chapter=chapter.number,
                    suggestion="Semplificare frasi lunghe e ridurre parole complesse",
                ))
            report.readability_score = max(report.readability_score, gulpease)

    def _check_manuscript_structure(self, manuscript: Any, report: EditorialReport) -> None:
        """Validate overall manuscript structure."""
        if len(manuscript.chapters) < 3:
            report.issues.append(EditorialIssue(
                severity=Severity.ERROR,
                category="structure",
                message="Manoscritto con meno di 3 capitoli",
                suggestion="Un libro KDP richiede almeno 3 capitoli sostanziali",
            ))

        if manuscript.total_words < 5000:
            report.issues.append(EditorialIssue(
                severity=Severity.WARNING,
                category="structure",
                message=f"Manoscritto corto ({manuscript.total_words} parole)",
                suggestion="Il minimo consigliato per KDP e 10.000 parole",
            ))

        if not manuscript.front_matter:
            report.issues.append(EditorialIssue(
                severity=Severity.ERROR,
                category="structure",
                message="Mancano i preliminari (front matter)",
            ))
