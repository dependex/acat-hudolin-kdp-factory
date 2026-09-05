# Architecture

## Design Principles
1. Drive = Source of Truth - All knowledge lives on Google Drive
2. GitHub = Engine - Code, templates, and CI/CD live here
3. No Competing Knowledge - Never duplicate Drive content
4. Adapter Pattern - Swap typesetting engines without changing pipeline
5. Book DNA - Every product has a declarative blueprint (YAML)

## Pipeline Flow
Drive -> Source Registry -> Content Assembler -> Editorial QA -> Typesetter (Typst/Paged.js) -> Cover Gen -> KDP Preflight -> Package -> Drive Archive

## Module Contracts
Each engine implements: validate_input, execute, rollback
