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
    knowledge_graph: InMemoryKnowledgeGraph,
) -> str:
    """Transform a manifest into a Celestial Body and anchor it to the Constellation.
    
    Args:
        payload: Raw agent manifest payload
        signature: Cryptographic signature (not validated by this function)
        public_key: Public key associated with the signature
        constellation: ConstellationStore instance for anchoring
        knowledge_graph: InMemoryKnowledgeGraph instance for verification
        
    Returns:
        The integrity hash of the anchored body
        
    Raises:
        KeyError: If required fields are missing from the payload
        ValueError: If the manifest is malformed or invalid
        TypeError: If field types are incorrect
    """
    try:
        gatekeeper = IngestionGatekeeper(knowledge_graph=knowledge_graph)
        manifest = gatekeeper.load_manifest(payload)
        celestial_body = gatekeeper.transform_to_celestial_body(manifest)
        return constellation.anchor_body(
            body=celestial_body,
            signature=signature,
            public_key=public_key,
        )
    except KeyError as e:
        raise KeyError(f"Missing required field in manifest: {e}") from e
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid manifest format: {e}") from e


__all__ = ["anchor_manifest"]
