"""Constellation storage for anchoring Celestial Bodies in a simulated DHT."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Optional

from .schemas import AgentCapabilities, CelestialBody, MemoryState


class AnchorStatus(str, Enum):
    """Status of an anchored body in the Constellation."""
    ANCHOR_OK = "ANCHOR_OK"
    CORRUPTED = "[CORRUPTED/MUTATED]"


@dataclass(frozen=True)
class ConstellationRecord:
    """Record retrieved from the Constellation with integrity verification status."""
    integrity_hash: str
    record_data: Dict[str, Any]
    signature: str
    public_key: Optional[str]
    status: AnchorStatus
    recalculated_hash: Optional[str] = None


class ConstellationStore:
    """In-memory DHT-like store for anchoring Celestial Body manifests.
    
    Thread Safety:
        This store is NOT thread-safe. Access from multiple threads requires
        external synchronization (e.g., threading.Lock).
    
    Hash Collisions:
        If two different bodies produce the same integrity hash, the second
        anchor_body call will overwrite the first. While SHA-256 collisions
        are extremely unlikely, callers should be aware of this behavior.
    
    Signature Verification:
        This store accepts and stores signatures but does NOT perform
        cryptographic validation. Signature verification is the caller's
        responsibility before calling anchor_body.
    
    Integrity Hash:
        The integrity hash covers mission-critical fields only:
        - atmosphere: mission, constraints, interfaces
        - capabilities: interfaces, skills, compute_profile
        - memory_state: continuity_hash, summaries, attachments
        
        The following fields are intentionally excluded from integrity checks
        as they are metadata that may change without affecting the agent's
        core functionality:
        - body_id, display_name, mass, gravity, trust
    """

    def __init__(self) -> None:
        self._dht: Dict[str, Dict[str, Any]] = {}

    def anchor_body(
        self,
        body: CelestialBody,
        signature: str,
        public_key: Optional[str] = None,
    ) -> str:
        """Anchor a CelestialBody to the Constellation.
        
        Args:
            body: The CelestialBody to anchor
            signature: Cryptographic signature (not validated by this method)
            public_key: Optional public key associated with the signature
            
        Returns:
            The integrity hash that can be used to retrieve the body
        """
        integrity_hash = self.compute_integrity_hash(body)
        record_data = {
            "body": body.as_dict(),
            "signature": signature,
            "public_key": public_key,
        }
        self._dht[integrity_hash] = record_data
        return integrity_hash

    def retrieve_body(self, integrity_hash: str) -> Optional[ConstellationRecord]:
        """Retrieve an anchored body and verify its integrity.
        
        Args:
            integrity_hash: The hash returned by anchor_body
            
        Returns:
            ConstellationRecord with verification status, or None if not found
        """
        record_data = self._dht.get(integrity_hash)
        if not record_data:
            return None
        body = self._body_from_payload(record_data["body"])
        recalculated_hash = self.compute_integrity_hash(body)
        status = AnchorStatus.ANCHOR_OK
        if recalculated_hash != integrity_hash:
            status = AnchorStatus.CORRUPTED
        return ConstellationRecord(
            integrity_hash=integrity_hash,
            record_data=record_data,
            signature=record_data["signature"],
            public_key=record_data.get("public_key"),
            status=status,
            recalculated_hash=recalculated_hash,
        )

    def compute_integrity_hash(self, body: CelestialBody) -> str:
        """Compute SHA-256 integrity hash over mission-critical fields.
        
        The hash includes:
        - atmosphere: mission, constraints, interfaces
        - capabilities: interfaces, skills, compute_profile
        - memory_state: continuity_hash, summaries, attachments
        """
        intent_payload = {
            "mission": body.atmosphere.get("mission"),
            "constraints": list(body.atmosphere.get("constraints", [])),
            "interfaces": list(body.atmosphere.get("interfaces", [])),
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
        """Reconstruct a CelestialBody from a stored payload.
        
        Args:
            payload: Dictionary representation of a CelestialBody
            
        Returns:
            Reconstructed CelestialBody instance
            
        Raises:
            KeyError: If required fields are missing from the payload
            TypeError: If field types are incorrect
        """
        # Validate required top-level fields
        required_fields = [
            "body_id", "display_name", "mass", "atmosphere", 
            "gravity", "memory_state", "capabilities"
        ]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise KeyError(f"Missing required fields in payload: {missing}")
        
        memory = payload["memory_state"]
        capabilities = payload["capabilities"]
        
        # Validate nested required fields
        if "continuity_hash" not in memory:
            raise KeyError("Missing 'continuity_hash' in memory_state")
        
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
