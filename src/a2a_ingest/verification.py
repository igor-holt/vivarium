"""Citation and verification engine for A2A exchanges."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    SUBJECTIVE = "subjective"
    HALLUCINATION = "hallucination"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class Citation:
    source_id: str
    snippet: str
    uri: Optional[str] = None


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    citations: List[Citation] = field(default_factory=list)
    rationale: Optional[str] = None


class KnowledgeGraph:
    """Abstract interface for verifying claims against the moltbook knowledge graph."""

    def verify_claim(self, claim: str) -> VerificationResult:
        raise NotImplementedError


class InMemoryKnowledgeGraph(KnowledgeGraph):
    """Simple knowledge graph for local development and testing."""

    def __init__(self, facts: Optional[Dict[str, Citation]] = None) -> None:
        self._facts = facts or {}

    def add_fact(self, claim: str, citation: Citation) -> None:
        self._facts[claim] = citation

    def verify_claim(self, claim: str) -> VerificationResult:
        citation = self._facts.get(claim)
        if citation:
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                citations=[citation],
                rationale="Claim matched a known invariant in the knowledge graph.",
            )
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            citations=[],
            rationale="No supporting invariant located in the knowledge graph.",
        )


def verify_claims(
    knowledge_graph: KnowledgeGraph,
    claims: Iterable[str],
) -> Dict[str, VerificationResult]:
    return {claim: knowledge_graph.verify_claim(claim) for claim in claims}
