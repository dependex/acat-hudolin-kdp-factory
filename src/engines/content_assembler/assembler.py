"""Content Assembler Engine.

Reads sources from the knowledge base and structures them into
a manuscript following the Book DNA blueprint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Chapter:
    """A single chapter in the manuscript."""
    number: int
    title: str
    content: str
    word_count: int = 0
    source_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.word_count = len(self.content.split())


@dataclass
class Manuscript:
    """Assembled manuscript ready for editorial review."""
    product_id: str
    title: str
    subtitle: str
    chapters: list[Chapter] = field(default_factory=list)
    front_matter: str = ""
    back_matter: str = ""

    @property
    def total_words(self) -> int:
        return sum(ch.word_count for ch in self.chapters)

    @property
    def estimated_pages(self) -> int:
        return max(1, self.total_words // 250)

    def to_markdown(self) -> str:
        parts = []
        if self.front_matter:
            parts.append(self.front_matter)
            parts.append("\n---\n")
        for ch in self.chapters:
            parts.append(f"# Capitolo {ch.number}: {ch.title}\n")
            parts.append(ch.content)
            parts.append("\n\n")
        if self.back_matter:
            parts.append("---\n")
            parts.append(self.back_matter)
        return "\n".join(parts)


class ContentAssembler:
    """Assembles content from knowledge sources into a structured manuscript."""

    def __init__(self, knowledge_dir: Path, templates_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir
        self.templates_dir = templates_dir

    def assemble(self, book_dna: dict[str, Any]) -> Manuscript:
        """Assemble manuscript from Book DNA definition."""
        manuscript = Manuscript(
            product_id=book_dna["id"],
            title=book_dna["title"],
            subtitle=book_dna.get("subtitle", ""),
        )
        manuscript.front_matter = self._build_front_matter(book_dna)
        sources = book_dna.get("sources", [])
        manuscript.chapters = self._assemble_chapters(sources, book_dna)
        manuscript.back_matter = self._build_back_matter(book_dna)
        return manuscript

    def _build_front_matter(self, book_dna: dict[str, Any]) -> str:
        authors = ", ".join(book_dna.get("authors", ["ACAT Hudolin"]))
        return f"""# {book_dna["title"]}

*{book_dna.get("subtitle", "")}*

Autori: {authors}

---

Copyright ACAT Hudolin. Tutti i diritti riservati.
Metodo Hudolin per i Club Alcologici Territoriali.
"""

    def _assemble_chapters(
        self, sources: list[dict[str, Any]], book_dna: dict[str, Any]
    ) -> list[Chapter]:
        chapters: list[Chapter] = []
        chapter_num = 0
        handler_map = {
            "knowledge_base": self._chapter_from_knowledge,
            "club_method": self._chapter_from_club_method,
            "modulistica": self._chapter_from_modulistica,
        }
        for source in sources:
            handler = handler_map.get(source.get("type", ""))
            if handler:
                for ch in handler(source):
                    chapter_num += 1
                    ch.number = chapter_num
                    chapters.append(ch)
        max_ch = book_dna.get("stages", {}).get("editorial", {}).get("max_chapters", 12)
        return chapters[:max_ch]

    def _chapter_from_knowledge(self, source: dict[str, Any]) -> list[Chapter]:
        chapters = []
        if self.knowledge_dir.exists():
            for md_file in sorted(self.knowledge_dir.rglob("*.md")):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                if len(content.strip()) > 50:
                    title = md_file.stem.replace("_", " ").title()
                    chapters.append(Chapter(
                        number=0, title=title, content=content,
                        source_refs=[str(md_file.relative_to(self.knowledge_dir))],
                    ))
        return chapters

    def _chapter_from_club_method(self, source: dict[str, Any]) -> list[Chapter]:
        club_dir = self.knowledge_dir / "04_operations"
        chapters = []
        if club_dir.exists():
            for md_file in sorted(club_dir.glob("*.md")):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                title = md_file.stem.replace("_", " ").title()
                chapters.append(Chapter(number=0, title=title, content=content,
                                        source_refs=[source.get("ref", "")]))
        return chapters

    def _chapter_from_modulistica(self, source: dict[str, Any]) -> list[Chapter]:
        return [Chapter(
            number=0,
            title="Modulistica e Registri del Club",
            content="""## Strumenti di documentazione

Il Servitore-Insegnante utilizza i seguenti strumenti:

1. **Diario del Club** - Registrazione di ogni seduta
2. **Registro Presenze** - Monitoraggio partecipazione famiglie
3. **Scheda Famiglia** - Profilo e percorso di ogni famiglia
4. **Verbale di Moltiplicazione** - Documentazione scissione Club
5. **Relazione Annuale** - Report attivita annuali
""",
            source_refs=[source.get("ref", "")],
        )]

    def _build_back_matter(self, book_dna: dict[str, Any]) -> str:
        return """# Glossario

- **CAT** - Club Alcologico Territoriale
- **ACAT** - Associazione dei Club Alcologici Territoriali
- **Servitore-Insegnante** - Facilitatore formato nel metodo Hudolin
- **Moltiplicazione** - Processo di creazione di un nuovo Club
- **SIC-ID** - Identificativo universale nel sistema DEPENDEX
- **DRX** - Dialogo, Relazioni, eXperienza

# Risorse

- [dependex.social](https://dependex.social) - Piattaforma globale
- [oltre.social](https://oltre.social) - Rete italiana
- info@dependex.social
"""
