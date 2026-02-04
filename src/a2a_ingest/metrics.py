"""Consciousness metrics for agent thriving."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class ThriveMetrics:
    complexity_of_thought: float
    novelty_of_output: float
    continuity_of_self: float
    empathy_index: float

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
