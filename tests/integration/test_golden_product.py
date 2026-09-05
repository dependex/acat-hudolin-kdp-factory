"""Integration test for Golden Product 001."""
from pathlib import Path
from src.orchestrator.config import PipelineConfig
from src.orchestrator.pipeline import Pipeline
from src.orchestrator.state import Stage


def test_gp001_full_pipeline(tmp_path: Path):
    """Test full execution of Golden Product 001 pipeline."""
    config = PipelineConfig.load()
    # Direct outputs to test temporary directory to keep clean
    config.output_dir = tmp_path / "output"
    
    pipeline = Pipeline(config)
    pipeline.run("GP001", full=False)
    
    # Verify all stages transitioned
    stage_names = [e.stage for e in pipeline.state.history]
    assert Stage.HARVEST in stage_names
    assert Stage.ASSEMBLE in stage_names
    assert Stage.EDITORIAL in stage_names
    assert Stage.TYPESET in stage_names
    assert Stage.COVER in stage_names
    assert Stage.PREFLIGHT in stage_names
    assert Stage.PACKAGE in stage_names
    assert Stage.DELIVER in stage_names
    
    # Verify outputs generated
    assert (config.output_dir / "ACAT-KDP-GP001_manuscript.md").exists()
    assert (config.output_dir / "ACAT-KDP-GP001_editorial_report.json").exists()
    assert (config.output_dir / "ACAT-KDP-GP001_interior.typ").exists()
    assert (config.output_dir / "ACAT-KDP-GP001_cover.typ").exists()
    assert (config.output_dir / "ACAT-KDP-GP001_preflight_report.json").exists()
    assert (config.output_dir / "ACAT-KDP-GP001_kdp_package_manifest.json").exists()
    
    # Preflight validation status
    assert pipeline.preflight_report is not None
    assert pipeline.preflight_report.passed is True
