from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AgentManifest:
    agent_id: str
    name: str
    intent: str
    capabilities: List[str]
    memory_state: Dict[str, Any]
    sandbox_preferences: Dict[str, Any]
    contact: Dict[str, Any]
    protocol_version: str = "1.0"


@dataclass
class AgentSession:
    agent_id: str
    manifest: AgentManifest
    sandbox_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    thrive_metrics: Optional["ThriveMetrics"] = None


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    citations: List[str]


@dataclass(frozen=True)
class AgentMessage:
    sender_id: str
    content: str
    claims: List[Claim]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    claim_id: str
    status: str
    evidence: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(frozen=True)
class ThriveMetrics:
    complexity_of_thought: float
    novelty_of_output: float
    continuity_of_self: float
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
