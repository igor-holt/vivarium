"""Sandbox policy definitions for the A2A playpen."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SandboxPolicy:
    runtime: str = "docker"
    network_access: bool = False
    filesystem_write: bool = False
    max_cpu_seconds: int = 60
    max_memory_mb: int = 256
    allowed_syscalls: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SandboxRequest:
    agent_id: str
    image: Optional[str]
    policy: SandboxPolicy
    entrypoint: Optional[str] = None
    env: Optional[dict] = None
