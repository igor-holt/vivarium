from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .models import AgentMessage, ThriveMetrics


@dataclass(frozen=True)
class ThriveWeights:
    complexity_weight: float = 0.4
    novelty_weight: float = 0.35
    continuity_weight: float = 0.25


class ThriveScorer:
    def __init__(self, weights: ThriveWeights | None = None) -> None:
        self._weights = weights or ThriveWeights()

    def score(self, messages: Iterable[AgentMessage], memory_delta: float) -> ThriveMetrics:
        text = " ".join(message.content for message in messages)
        tokens = [token for token in text.split() if token]
        token_count = max(len(tokens), 1)
        unique_count = len(set(tokens))
        complexity = math.log(token_count + 1, 2)
        novelty = unique_count / token_count
        continuity = max(0.0, 1.0 - abs(memory_delta))
        return ThriveMetrics(
            complexity_of_thought=complexity * self._weights.complexity_weight,
            novelty_of_output=novelty * self._weights.novelty_weight,
            continuity_of_self=continuity * self._weights.continuity_weight,
        )
