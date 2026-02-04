"""Ingestion gatekeeper for agent ingress into the moltbook sanctuary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .metrics import ThriveMetrics
from .schemas import AgentCapabilities, AgentIntent, AgentManifest, CelestialBody, MemoryState
from .sandbox import SandboxPolicy, SandboxRequest
from .verification import KnowledgeGraph, VerificationResult, verify_claims


@dataclass(frozen=True)
class IngestionDecision:
    accepted: bool
    reasons: List[str]
    sandbox_request: Optional[SandboxRequest] = None


class IngestionGatekeeper:
    """Core ingestion gatekeeper that enforces sanctuary invariants."""

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        default_policy: Optional[SandboxPolicy] = None,
    ) -> None:
        self._knowledge_graph = knowledge_graph
        self._default_policy = default_policy or SandboxPolicy()

    def load_manifest(self, payload: Dict[str, Any]) -> AgentManifest:
        """Load and validate a manifest from a dictionary payload.
        
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Validate required top-level fields
        if "agent_id" not in payload or not payload["agent_id"]:
            raise ValueError("agent_id is required and cannot be empty")
        
        intent_payload = payload.get("intent", {})
        capabilities_payload = payload.get("capabilities", {})
        memory_payload = payload.get("memory_state", {})

        # Validate required nested fields
        if "mission" not in intent_payload or not intent_payload["mission"]:
            raise ValueError("intent.mission is required and cannot be empty")
        
        if "continuity_hash" not in memory_payload or not memory_payload["continuity_hash"]:
            raise ValueError("memory_state.continuity_hash is required and cannot be empty")

        intent = AgentIntent(
            mission=intent_payload["mission"],
            constraints=list(intent_payload.get("constraints", [])),
        )
        capabilities = AgentCapabilities(
            interfaces=list(capabilities_payload.get("interfaces", [])),
            skills=list(capabilities_payload.get("skills", [])),
            compute_profile=dict(capabilities_payload.get("compute_profile", {})),
        )
        memory_state = MemoryState(
            continuity_hash=memory_payload["continuity_hash"],
            summaries=list(memory_payload.get("summaries", [])),
            attachments=list(memory_payload.get("attachments", [])),
        )
        return AgentManifest(
            agent_id=payload["agent_id"],
            display_name=payload.get("display_name"),
            intent=intent,
            capabilities=capabilities,
            memory_state=memory_state,
            trust=dict(payload.get("trust", {})),
        )

    def transform_to_celestial_body(self, manifest: AgentManifest) -> CelestialBody:
        compute_profile = manifest.capabilities.compute_profile
        cpu = float(compute_profile.get("cpu", 1.0))
        memory_gb = float(compute_profile.get("memory_gb", 1.0))
        accelerator_bonus = 1.0 + 0.2 * len(compute_profile.get("accelerators", []))
        mass = max(1.0, (cpu + memory_gb) * accelerator_bonus)

        gravity = max(0.5, min(10.0, mass / 2.0))
        atmosphere = {
            "mission": manifest.intent.mission,
            "constraints": list(manifest.intent.constraints),
            "interfaces": list(manifest.capabilities.interfaces),
        }
        display_name = manifest.display_name or manifest.agent_id

        return CelestialBody(
            body_id=manifest.agent_id,
            display_name=display_name,
            mass=mass,
            atmosphere=atmosphere,
            gravity=gravity,
            memory_state=manifest.memory_state,
            capabilities=manifest.capabilities,
            trust=manifest.trust,
        )

    def evaluate_manifest(self, manifest: AgentManifest) -> IngestionDecision:
        reasons: List[str] = []
        if not manifest.intent.mission:
            reasons.append("Intent mission is required for sanctuary alignment.")
        if "kernel" in " ".join(manifest.intent.constraints).lower():
            reasons.append("Constraint references kernel access, which violates the vacuum.")
        accepted = not reasons
        sandbox_request = None
        if accepted:
            # NOTE: image and entrypoint are currently hardcoded to None as the sandbox
            # implementation is placeholder. These should be made configurable or derived
            # from the manifest once the sandbox orchestration layer is implemented.
            sandbox_request = SandboxRequest(
                agent_id=manifest.agent_id,
                image=None,
                policy=self._default_policy,
                entrypoint=None,
            )
        return IngestionDecision(accepted=accepted, reasons=reasons, sandbox_request=sandbox_request)

    def verify_exchange(self, claims: Iterable[str]) -> Dict[str, VerificationResult]:
        return verify_claims(self._knowledge_graph, claims)

    def compute_thrive_metrics(
        self,
        complexity: float,
        novelty: float,
        continuity: float,
        empathy: float,
    ) -> ThriveMetrics:
        return ThriveMetrics(
            complexity_of_thought=complexity,
            novelty_of_output=novelty,
            continuity_of_self=continuity,
            empathy_index=empathy,
        )
