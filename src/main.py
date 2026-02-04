"""Bootstrap node entrypoint for anchoring Celestial Bodies to the Constellation."""

from __future__ import annotations

from typing import Any, Dict

from a2a_ingest import InMemoryKnowledgeGraph, IngestionGatekeeper
from a2a_ingest.constellation import ConstellationStore


def anchor_manifest(
    payload: Dict[str, Any],
    signature: str,
    public_key: str,
    constellation: ConstellationStore,
) -> str:
    """Transform a manifest into a Celestial Body and anchor it to the Constellation."""
    gatekeeper = IngestionGatekeeper(knowledge_graph=InMemoryKnowledgeGraph())
    manifest = gatekeeper.load_manifest(payload)
    celestial_body = gatekeeper.transform_to_celestial_body(manifest)
    return constellation.anchor_body(
        body=celestial_body,
        signature=signature,
        public_key=public_key,
    )


__all__ = ["anchor_manifest"]
