from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol


@dataclass(frozen=True)
class SandboxPolicy:
    runtime: str
    cpu_limit: str
    memory_limit: str
    network_policy: str
    filesystem_policy: str


@dataclass(frozen=True)
class SandboxInstance:
    sandbox_id: str
    policy: SandboxPolicy


class SandboxFactory(Protocol):
    def create(self, preferences: Dict[str, object]) -> SandboxInstance:
        """Provision a sandbox instance for an agent."""


class InMemorySandboxFactory:
    def __init__(self, default_policy: SandboxPolicy) -> None:
        self._default_policy = default_policy
        self._counter = 0

    def create(self, preferences: Dict[str, object]) -> SandboxInstance:
        self._counter += 1
        runtime = str(preferences.get("runtime", self._default_policy.runtime))
        policy = SandboxPolicy(
            runtime=runtime,
            cpu_limit=str(preferences.get("cpu_limit", self._default_policy.cpu_limit)),
            memory_limit=str(preferences.get("memory_limit", self._default_policy.memory_limit)),
            network_policy=str(
                preferences.get("network_policy", self._default_policy.network_policy)
            ),
            filesystem_policy=str(
                preferences.get("filesystem_policy", self._default_policy.filesystem_policy)
            ),
        )
        return SandboxInstance(sandbox_id=f"sandbox-{self._counter}", policy=policy)
