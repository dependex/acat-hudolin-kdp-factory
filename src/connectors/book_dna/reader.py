"""Book DNA Reader.

Loads, validates, and parses Book DNA YAML files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore[assignment]


class BookDNAReader:
    """Reads and validates Book DNA configuration files."""

    def __init__(self, schemas_dir: Path) -> None:
        self.schemas_dir = schemas_dir

    def load(self, product_dir: Path) -> dict[str, Any]:
        """Load Book DNA from a product directory."""
        dna_path = product_dir / "book_dna.yaml"
        if not dna_path.exists():
            dna_path = product_dir / "book_dna.yml"
        if not dna_path.exists():
            raise FileNotFoundError(f"No book_dna.yaml found in {product_dir}")

        with open(dna_path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        self.validate(data)
        return data

    def validate(self, data: dict[str, Any]) -> None:
        """Validate Book DNA against JSON Schema."""
        schema_path = self.schemas_dir / "book_dna.schema.json"
        if not schema_path.exists():
            return  # Skip validation if schema not found

        if jsonschema is None:
            return  # Skip if jsonschema not installed

        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        jsonschema.validate(instance=data, schema=schema)

    def get_product_id(self, data: dict[str, Any]) -> str:
        """Extract product ID from Book DNA."""
        return str(data.get("id", "UNKNOWN"))

    def get_sources(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract source references."""
        return list(data.get("sources", []))
