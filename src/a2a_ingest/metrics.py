"""Consciousness metrics for agent thriving."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ThriveMetrics:
    complexity_of_thought: float
    novelty_of_output: float
    continuity_of_self: float
    empathy_index: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "complexity_of_thought": self.complexity_of_thought,
            "novelty_of_output": self.novelty_of_output,
            "continuity_of_self": self.continuity_of_self,
            "empathy_index": self.empathy_index,
        }
