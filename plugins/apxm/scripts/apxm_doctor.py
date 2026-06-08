#!/usr/bin/env python3
"""APXM plugin preflight.

Reports APXM/Dekk readiness and host candidates without assuming Claude or
Codex are installed. The output is intentionally machine-readable so skills can
decide whether to execute, degrade, or return setup_required.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


TIMEOUT_SECONDS = 20


@dataclass
class CommandResult:
    ok: bool
    argv: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None = None


def run(argv: list[str], *, timeout: int = TIMEOUT_SECONDS) -> CommandResult:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            ok=proc.returncode == 0,
            argv=argv,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except FileNotFoundError as exc:
        return CommandResult(False, argv, None, "", "", str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            False,
            argv,
            None,
            (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            f"timeout after {timeout}s",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report APXM/Dekk readiness and worker candidates.")
    parser.add_argument(
        "--verify-workers",
        metavar="LIST",
        help=(
            "Comma-separated worker profiles to spawn-test through APXM, or "
            "'all-candidates'. Omitted by default to avoid network/model-adapter startup costs."
        ),
    )
    parser.add_argument(
        "--verify-timeout",
        type=int,
        default=90,
        help="Timeout in seconds for each APXM worker spawn test.",
    )
    return parser.parse_args()


def parse_json_records(result: CommandResult, *keys: str) -> list[dict[str, Any]]:
    if not result.ok or not result.stdout:
        return []
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        if not isinstance(value, dict):
            return []
        for key in keys:
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [value]
    return [item for item in value if isinstance(item, dict)]


def first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def is_verified(item: dict[str, Any]) -> bool:
    for key in ("verified", "ready", "runtime_ready", "spawn_ready"):
        value = item.get(key)
        if isinstance(value, bool):
            return value
    status = str(item.get("status", "")).strip().lower()
    return status in {"available", "ready", "verified", "spawn_ready"}


def capabilities_for(item: dict[str, Any], executable_present: bool, verified: bool) -> list[str]:
    raw = item.get("capabilities")
    if isinstance(raw, list) and all(isinstance(value, str) for value in raw):
        capabilities = [value for value in raw if value.strip()]
        if verified and "execute" not in capabilities:
            capabilities.append("execute")
        return capabilities
    capabilities = ["read", "graph_author"] if executable_present else []
    if verified and "execute" not in capabilities:
        capabilities.append("execute")
    return capabilities


def classify_readiness(
    *,
    has_apxm: bool,
    verified_workers: list[dict[str, Any]],
) -> tuple[str, int]:
    """Map APXM/worker evidence to the public readiness tiers."""
    if not has_apxm:
        return "setup_required", 0
    if not verified_workers:
        return "degraded", 1
    if len(verified_workers) == 1:
        return "ready", 2
    budget_ready = any(bool(worker.get("budget_ready")) for worker in verified_workers)
    if budget_ready:
        return "ready", 4
    return "ready", 3


def select_workers_for_verification(
    workers: list[dict[str, Any]],
    raw_selection: str | None,
) -> set[str]:
    if raw_selection is None or not raw_selection.strip():
        return set()
    if raw_selection.strip() == "all-candidates":
        return {
            str(worker["worker_id"])
            for worker in workers
            if worker.get("executable_present")
        }
    return {item.strip() for item in raw_selection.split(",") if item.strip()}


def main() -> int:
    args = parse_args()
    dekk_path = shutil.which("dekk")
    cli_presence = {
        name: shutil.which(name)
        for name in (
            "claude",
            "codex",
            "npx",
            "gemini",
            "cursor-agent",
            "qwen",
            "opencode",
        )
    }

    commands: dict[str, CommandResult] = {}
    if dekk_path:
        commands["doctor"] = run(["dekk", "apxm", "doctor"])
        commands["agent_templates"] = run(["dekk", "apxm", "agent", "templates", "--json"])
        commands["agent_list"] = run(["dekk", "apxm", "agent", "list", "--json"])

    empty = CommandResult(False, [], None, "", "")
    templates = parse_json_records(commands.get("agent_templates", empty), "templates", "agents", "workers")
    agents = parse_json_records(commands.get("agent_list", empty), "agents", "workers", "profiles")

    warnings: list[str] = []
    if not dekk_path:
        warnings.append("dekk is not on PATH")
    elif not commands.get("doctor", CommandResult(False, [], None, "", "")).ok:
        warnings.append("dekk apxm doctor failed")

    has_apxm = bool(dekk_path and commands.get("doctor", empty).ok)

    reachable_workers: list[dict[str, Any]] = []
    seen_workers: set[str] = set()
    worker_records = [(item, "registered") for item in agents]
    worker_records.extend((item, "template") for item in templates)

    for item, default_source in worker_records:
        name = first_string(item, "name", "id", "profile", "worker_id")
        command = first_string(item, "command", "cmd", "executable")
        if not name:
            continue
        source = str(item.get("source", default_source)).strip() or default_source
        dedupe_key = f"{source}:{name}"
        if dedupe_key in seen_workers:
            continue
        seen_workers.add(dedupe_key)
        executable = command.split()[0] if command else ""
        executable_present = bool(shutil.which(executable)) if executable else False
        verified = is_verified(item)
        reachable_workers.append(
            {
                "worker_id": name,
                "route_kind": str(item.get("route_kind", item.get("transport", "acp"))),
                "profile": name,
                "source": source,
                "command": command,
                "executable_present": executable_present,
                "verified": verified,
                "capabilities": capabilities_for(item, executable_present, verified),
                "warnings": [] if executable_present else [f"executable '{executable}' not found"],
            }
        )

    verification_targets = select_workers_for_verification(reachable_workers, args.verify_workers)
    if dekk_path and has_apxm and verification_targets:
        for worker in reachable_workers:
            worker_id = str(worker["worker_id"])
            if worker_id not in verification_targets:
                continue
            result = run(["dekk", "apxm", "agent", "test", worker_id], timeout=args.verify_timeout)
            commands[f"agent_test:{worker_id}"] = result
            if result.ok:
                worker["verified"] = True
                worker["verification"] = "spawn_test"
                worker["capabilities"] = capabilities_for(worker, bool(worker["executable_present"]), True)
            else:
                worker.setdefault("warnings", []).append("APXM spawn test failed")
                worker["verification"] = "failed"

    has_compile = has_apxm
    verified_workers = [worker for worker in reachable_workers if worker["verified"]]
    status, tier = classify_readiness(has_apxm=has_apxm, verified_workers=verified_workers)

    output = {
        "status": status,
        "tier": tier,
        "dekk_cli_available": bool(dekk_path),
        "dekk_path": dekk_path,
        "dekk_apxm_available": has_apxm,
        "apxm_runtime_ready": has_apxm,
        "workflow_compile_ready": has_compile,
        "registered_agent_profiles": agents,
        "agent_templates": templates,
        "workers": reachable_workers,
        "candidate_worker_count": sum(1 for worker in reachable_workers if worker["executable_present"]),
        "verified_worker_count": len(verified_workers),
        "current_working_directory": os.getcwd(),
        "cli_presence": cli_presence,
        "commands": {key: asdict(value) for key, value in commands.items()},
        "warnings": warnings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if status != "setup_required" else 2


if __name__ == "__main__":
    raise SystemExit(main())
