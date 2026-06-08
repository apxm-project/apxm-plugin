#!/usr/bin/env python3
"""Regression tests for APXM plugin preflight classification."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
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
        candidate = {"worker_id": "planner-a", "executable_present": True, "verified": False}
        self.assertFalse(candidate["verified"])
        verified = [worker for worker in [candidate] if worker.get("verified")]
        self.assertEqual(
            self.doctor.classify_readiness(has_apxm=True, verified_workers=verified),
            ("degraded", 1),
        )

    def test_one_verified_worker_is_tier_two(self) -> None:
        self.assertEqual(self.classify(True, {"worker_id": "worker-a"}), ("ready", 2))

    def test_multiple_verified_workers_without_budget_are_tier_three(self) -> None:
        workers = ({"worker_id": "worker-a"}, {"worker_id": "worker-b"})
        self.assertEqual(self.classify(True, *workers), ("ready", 3))

    def test_multiple_budgeted_workers_are_tier_four(self) -> None:
        workers = ({"worker_id": "worker-a"}, {"worker_id": "worker-b", "budget_ready": True})
        self.assertEqual(self.classify(True, *workers), ("ready", 4))

    def test_verified_worker_capabilities_include_execute(self) -> None:
        capabilities = self.doctor.capabilities_for(
            {"capabilities": ["read", "graph_author"]},
            executable_present=True,
            verified=True,
        )
        self.assertIn("execute", capabilities)

    def test_executable_from_command_handles_env_and_quotes(self) -> None:
        self.assertEqual(
            self.doctor.executable_from_command("FOO=bar env BAR=baz 'custom agent' --acp"),
            "custom agent",
        )

    def test_all_resolvable_selects_every_worker(self) -> None:
        workers = [
            {"worker_id": "alpha", "executable_present": True},
            {"worker_id": "beta", "executable_present": False},
        ]
        self.assertEqual(
            self.doctor.select_workers_for_verification(workers, "all-resolvable"),
            {"alpha", "beta"},
        )

    def test_all_candidates_selects_only_present_executables(self) -> None:
        workers = [
            {"worker_id": "alpha", "executable_present": True},
            {"worker_id": "beta", "executable_present": False},
        ]
        self.assertEqual(
            self.doctor.select_workers_for_verification(workers, "all-candidates"),
            {"alpha"},
        )

    def test_capability_index_uses_arbitrary_worker_ids(self) -> None:
        workers = [
            {"worker_id": "alpha", "capabilities": ["read", "graph_author"], "verified": False},
            {"worker_id": "beta", "capabilities": ["read", "execute"], "verified": True},
        ]
        self.assertEqual(
            self.doctor.index_workers_by_capability(workers)["read"],
            ["alpha", "beta"],
        )
        self.assertEqual(
            self.doctor.index_workers_by_capability(workers, verified_only=True)["execute"],
            ["beta"],
        )

    def test_role_routes_apply_preferences_without_requiring_specific_brands(self) -> None:
        workers = [
            {
                "worker_id": "alpha",
                "capabilities": ["read", "graph_author", "execute"],
                "executable_present": True,
                "verified": True,
            },
            {
                "worker_id": "beta",
                "capabilities": ["read", "execute"],
                "executable_present": True,
                "verified": True,
            },
        ]
        policy = {
            "worker_roles": {
                "planner": {"required_capabilities": ["read", "graph_author"]},
                "executor": {"required_capabilities": ["execute"]},
            },
            "preferred_workers": {
                "planner": ["alpha"],
                "executor": ["beta"],
            },
        }
        routes = self.doctor.resolve_role_routes(workers, policy)
        self.assertTrue(routes["ready"])
        self.assertEqual(routes["routes"]["planner"]["selected_workers"], ["alpha"])
        self.assertEqual(routes["routes"]["executor"]["selected_workers"], ["beta"])

    def test_role_routes_report_missing_capability(self) -> None:
        workers = [
            {
                "worker_id": "alpha",
                "capabilities": ["read", "graph_author", "execute"],
                "executable_present": True,
                "verified": True,
            },
        ]
        policy = {
            "worker_roles": {
                "writer": {"required_capabilities": ["write"]},
            }
        }
        routes = self.doctor.resolve_role_routes(workers, policy)
        self.assertFalse(routes["ready"])
        self.assertEqual(routes["routes"]["writer"]["status"], "missing")

    def test_discovers_explicit_apxm_dekk_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".dekk.toml").write_text('[project]\nname = "apxm"\n')
            warnings: list[str] = []
            self.assertEqual(self.doctor.discover_apxm_cwd(str(root), warnings), str(root.resolve()))
            self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
