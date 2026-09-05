"""KDP Factory Pipeline Orchestrator.

Conducts the end-to-end book production pipeline:
Harvest -> Assemble -> Editorial -> Typeset -> Cover -> Preflight -> Package -> Deliver
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.table import Table

from .config import PipelineConfig
from .state import PipelineState, Stage
from ..connectors.book_dna.reader import BookDNAReader
from ..connectors.source_registry.registry import SourceRegistry
from ..engines.content_assembler.assembler import ContentAssembler, Manuscript
from ..engines.editorial.editor import EditorialEngine, EditorialReport
from ..engines.typesetter.typesetter import Typesetter, TypesetConfig
from ..engines.cover_gen.cover import CoverGenerator
from ..engines.preflight.preflight import PreflightEngine, PreflightReport
from ..adapters.typst.adapter import TypstAdapter
from ..adapters.drive.adapter import DriveAdapter

console = Console()


class Pipeline:
    """Main pipeline engine that coordinates all production stages."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.state = PipelineState()
        self.product_dir: Path = Path(".")
        self.book_dna: dict[str, Any] = {}
        self.product_id: str = ""
        self.sources: list[Any] = []
        self.manuscript: Manuscript | None = None
        self.editorial_report: EditorialReport | None = None
        self.interior_path: Path | None = None
        self.cover_path: Path | None = None
        self.preflight_report: PreflightReport | None = None

    def run(self, product_id: str, full: bool = False) -> None:
        """Execute the pipeline for a given product."""
        console.print(f"[bold green]KDP Factory[/] Starting pipeline for [bold cyan]{product_id}[/]")

        stages = [
            Stage.HARVEST,
            Stage.ASSEMBLE,
            Stage.EDITORIAL,
            Stage.TYPESET,
            Stage.COVER,
            Stage.PREFLIGHT,
            Stage.PACKAGE,
            Stage.DELIVER,
        ]

        for stage in stages:
            self.state.transition(stage)
            console.print(f"  [cyan]{stage.value.upper()}[/] ... ", end="")
            try:
                self._execute_stage(stage, product_id)
                console.print("[green]OK[/]")
            except Exception as e:
                console.print(f"[red]FAIL: {e}[/]")
                if not full:
                    raise
        
        self._print_summary(product_id)

    def _find_product_dir(self, product_id: str) -> Path:
        """Locate product directory matching product_id."""
        if not self.config.products_dir.exists():
            raise FileNotFoundError(f"Products directory not found: {self.config.products_dir}")

        direct = self.config.products_dir / product_id
        if direct.exists() and direct.is_dir():
            return direct

        for child in sorted(self.config.products_dir.iterdir()):
            if child.is_dir():
                if product_id.lower() in child.name.lower():
                    return child
                for dna_name in ("book_dna.yaml", "book_dna.yml"):
                    dna_file = child / dna_name
                    if dna_file.exists():
                        try:
                            data = yaml.safe_load(dna_file.read_text(encoding="utf-8"))
                            if data and str(data.get("id", "")).lower() == product_id.lower():
                                return child
                        except Exception:
                            pass
        raise FileNotFoundError(f"No product directory found for '{product_id}' in {self.config.products_dir}")

    def _execute_stage(self, stage: Stage, product_id: str) -> None:
        """Execute a single pipeline stage."""
        if stage == Stage.HARVEST:
            self._harvest(product_id)
        elif stage == Stage.ASSEMBLE:
            self._assemble(product_id)
        elif stage == Stage.EDITORIAL:
            self._editorial(product_id)
        elif stage == Stage.TYPESET:
            self._typeset(product_id)
        elif stage == Stage.COVER:
            self._cover(product_id)
        elif stage == Stage.PREFLIGHT:
            self._preflight(product_id)
        elif stage == Stage.PACKAGE:
            self._package(product_id)
        elif stage == Stage.DELIVER:
            self._deliver(product_id)

    def _harvest(self, product_id: str) -> None:
        self.product_dir = self._find_product_dir(product_id)
        reader = BookDNAReader(self.config.schemas_dir)
        self.book_dna = reader.load(self.product_dir)
        self.product_id = self.book_dna.get("id", product_id)
        registry = SourceRegistry(self.config.knowledge_dir)
        self.sources = registry.resolve_sources(self.book_dna.get("sources", []))

    def _assemble(self, product_id: str) -> None:
        assembler = ContentAssembler(self.config.knowledge_dir, self.config.templates_dir)
        self.manuscript = assembler.assemble(self.book_dna)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        md_file = self.config.output_dir / f"{self.product_id}_manuscript.md"
        md_file.write_text(self.manuscript.to_markdown(), encoding="utf-8")

    def _editorial(self, product_id: str) -> None:
        if not self.manuscript:
            raise ValueError("Manuscript has not been assembled")
        style_cfg = self.book_dna.get("stages", {}).get("editorial", {})
        editor = EditorialEngine(style_cfg)
        self.editorial_report = editor.review(self.manuscript)
        report_file = self.config.output_dir / f"{self.product_id}_editorial_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "passed": self.editorial_report.passed,
                "readability_score": self.editorial_report.readability_score,
                "word_count": self.editorial_report.word_count,
                "chapter_count": self.editorial_report.chapter_count,
                "error_count": self.editorial_report.error_count,
                "warning_count": self.editorial_report.warning_count,
                "issues": [
                    {
                        "severity": i.severity.value,
                        "category": i.category,
                        "message": i.message,
                        "chapter": i.chapter,
                        "line": i.line,
                        "suggestion": i.suggestion,
                    }
                    for i in self.editorial_report.issues
                ],
            }, f, indent=2, ensure_ascii=False)

    def _typeset(self, product_id: str) -> None:
        if not self.manuscript:
            raise ValueError("Manuscript has not been assembled")
        adapter = TypstAdapter()
        trim = self.book_dna.get("format", {}).get("trim_size", self.config.trim_size)
        typeset_cfg = TypesetConfig.for_trim(trim)
        typesetter = Typesetter(adapter, typeset_cfg)
        self.interior_path = typesetter.typeset(self.manuscript, self.config.output_dir)

    def _cover(self, product_id: str) -> None:
        cover_gen = CoverGenerator(self.config.templates_dir)
        pages = self.manuscript.estimated_pages if self.manuscript else 100
        self.cover_path = cover_gen.generate(self.book_dna, pages, self.config.output_dir)
        adapter = TypstAdapter()
        if adapter.validate() and self.cover_path.suffix == ".typ":
            try:
                pdf_out = self.cover_path.with_suffix(".pdf")
                adapter.render(self.cover_path.read_text(encoding="utf-8"), TypesetConfig(), pdf_out)
            except Exception as e:
                console.print(f"[yellow]Cover compilation warning: {e}[/]")

    def _preflight(self, product_id: str) -> None:
        engine = PreflightEngine()
        self.preflight_report = engine.validate(self.book_dna, self.config.output_dir)
        report_file = self.config.output_dir / f"{self.product_id}_preflight_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "passed": self.preflight_report.passed,
                "summary": self.preflight_report.summary,
                "checks": [
                    {
                        "name": c.name,
                        "status": c.status.value,
                        "message": c.message,
                        "details": c.details,
                    }
                    for c in self.preflight_report.checks
                ],
            }, f, indent=2, ensure_ascii=False)

    def _package(self, product_id: str) -> None:
        manifest = {
            "product_id": self.product_id,
            "title": self.book_dna.get("title", ""),
            "subtitle": self.book_dna.get("subtitle", ""),
            "format": self.book_dna.get("format", {}),
            "metadata": self.book_dna.get("metadata", {}),
            "artifacts": {
                "manuscript_md": f"{self.product_id}_manuscript.md",
                "interior_pdf": f"{self.product_id}_interior.pdf",
                "cover_typ": f"{self.product_id}_cover.typ",
                "cover_pdf": f"{self.product_id}_cover.pdf",
                "editorial_report": f"{self.product_id}_editorial_report.json",
                "preflight_report": f"{self.product_id}_preflight_report.json",
            },
            "kdp_ready": self.preflight_report.passed if self.preflight_report else False,
        }
        manifest_file = self.config.output_dir / f"{self.product_id}_kdp_package_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def _deliver(self, product_id: str) -> None:
        if self.config.drive_folder_id:
            try:
                adapter = DriveAdapter(self.config.drive_folder_id)
                adapter.upload_directory(self.config.output_dir)
            except Exception as e:
                console.print(f"[yellow]Drive delivery warning: {e}[/]")

    def _print_summary(self, product_id: str) -> None:
        """Print pipeline execution summary."""
        table = Table(title=f"KDP Factory Pipeline Summary: {product_id}")
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        for entry in self.state.history:
            status_style = "green" if entry.status == "done" else "red"
            table.add_row(entry.stage.value, f"[{status_style}]{entry.status}[/]", entry.duration)
        console.print(table)


@click.command()
@click.option("--product", required=True, help="Product ID (e.g., GP001, GP001-diario-del-club, ACAT-KDP-GP001)")
@click.option("--full", is_flag=True, help="Continue on errors")
def main(product: str, full: bool) -> None:
    """ACAT Hudolin KDP Factory - Book Production Pipeline."""
    config = PipelineConfig.load()
    pipeline = Pipeline(config)
    pipeline.run(product, full=full)


if __name__ == "__main__":
    main()
