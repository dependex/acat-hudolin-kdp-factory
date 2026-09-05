"""Pipeline state machine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Stage(Enum):
    IDLE = "idle"
    HARVEST = "harvest"
    ASSEMBLE = "assemble"
    EDITORIAL = "editorial"
    TYPESET = "typeset"
    COVER = "cover"
    PREFLIGHT = "preflight"
    PACKAGE = "package"
    DELIVER = "deliver"
    DONE = "done"
    ERROR = "error"


@dataclass
class StageEntry:
    stage: Stage
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    @property
    def duration(self) -> str:
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return f"{delta.total_seconds():.1f}s"
        return "-"


@dataclass
class PipelineState:
    current: Stage = Stage.IDLE
    history: list[StageEntry] = field(default_factory=list)
    
    def transition(self, stage: Stage) -> None:
        if self.history:
            self.history[-1].status = "done"
            self.history[-1].completed_at = datetime.now()
        
        entry = StageEntry(stage=stage, status="running", started_at=datetime.now())
        self.history.append(entry)
        self.current = stage
