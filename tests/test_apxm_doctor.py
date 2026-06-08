#!/usr/bin/env python3
"""Regression tests for APXM plugin preflight classification."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1] / "plugins" / "apxm"
DOCTOR_PATH = PLUGIN_ROOT / "scripts" / "apxm_doctor.py"


def load_doctor_module():
    spec = importlib.util.spec_from_file_location("apxm_doctor", DOCTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {DOCTOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReadinessClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doctor = load_doctor_module()

    def classify(self, has_apxm: bool, *workers: dict[str, object]) -> tuple[str, int]:
        return self.doctor.classify_readiness(
            has_apxm=has_apxm,
            verified_workers=list(workers),
        )

    def test_no_apxm_is_tier_zero_setup_required(self) -> None:
        self.assertEqual(self.classify(False), ("setup_required", 0))

    def test_apxm_without_verified_workers_is_tier_one(self) -> None:
        self.assertEqual(self.classify(True), ("degraded", 1))

    def test_candidate_executables_do_not_promote_to_tier_two(self) -> None:
        candidate = {"worker_id": "codex", "executable_present": True, "verified": False}
        self.assertFalse(candidate["verified"])
        self.assertEqual(self.classify(True), ("degraded", 1))

    def test_one_verified_worker_is_tier_two(self) -> None:
        self.assertEqual(self.classify(True, {"worker_id": "codex"}), ("ready", 2))

    def test_multiple_verified_workers_without_budget_are_tier_three(self) -> None:
        workers = ({"worker_id": "codex"}, {"worker_id": "claude"})
        self.assertEqual(self.classify(True, *workers), ("ready", 3))

    def test_multiple_budgeted_workers_are_tier_four(self) -> None:
        workers = ({"worker_id": "codex"}, {"worker_id": "claude", "budget_ready": True})
        self.assertEqual(self.classify(True, *workers), ("ready", 4))

    def test_verified_worker_capabilities_include_execute(self) -> None:
        capabilities = self.doctor.capabilities_for(
            {"capabilities": ["read", "graph_author"]},
            executable_present=True,
            verified=True,
        )
        self.assertIn("execute", capabilities)


if __name__ == "__main__":
    unittest.main()
