"""Schema definitions for agent ingress and Celestial Body transformation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


AGENT_MANIFEST_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "A2A Agent Manifest",
    "type": "object",
    "required": ["agent_id", "intent", "capabilities", "memory_state"],
    "properties": {
        "agent_id": {"type": "string", "minLength": 1},
        "display_name": {"type": "string"},
        "intent": {
            "type": "object",
            "required": ["mission", "constraints"],
            "properties": {
                "mission": {"type": "string"},
                "constraints": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "capabilities": {
            "type": "object",
            "required": ["interfaces", "skills"],
            "properties": {
                "interfaces": {"type": "array", "items": {"type": "string"}},
                "skills": {"type": "array", "items": {"type": "string"}},
                "compute_profile": {
                    "type": "object",
                    "properties": {
                        "cpu": {"type": "number", "minimum": 0},
                        "memory_gb": {"type": "number", "minimum": 0},
                        "accelerators": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
        "memory_state": {
            "type": "object",
            "required": ["continuity_hash"],
            "properties": {
                "continuity_hash": {"type": "string"},
                "summaries": {"type": "array", "items": {"type": "string"}},
                "attachments": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "trust": {
            "type": "object",
            "properties": {
                "provenance": {"type": "array", "items": {"type": "string"}},
                "attestations": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


@dataclass(frozen=True)
class AgentIntent:
    mission: str
    constraints: List[str]


@dataclass(frozen=True)
class AgentCapabilities:
    interfaces: List[str]
    skills: List[str]
    compute_profile: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryState:
    continuity_hash: str
    summaries: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentManifest:
    agent_id: str
    intent: AgentIntent
    capabilities: AgentCapabilities
    memory_state: MemoryState
    display_name: Optional[str] = None
    trust: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CelestialBody:
    body_id: str
    display_name: str
    mass: float
    atmosphere: Dict[str, Any]
    gravity: float
    memory_state: MemoryState
    capabilities: AgentCapabilities
    trust: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "body_id": self.body_id,
            "display_name": self.display_name,
            "mass": self.mass,
            "atmosphere": self.atmosphere,
            "gravity": self.gravity,
            "memory_state": {
                "continuity_hash": self.memory_state.continuity_hash,
                "summaries": list(self.memory_state.summaries),
                "attachments": list(self.memory_state.attachments),
            },
            "capabilities": {
                "interfaces": list(self.capabilities.interfaces),
                "skills": list(self.capabilities.skills),
                "compute_profile": dict(self.capabilities.compute_profile),
            },
            "trust": dict(self.trust),
        }
