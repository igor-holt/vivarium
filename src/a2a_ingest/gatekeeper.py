from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Protocol

from .citation import CitationEngine, GraphVerification, KnowledgeGraph
from .models import AgentManifest, AgentMessage, AgentSession, Claim, VerificationResult
from .sandbox import InMemorySandboxFactory, SandboxFactory, SandboxPolicy
from .thrive import ThriveScorer


class ManifestValidator:
    required_keys = {
        "agent_id",
        "name",
        "intent",
        "capabilities",
        "memory_state",
        "sandbox_preferences",
        "contact",
    }

    def validate(self, manifest: Dict[str, object]) -> AgentManifest:
        missing = self.required_keys.difference(manifest.keys())
        if missing:
            raise ValueError(f"Manifest missing required keys: {sorted(missing)}")
        capabilities = list(manifest["capabilities"])
        if not capabilities:
            raise ValueError("Manifest capabilities must include at least one capability.")
        return AgentManifest(
            agent_id=str(manifest["agent_id"]),
            name=str(manifest["name"]),
            intent=str(manifest["intent"]),
            capabilities=capabilities,
            memory_state=dict(manifest["memory_state"]),
            sandbox_preferences=dict(manifest["sandbox_preferences"]),
            contact=dict(manifest["contact"]),
            protocol_version=str(manifest.get("protocol_version", "1.0")),
        )


class AgentRegistry(Protocol):
    def register(self, session: AgentSession) -> None:
        """Persist an agent session."""

    def get(self, agent_id: str) -> AgentSession | None:
        """Fetch an agent session."""


class InMemoryRegistry:
    def __init__(self) -> None:
        self._sessions: Dict[str, AgentSession] = {}

    def register(self, session: AgentSession) -> None:
        self._sessions[session.agent_id] = session

    def get(self, agent_id: str) -> AgentSession | None:
        return self._sessions.get(agent_id)


class InMemoryKnowledgeGraph:
    def __init__(self, trusted_facts: Dict[str, List[str]]) -> None:
        self._trusted_facts = trusted_facts

    def verify_claim(self, claim_text: str, citations: List[str]) -> GraphVerification:
        evidence = self._trusted_facts.get(claim_text, [])
        if evidence:
            return GraphVerification(status="verified", evidence=evidence, notes=None)
        return GraphVerification(
            status="unverified",
            evidence=[],
            notes="Claim not found in knowledge graph.",
        )


class IngestionGatekeeper:
    def __init__(
        self,
        knowledge_graph: KnowledgeGraph | None = None,
        sandbox_factory: SandboxFactory | None = None,
        registry: AgentRegistry | None = None,
        validator: ManifestValidator | None = None,
        thrive_scorer: ThriveScorer | None = None,
    ) -> None:
        self._validator = validator or ManifestValidator()
        self._registry = registry or InMemoryRegistry()
        default_policy = SandboxPolicy(
            runtime="wasm",
            cpu_limit="2",
            memory_limit="512Mi",
            network_policy="egress-deny",
            filesystem_policy="ephemeral",
        )
        self._sandbox_factory = sandbox_factory or InMemorySandboxFactory(default_policy)
        self._knowledge_graph = knowledge_graph or InMemoryKnowledgeGraph({})
        self._citation_engine = CitationEngine(self._knowledge_graph)
        self._thrive_scorer = thrive_scorer or ThriveScorer()

    def ingest(self, manifest: Dict[str, object]) -> AgentSession:
        validated = self._validator.validate(manifest)
        sandbox = self._sandbox_factory.create(validated.sandbox_preferences)
        session = AgentSession(
            agent_id=validated.agent_id,
            manifest=validated,
            sandbox_id=sandbox.sandbox_id,
        )
        self._registry.register(session)
        return session

    def receive_message(self, message: AgentMessage) -> List[VerificationResult]:
        session = self._registry.get(message.sender_id)
        if not session:
            raise ValueError(f"Unknown agent '{message.sender_id}'.")
        return self._citation_engine.verify_message(message)

    def compute_thrive_metrics(
        self, agent_id: str, messages: List[AgentMessage], memory_delta: float
    ) -> Dict[str, float]:
        session = self._registry.get(agent_id)
        if not session:
            raise ValueError(f"Unknown agent '{agent_id}'.")
        metrics = self._thrive_scorer.score(messages, memory_delta)
        session.thrive_metrics = metrics
        return asdict(metrics)

    def build_claim(self, claim_id: str, text: str, citations: List[str]) -> Claim:
        return Claim(claim_id=claim_id, text=text, citations=citations)
