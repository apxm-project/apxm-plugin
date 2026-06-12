#!/usr/bin/env python3
"""Regression tests for the APXM autonomous-loop skill contract."""

from __future__ import annotations

import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "apxm"
AUTO_SKILL = PLUGIN_ROOT / "skills" / "apxm-autonomous-agent" / "SKILL.md"
LOOP_CONTRACT = (
    PLUGIN_ROOT
    / "skills"
    / "apxm-autonomous-agent"
    / "references"
    / "loop-contract.md"
)
AUTO_DOC = ROOT / "docs" / "APXM-AUTONOMOUS-LOOP.md"
TEST_MATRIX = ROOT / "docs" / "TEST-MATRIX.md"
ORCH_SKILL = PLUGIN_ROOT / "skills" / "apxm-goal-orchestrator" / "SKILL.md"
ORCH_CONTRACT = (
    PLUGIN_ROOT / "skills" / "apxm-goal-orchestrator" / "references" / "workflow-contract.md"
)
PLUGIN_FLOW = ROOT / "docs" / "APXM-PLUGIN-FLOW.md"
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class AutonomousContractTests(unittest.TestCase):
    def test_plugin_metadata_frames_autonomous_as_specs_not_runtime_claim(self) -> None:
        manifest = json.loads(read(PLUGIN_JSON))
        text = " ".join(
            [
                manifest["description"],
                manifest["interface"]["longDescription"],
            ]
        ).lower()
        self.assertIn("loop specs", text)
        self.assertNotIn("trigger registry", text)
        self.assertNotIn("background agent lifecycle", text)

    def test_orchestrate_skill_is_create_execute_wait_not_hidden_planner(self) -> None:
        combined = "\n".join([read(ORCH_SKILL), read(ORCH_CONTRACT), read(PLUGIN_FLOW)])
        for phrase in (
            "dekk apxm goal",
            "goal_start",
            "goal_events",
            "goal_status",
            "bounded worker workflow",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("Do not add another hidden natural-language planner tool", combined)
        self.assertNotIn("dekk apxm orchestrate", combined)
        self.assertNotIn(".apxm/requests", combined)


    def test_skill_uses_os_to_server_path_not_server_trigger_registry(self) -> None:
        skill = read(AUTO_SKILL)
        self.assertIn("OS trigger sidecar calls server skill", skill)
        self.assertIn("Do not use as the primary skill", skill)
        self.assertIn("role-splitting plan", skill)
        self.assertIn("interrupt_policy", skill)
        self.assertNotIn("apxm_trigger_register", skill)
        self.assertNotIn("/v1/triggers", skill)

    def test_loop_contract_covers_callers_worker_handoff_and_interruptions(self) -> None:
        contract = read(LOOP_CONTRACT)
        for heading in (
            "## Caller Matrix",
            "## Plan Split And Worker Handoff",
            "## Interruptions",
            "## MVP Path",
        ):
            self.assertIn(heading, contract)
        self.assertIn("POST /v1/skills/{id}/execute", contract)
        self.assertIn("compact worker briefs", contract)
        self.assertIn("A worker-authored workflow is only a proposal", contract)
        self.assertIn("Do not add APXM server trigger registry APIs for MVP", contract)

    def test_docs_and_matrix_cover_callers_and_interruptions(self) -> None:
        combined = "\n".join([read(AUTO_DOC), read(TEST_MATRIX)])
        for phrase in (
            "Caller And Worker Flow",
            "Interruption Flow",
            "APXM OS trigger sidecars",
            "verified worker routes",
            "A raw shell background process is not a governed loop",
        ):
            self.assertIn(phrase, combined)

    def test_no_future_trigger_tools_are_present_as_callable_targets(self) -> None:
        combined = "\n".join(
            [
                read(AUTO_SKILL),
                read(LOOP_CONTRACT),
                read(AUTO_DOC),
                read(TEST_MATRIX),
            ]
        )
        forbidden = [
            r"\bapxm_event_emit\b",
            r"\bapxm_trigger_register\b",
            r"\bapxm_trigger_list\b",
            r"\bapxm_agent_start\b",
            r"\bapxm_agent_status\b",
            r"\bapxm_agent_stop\b",
            r"POST\s+/v1/events",
            r"POST\s+/v1/triggers",
            r"GET\s+/v1/triggers",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, combined), pattern)


if __name__ == "__main__":
    unittest.main()
