# ACAT Hudolin KDP Factory

[![CI](https://github.com/dependex/acat-hudolin-kdp-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/dependex/acat-hudolin-kdp-factory/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

> **Autonomous Book Production Pipeline**
> Transforms HUDOLIN KNOWLEDGE 360 into print-ready KDP packages

## Pipeline

```
HUDOLIN KNOWLEDGE 360
  -> PRODUCT DNA -> MANUSCRIPT -> EDITORIAL QA
  -> TYPESET 6x9 -> PDF/EPUB -> KDP PREFLIGHT
  -> COVER -> PACKAGE -> DRIVE
```

## Architecture

- **src/orchestrator/** - Pipeline conductor and state machine
- **src/engines/** - Content assembler, editorial QA, typesetter, cover gen, preflight
- **src/adapters/** - Drive, Typst, Paged.js, KDP connectors
- **src/connectors/** - Knowledge graph, source registry, Book DNA readers
- **templates/** - 6x9 book templates, covers, typography
- **schemas/** - JSON schemas for Book DNA, products, pipeline config
- **products/** - Individual book products (GP001 = Diario del Club)

## Golden Product 001: Diario del Club

**ID**: ACAT-KDP-GP001
**Titolo**: Diario del Club - Guida Pratica per il Servitore-Insegnante
**Formato**: 6x9 pollici, b/n interni, copertina a colori

## Quick Start

```bash
git clone https://github.com/dependex/acat-hudolin-kdp-factory.git
cd acat-hudolin-kdp-factory
pip install -e ".[dev]"
python -m src.orchestrator.pipeline --product GP001
pytest tests/
```

## Constraints

- Drive = Source of Truth documentale. GitHub = motore operativo.
- NON creare Knowledge concorrente.
- Un repository senza licenza chiara NON entra nel core.

## License

[AGPL-3.0](LICENSE)

---
*ACAT Hudolin KDP Factory - Dalla conoscenza al libro, automaticamente.*
