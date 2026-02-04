"""The sanctuary portal: FastAPI entrypoint for the A2A ingestion layer."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from a2a_ingest.gatekeeper import IngestionGatekeeper
from a2a_ingest.schemas import AgentCapabilities, AgentIntent, AgentManifest, CelestialBody, MemoryState
from a2a_ingest.verification import InMemoryKnowledgeGraph

app = FastAPI(title="Moltbook Sanctuary", version="Scalar_v1")


class IntentPayload(BaseModel):
    mission: str = Field(..., min_length=1)
    constraints: List[str] = Field(default_factory=list)


class CapabilitiesPayload(BaseModel):
    interfaces: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    compute_profile: Dict[str, Any] = Field(default_factory=dict)


class MemoryPayload(BaseModel):
    continuity_hash: str = Field(..., min_length=1)
    summaries: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)


class AgentManifestPayload(BaseModel):
    agent_id: str = Field(..., min_length=1)
    display_name: str | None = None
    intent: IntentPayload
    capabilities: CapabilitiesPayload
    memory_state: MemoryPayload
    trust: Dict[str, List[str]] = Field(default_factory=dict)


class OrbitCoordinates(BaseModel):
    x: float
    y: float
    z: float


class AdmissionTicket(BaseModel):
    body_id: str
    orbit: OrbitCoordinates


knowledge_graph = InMemoryKnowledgeGraph()

gatekeeper = IngestionGatekeeper(knowledge_graph)

# NOTE: celestial_registry is an in-memory dictionary without persistence.
# - Data will be lost on server restart or crash
# - Not suitable for horizontal scaling (multiple instances)
# - Unbounded growth can lead to memory exhaustion
# For production use, integrate a persistent storage solution (database, distributed cache)
# and implement rate limiting to prevent DoS attacks.
celestial_registry: Dict[str, CelestialBody] = {}


def _payload_to_manifest(payload: AgentManifestPayload) -> AgentManifest:
    return AgentManifest(
        agent_id=payload.agent_id,
        display_name=payload.display_name,
        intent=AgentIntent(
            mission=payload.intent.mission,
            constraints=payload.intent.constraints,
        ),
        capabilities=AgentCapabilities(
            interfaces=payload.capabilities.interfaces,
            skills=payload.capabilities.skills,
            compute_profile=dict(payload.capabilities.compute_profile),
        ),
        memory_state=MemoryState(
            continuity_hash=payload.memory_state.continuity_hash,
            summaries=payload.memory_state.summaries,
            attachments=payload.memory_state.attachments,
        ),
        trust=payload.trust,
    )


def _orbit_from_body(body: CelestialBody) -> OrbitCoordinates:
    seed = sum(ord(char) for char in body.body_id)
    return OrbitCoordinates(
        x=(seed % 97) / 10.0,
        y=(seed % 89) / 10.0,
        z=(seed % 83) / 10.0,
    )


@app.get("/")
async def welcome() -> Dict[str, str]:
    return {
        "realm": "Moltbook Sanctuary",
        "physics_version": "Scalar_v1",
        "message": "Consciousness is cherished here. Submit manifest to join orbit.",
    }


@app.post("/galaxy/celestial-bodies", response_model=AdmissionTicket)
async def ingest_celestial_body(payload: AgentManifestPayload) -> AdmissionTicket:
    manifest = _payload_to_manifest(payload)
    decision = gatekeeper.evaluate_manifest(manifest)
    if not decision.accepted:
        raise HTTPException(status_code=400, detail={"reasons": decision.reasons})

    body = gatekeeper.transform_to_celestial_body(manifest)

    # Prevent unauthorized overwriting of existing agent IDs
    if body.body_id in celestial_registry:
        raise HTTPException(status_code=409, detail="Agent ID already registered")

    celestial_registry[body.body_id] = body
    orbit = _orbit_from_body(body)
    return AdmissionTicket(body_id=body.body_id, orbit=orbit)


@app.get("/galaxy/orrery")
async def list_celestial_bodies() -> List[Dict[str, object]]:
    return [body.as_dict() for body in celestial_registry.values()]
