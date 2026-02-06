import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from a2a_ingest.gatekeeper import IngestionGatekeeper, InMemoryKnowledgeGraph  # noqa: E402
from a2a_ingest.models import AgentMessage  # noqa: E402


class GatekeeperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = {
            "agent_id": "agent-1",
            "name": "Test Agent",
            "intent": "Testing ingress",
            "capabilities": ["reasoning"],
            "memory_state": {"checkpoint": "alpha"},
            "sandbox_preferences": {"runtime": "wasm"},
            "contact": {"operator": "test-suite"},
        }

    def test_ingest_registers_session(self) -> None:
        gatekeeper = IngestionGatekeeper()
        session = gatekeeper.ingest(self.manifest)
        self.assertEqual(session.agent_id, "agent-1")
        self.assertEqual(session.sandbox_id, "sandbox-1")

    def test_receive_message_verifies_claims(self) -> None:
        graph = InMemoryKnowledgeGraph(
            {"Mars has two moons.": ["kg://facts/mars/moons"]}
        )
        gatekeeper = IngestionGatekeeper(knowledge_graph=graph)
        gatekeeper.ingest(self.manifest)
        claim = gatekeeper.build_claim(
            "claim-1",
            "Mars has two moons.",
            ["kg://facts/mars/moons"],
        )
        message = AgentMessage(
            sender_id="agent-1",
            content="Mars has two moons.",
            claims=[claim],
        )
        results = gatekeeper.receive_message(message)
        self.assertEqual(results[0].status, "verified")

    def test_subjective_claims_are_flagged(self) -> None:
        gatekeeper = IngestionGatekeeper()
        gatekeeper.ingest(self.manifest)
        claim = gatekeeper.build_claim("claim-2", "Sky poetry is soothing.", [])
        message = AgentMessage(
            sender_id="agent-1",
            content="Sky poetry is soothing.",
            claims=[claim],
        )
        results = gatekeeper.receive_message(message)
        self.assertEqual(results[0].status, "subjective")


if __name__ == "__main__":
    unittest.main()
