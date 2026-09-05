"""KDP Factory Pipeline Orchestrator.

Conducts the end-to-end book production pipeline:
Harvest -> Assemble -> Editorial -> Typeset -> Cover -> Preflight -> Package -> Deliver
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from .config import PipelineConfig
from .state import PipelineState, Stage

console = Console()


class Pipeline:
    """Main pipeline engine that coordinates all production stages."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.state = PipelineState()

    def run(self, product_id: str, full: bool = False) -> None:
        """Execute the pipeline for a given product."""
        console.print(f"[bold green]KDP Factory[/] Starting pipeline for {product_id}")

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
            console.print(f"  [cyan]{stage.value}[/] ... ", end="")
            try:
                self._execute_stage(stage, product_id)
                console.print("[green]OK[/]")
            except Exception as e:
                console.print(f"[red]FAIL: {e}[/]")
                if not full:
                    raise
        
        self._print_summary(product_id)

    def _execute_stage(self, stage: Stage, product_id: str) -> None:
        """Execute a single pipeline stage."""
        # Stage dispatch - each engine handles its own logic
        pass  # TODO: wire up engines

    def _print_summary(self, product_id: str) -> None:
        """Print pipeline execution summary."""
        table = Table(title=f"Pipeline Summary: {product_id}")
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        for entry in self.state.history:
            table.add_row(entry.stage.value, entry.status, entry.duration)
        console.print(table)


@click.command()
@click.option("--product", required=True, help="Product ID (e.g., GP001)")
@click.option("--full", is_flag=True, help="Continue on errors")
def main(product: str, full: bool) -> None:
    """ACAT Hudolin KDP Factory - Book Production Pipeline."""
    config = PipelineConfig.load()
    pipeline = Pipeline(config)
    pipeline.run(product, full=full)


if __name__ == "__main__":
    main()
