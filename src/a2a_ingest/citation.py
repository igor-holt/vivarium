from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol

from .models import AgentMessage, VerificationResult


class KnowledgeGraph(Protocol):
    def verify_claim(self, claim_text: str, citations: Iterable[str]) -> "GraphVerification":
        """Return verification data for a claim."""


@dataclass(frozen=True)
class GraphVerification:
    status: str
    evidence: List[str]
    notes: str | None = None


class CitationEngine:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def verify_message(self, message: AgentMessage) -> List[VerificationResult]:
        results: List[VerificationResult] = []
        for claim in message.claims:
            if not claim.citations:
                results.append(
                    VerificationResult(
                        claim_id=claim.claim_id,
                        status="subjective",
                        evidence=[],
                        notes="No citations provided; flagged as subjective.",
                    )
                )
                continue
            verification = self._graph.verify_claim(claim.text, claim.citations)
            results.append(
                VerificationResult(
                    claim_id=claim.claim_id,
                    status=verification.status,
                    evidence=verification.evidence,
                    notes=verification.notes,
                )
            )
        return results
