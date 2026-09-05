"""Pipeline configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PipelineConfig:
    """Configuration for the KDP Factory pipeline."""
    
    products_dir: Path = field(default_factory=lambda: Path("products"))
    templates_dir: Path = field(default_factory=lambda: Path("templates"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    schemas_dir: Path = field(default_factory=lambda: Path("schemas"))
    
    # Engine settings
    typesetter: str = "typst"  # or "pagedjs"
    trim_size: str = "6x9"
    color_interior: bool = False
    
    # Drive connector
    drive_folder_id: str = ""
    
    @classmethod
    def load(cls, path: Path | None = None) -> PipelineConfig:
        """Load config from YAML file or defaults."""
        if path and path.exists():
            with open(path) as f:
                data: dict[str, Any] = yaml.safe_load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()
