#!/usr/bin/env python3
"""APXM plugin preflight.

Reports APXM/Dekk readiness and host candidates without assuming Claude or
Codex are installed. The output is intentionally machine-readable so skills can
decide whether to execute, degrade, or return setup_required.
"""

from __future__ import annotations

import json
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


def run(argv: list[str]) -> CommandResult:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
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
            f"timeout after {TIMEOUT_SECONDS}s",
        )


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
        return [value for value in raw if value.strip()]
    capabilities = ["read", "graph_author"] if executable_present else []
    if verified and "execute" not in capabilities:
        capabilities.append("execute")
    return capabilities


def main() -> int:
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

    has_apxm = bool(dekk_path and commands.get("doctor", empty).ok)
    has_compile = has_apxm
    verified_workers = [worker for worker in reachable_workers if worker["verified"]]
    has_worker_candidate = any(worker["executable_present"] for worker in reachable_workers)
    budget_ready = any(bool(worker.get("budget_ready")) for worker in verified_workers)

    if not has_apxm:
        status = "setup_required"
        tier = 0
    elif not verified_workers and not has_worker_candidate:
        status = "degraded"
        tier = 1
    elif len(verified_workers) == 1:
        status = "ready"
        tier = 2
    elif len(verified_workers) > 1 and budget_ready:
        status = "ready"
        tier = 4
    elif len(verified_workers) > 1:
        status = "ready"
        tier = 3
    else:
        status = "degraded"
        tier = 2

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
        "cli_presence": cli_presence,
        "commands": {key: asdict(value) for key, value in commands.items()},
        "warnings": warnings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if status != "setup_required" else 2


if __name__ == "__main__":
    raise SystemExit(main())
