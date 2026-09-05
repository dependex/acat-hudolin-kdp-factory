"""Tests for pipeline configuration."""
from src.orchestrator.config import PipelineConfig


def test_default_config():
    config = PipelineConfig.load()
    assert config.typesetter == "typst"
    assert config.trim_size == "6x9"
    assert config.color_interior is False
