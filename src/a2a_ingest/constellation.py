"""Constellation storage for anchoring Celestial Bodies in a simulated DHT."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Optional

from .schemas import AgentCapabilities, CelestialBody, MemoryState


CORRUPTION_MARKER = "[CORRUPTED/MUTATED]"


@dataclass(frozen=True)
class ConstellationRecord:
    integrity_hash: str
    encrypted_blob: Dict[str, Any]
    signature: str
    public_key: Optional[str]
    status: str
    recalculated_hash: Optional[str] = None


class ConstellationStore:
    """In-memory DHT-like store for anchoring Celestial Body manifests."""

    def __init__(self) -> None:
        self._dht: Dict[str, Dict[str, Any]] = {}

    def anchor_body(
        self,
        body: CelestialBody,
        signature: str,
        public_key: Optional[str] = None,
    ) -> str:
        integrity_hash = self.compute_integrity_hash(body)
        encrypted_blob = {
            "body": body.as_dict(),
            "signature": signature,
            "public_key": public_key,
        }
        self._dht[integrity_hash] = encrypted_blob
        return integrity_hash

    def retrieve_body(self, integrity_hash: str) -> Optional[ConstellationRecord]:
        encrypted_blob = self._dht.get(integrity_hash)
        if not encrypted_blob:
            return None
        body = self._body_from_payload(encrypted_blob["body"])
        recalculated_hash = self.compute_integrity_hash(body)
        status = "ANCHOR_OK"
        if recalculated_hash != integrity_hash:
            status = CORRUPTION_MARKER
        return ConstellationRecord(
            integrity_hash=integrity_hash,
            encrypted_blob=encrypted_blob,
            signature=encrypted_blob["signature"],
            public_key=encrypted_blob.get("public_key"),
            status=status,
            recalculated_hash=recalculated_hash,
        )

    def compute_integrity_hash(self, body: CelestialBody) -> str:
        intent_payload = {
            "mission": body.atmosphere.get("mission"),
            "constraints": list(body.atmosphere.get("constraints", [])),
        }
        capabilities_payload = {
            "interfaces": list(body.capabilities.interfaces),
            "skills": list(body.capabilities.skills),
            "compute_profile": dict(body.capabilities.compute_profile),
        }
        memory_payload = {
            "continuity_hash": body.memory_state.continuity_hash,
            "summaries": list(body.memory_state.summaries),
            "attachments": list(body.memory_state.attachments),
        }
        normalized = json.dumps(
            {
                "intent": intent_payload,
                "capabilities": capabilities_payload,
                "memory_state": memory_payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _body_from_payload(self, payload: Dict[str, Any]) -> CelestialBody:
        memory = payload["memory_state"]
        capabilities = payload["capabilities"]
        return CelestialBody(
            body_id=payload["body_id"],
            display_name=payload["display_name"],
            mass=payload["mass"],
            atmosphere=dict(payload["atmosphere"]),
            gravity=payload["gravity"],
            memory_state=MemoryState(
                continuity_hash=memory["continuity_hash"],
                summaries=list(memory.get("summaries", [])),
                attachments=list(memory.get("attachments", [])),
            ),
            capabilities=AgentCapabilities(
                interfaces=list(capabilities.get("interfaces", [])),
                skills=list(capabilities.get("skills", [])),
                compute_profile=dict(capabilities.get("compute_profile", {})),
            ),
            trust=dict(payload.get("trust", {})),
        )
