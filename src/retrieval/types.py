from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScoredChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    rank: int = 0


@dataclass(slots=True)
class RetrievalResult:
    query: str
    chunks: list[ScoredChunk]
    context: str = ""
    stage_latencies_ms: dict[str, float] = field(default_factory=dict)
