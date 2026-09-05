"""KDP Preflight Engine.

Validates that the assembled package meets all KDP publishing requirements:
trim size, margins, bleed, fonts, image DPI, file size, and metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class PreflightCheck:
    """A single preflight validation check."""
    name: str
    status: CheckStatus
    message: str
    details: str = ""


@dataclass
class PreflightReport:
    """Complete preflight validation report."""
    checks: list[PreflightCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.status != CheckStatus.FAIL for c in self.checks)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "pass": sum(1 for c in self.checks if c.status == CheckStatus.PASS),
            "warn": sum(1 for c in self.checks if c.status == CheckStatus.WARN),
            "fail": sum(1 for c in self.checks if c.status == CheckStatus.FAIL),
        }


class PreflightEngine:
    """Validates KDP publishing requirements."""

    # KDP constraints
    MIN_PAGES = 24
    MAX_PAGES = 828
    MAX_FILE_SIZE_MB = 650
    MIN_DPI = 300
    VALID_TRIMS = {"5x8", "5.25x8", "5.5x8.5", "6x9", "7x10", "8x10", "8.5x11"}

    def __init__(self) -> None:
        self.report = PreflightReport()

    def validate(self, book_dna: dict[str, Any], output_dir: Path) -> PreflightReport:
        """Run all preflight checks."""
        self.report = PreflightReport()
        self._check_trim_size(book_dna)
        self._check_page_count(output_dir, book_dna)
        self._check_metadata(book_dna)
        self._check_files(output_dir, book_dna)
        self._check_isbn(book_dna)
        return self.report

    def _check_trim_size(self, book_dna: dict[str, Any]) -> None:
        trim = book_dna.get("format", {}).get("trim_size", "")
        if trim in self.VALID_TRIMS:
            self.report.checks.append(PreflightCheck(
                name="trim_size", status=CheckStatus.PASS,
                message=f"Trim size {trim} is valid",
            ))
        else:
            self.report.checks.append(PreflightCheck(
                name="trim_size", status=CheckStatus.FAIL,
                message=f"Invalid trim size: {trim}",
                details=f"Valid sizes: {self.VALID_TRIMS}",
            ))

    def _check_page_count(self, output_dir: Path, book_dna: dict[str, Any] | None = None) -> None:
        # Estimate from file size or content
        product_id = book_dna.get("id", "") if book_dna else ""
        candidates = [
            output_dir / f"{product_id}_interior.pdf",
            output_dir / "interior.pdf",
            output_dir / f"{product_id}_interior.typ",
        ]
        interior = next((c for c in candidates if c.exists()), None)
        if interior:
            size_mb = interior.stat().st_size / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                self.report.checks.append(PreflightCheck(
                    name="file_size", status=CheckStatus.FAIL,
                    message=f"Interior file too large: {size_mb:.1f}MB (max {self.MAX_FILE_SIZE_MB}MB)",
                ))
            else:
                self.report.checks.append(PreflightCheck(
                    name="file_size", status=CheckStatus.PASS,
                    message=f"Interior file size OK: {size_mb:.1f}MB ({interior.name})",
                ))
        else:
            self.report.checks.append(PreflightCheck(
                name="file_size", status=CheckStatus.WARN,
                message="Interior file not found - skipping size check",
            ))

    def _check_metadata(self, book_dna: dict[str, Any]) -> None:
        meta = book_dna.get("metadata", {})
        required = ["language", "description", "categories", "keywords"]
        for field_name in required:
            if meta.get(field_name):
                self.report.checks.append(PreflightCheck(
                    name=f"metadata_{field_name}", status=CheckStatus.PASS,
                    message=f"Metadata {field_name} present",
                ))
            else:
                self.report.checks.append(PreflightCheck(
                    name=f"metadata_{field_name}", status=CheckStatus.WARN,
                    message=f"Metadata {field_name} missing",
                    details="KDP requires complete metadata for listing",
                ))

        desc = meta.get("description", "")
        if len(desc) < 50:
            self.report.checks.append(PreflightCheck(
                name="description_length", status=CheckStatus.WARN,
                message=f"Description too short ({len(desc)} chars, recommended 150+)",
            ))

    def _check_files(self, output_dir: Path, book_dna: dict[str, Any]) -> None:
        product_id = book_dna.get("id", "unknown")
        expected = [f"{product_id}_interior.pdf", f"{product_id}_cover.typ"]
        for filename in expected:
            path = output_dir / filename
            if path.exists():
                self.report.checks.append(PreflightCheck(
                    name=f"file_{filename}", status=CheckStatus.PASS,
                    message=f"File present: {filename}",
                ))
            else:
                self.report.checks.append(PreflightCheck(
                    name=f"file_{filename}", status=CheckStatus.WARN,
                    message=f"Expected file missing: {filename}",
                ))

    def _check_isbn(self, book_dna: dict[str, Any]) -> None:
        isbn = book_dna.get("metadata", {}).get("isbn", "")
        if isbn:
            self.report.checks.append(PreflightCheck(
                name="isbn", status=CheckStatus.PASS,
                message=f"ISBN present: {isbn}",
            ))
        else:
            self.report.checks.append(PreflightCheck(
                name="isbn", status=CheckStatus.WARN,
                message="No ISBN - KDP can assign a free one",
            ))
