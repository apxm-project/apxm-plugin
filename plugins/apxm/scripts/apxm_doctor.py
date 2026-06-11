#!/usr/bin/env python3
"""APXM plugin preflight.

Reports APXM/Dekk readiness and host candidates without assuming any specific
worker profiles are installed. The output is intentionally machine-readable so
skills can decide whether to execute, degrade, or return setup_required.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


TIMEOUT_SECONDS = 20
ALL_CANDIDATES = "all-candidates"
ALL_RESOLVABLE = "all-resolvable"

DEFAULT_ROLE_CAPABILITIES: dict[str, list[str]] = {
    "planner": ["read", "workflow_author"],
    "workflow_author": ["read", "workflow_author"],
    "executor": ["execute"],
    "reviewer": ["read"],
    "critic": ["read", "critique"],
    "verifier": ["execute"],
    "synthesizer": ["read"],
}


@dataclass
class CommandResult:
    ok: bool
    argv: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    cwd: str | None = None
    error: str | None = None


def run(
    argv: list[str],
    *,
    timeout: int = TIMEOUT_SECONDS,
    cwd: str | None = None,
) -> CommandResult:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=cwd,
        )
        return CommandResult(
            ok=proc.returncode == 0,
            argv=argv,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        return CommandResult(False, argv, None, "", "", cwd, str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            False,
            argv,
            None,
            (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            cwd,
            f"timeout after {timeout}s",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report APXM/Dekk readiness and worker candidates.")
    parser.add_argument(
        "--verify-workers",
        metavar="LIST",
        help=(
            "Comma-separated worker profiles to spawn-test through APXM, or "
            f"'{ALL_CANDIDATES}'/'{ALL_RESOLVABLE}'. Omitted by default to avoid "
            "network/model-adapter startup costs."
        ),
    )
    parser.add_argument(
        "--verify-timeout",
        type=int,
        default=90,
        help="Timeout in seconds for each APXM worker spawn test.",
    )
    parser.add_argument(
        "--policy",
        metavar="FILE",
        help="Optional JSON policy to evaluate worker_roles, preferred_workers, and allowed_workers.",
    )
    parser.add_argument(
        "--apxm-cwd",
        metavar="DIR",
        help=(
            "APXM worktree to use when only the Dekk wrapper is available. "
            "Can also be set with APXM_WORKTREE, APXM_REPO, or APXM_DEKK_CWD."
        ),
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


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def is_env_assignment(token: str) -> bool:
    if "=" not in token or token.startswith("-"):
        return False
    name = token.split("=", 1)[0]
    if not name:
        return False
    return all(char == "_" or char.isalnum() for char in name) and not name[0].isdigit()


def executable_from_command(command: str) -> str:
    if not command.strip():
        return ""
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    if not parts:
        return ""

    index = 0
    while index < len(parts) and is_env_assignment(parts[index]):
        index += 1
    if index >= len(parts):
        return ""

    if parts[index] == "env":
        index += 1
        while index < len(parts):
            token = parts[index]
            if token == "--":
                index += 1
                break
            if token.startswith("-") or is_env_assignment(token):
                index += 1
                continue
            break
    return parts[index] if index < len(parts) else ""


def is_verified(item: dict[str, Any]) -> bool:
    for key in ("verified", "ready", "runtime_ready", "spawn_ready"):
        value = item.get(key)
        if isinstance(value, bool):
            return value
    status = str(item.get("status", "")).strip().lower()
    return status in {"available", "ready", "verified", "spawn_ready"}


def route_capabilities_for(item: dict[str, Any], executable_present: bool, verified: bool) -> list[str]:
    capabilities = ["read", "workflow_author"] if executable_present else []
    raw = item.get("route_capabilities")
    if isinstance(raw, list) and all(isinstance(value, str) for value in raw):
        capabilities.extend(value.strip() for value in raw if value.strip())
    if verified:
        capabilities.extend(["read", "workflow_author", "execute"])
    deduped: list[str] = []
    for capability in capabilities:
        if capability not in deduped:
            deduped.append(capability)
    return deduped


def capability_servers_for(item: dict[str, Any]) -> list[str]:
    raw = item.get("capabilities")
    if not isinstance(raw, list):
        return []
    servers: list[str] = []
    for value in raw:
        if not isinstance(value, dict):
            continue
        name = first_string(value, "name", "id")
        if name:
            servers.append(name)
    return servers


def build_worker_descriptor(item: dict[str, Any], default_source: str) -> dict[str, Any] | None:
    name = first_string(item, "name", "id", "profile", "worker_id")
    command = first_string(item, "command", "cmd", "executable")
    if not name:
        return None

    source = str(item.get("source", default_source)).strip() or default_source
    executable = executable_from_command(command)
    executable_present = bool(shutil.which(executable)) if executable else False
    verified = is_verified(item)
    warnings = []
    if not command:
        warnings.append("worker command is empty")
    elif not executable:
        warnings.append("could not parse worker executable")
    elif not executable_present:
        warnings.append(f"executable '{executable}' not found")

    return {
        "worker_id": name,
        "route_kind": str(item.get("route_kind", item.get("transport", "acp"))),
        "profile": name,
        "source": source,
        "command": command,
        "executable": executable,
        "executable_present": executable_present,
        "verified": verified,
        "route_capabilities": route_capabilities_for(item, executable_present, verified),
        "capability_servers": capability_servers_for(item),
        "warnings": warnings,
    }


def collect_workers(agents: list[dict[str, Any]], templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reachable_workers: list[dict[str, Any]] = []
    seen_workers: set[str] = set()
    worker_records = [(item, "registered") for item in agents]
    worker_records.extend((item, "template") for item in templates)

    for item, default_source in worker_records:
        worker = build_worker_descriptor(item, default_source)
        if worker is None:
            continue
        dedupe_key = f"{worker['source']}:{worker['worker_id']}"
        if dedupe_key in seen_workers:
            continue
        seen_workers.add(dedupe_key)
        reachable_workers.append(worker)
    return reachable_workers


def index_workers_by_route_capability(
    workers: list[dict[str, Any]],
    *,
    verified_only: bool = False,
) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for worker in workers:
        if verified_only and not worker.get("verified"):
            continue
        worker_id = str(worker.get("worker_id", "")).strip()
        if not worker_id:
            continue
        for capability in normalize_string_list(worker.get("route_capabilities")):
            index[capability].append(worker_id)
    return {key: sorted(values) for key, values in sorted(index.items())}


def load_policy(path: str | None, warnings: list[str]) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        value = json.loads(Path(path).read_text())
    except OSError as exc:
        warnings.append(f"failed to read policy '{path}': {exc}")
        return None
    except json.JSONDecodeError as exc:
        warnings.append(f"failed to parse policy '{path}' as JSON: {exc}")
        return None
    if not isinstance(value, dict):
        warnings.append(f"policy '{path}' must be a JSON object")
        return None
    return value


def is_apxm_dekk_worktree(path: Path) -> bool:
    config = path / ".dekk.toml"
    if not config.is_file():
        return False
    try:
        content = config.read_text()
    except OSError:
        return False
    return 'name = "apxm"' in content or "name = 'apxm'" in content


def discover_apxm_cwd(raw_cwd: str | None, warnings: list[str]) -> str | None:
    candidates: list[Path] = []
    def add_candidate_with_parents(path: Path) -> None:
        candidates.append(path)
        candidates.extend(path.parents)

    if raw_cwd:
        add_candidate_with_parents(Path(raw_cwd).expanduser())
    for env_name in ("APXM_WORKTREE", "APXM_REPO", "APXM_DEKK_CWD"):
        value = os.environ.get(env_name)
        if value:
            add_candidate_with_parents(Path(value).expanduser())

    current = Path.cwd()
    add_candidate_with_parents(current)

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if is_apxm_dekk_worktree(resolved):
            return str(resolved)

    if raw_cwd:
        warnings.append(f"'{raw_cwd}' is not an APXM Dekk worktree")
    return None


def resolve_apxm_command(args: argparse.Namespace, warnings: list[str]) -> dict[str, Any] | None:
    apxm_path = shutil.which("apxm")
    if apxm_path:
        return {
            "kind": "apxm",
            "prefix": ["apxm"],
            "cwd": None,
            "path": apxm_path,
        }

    dekk_path = shutil.which("dekk")
    if not dekk_path:
        warnings.append("neither apxm nor dekk is on PATH")
        return None

    apxm_cwd = discover_apxm_cwd(args.apxm_cwd, warnings)
    if not apxm_cwd:
        warnings.append(
            "apxm CLI is not on PATH and no APXM Dekk worktree was found; "
            "set APXM_WORKTREE or pass --apxm-cwd"
        )
        return {
            "kind": "dekk-apxm-unresolved",
            "prefix": ["dekk", "apxm"],
            "cwd": None,
            "path": dekk_path,
        }

    return {
        "kind": "dekk-apxm",
        "prefix": ["dekk", "apxm"],
        "cwd": apxm_cwd,
        "path": dekk_path,
    }


def apxm_argv(runner: dict[str, Any], *args: str) -> list[str]:
    return [*runner["prefix"], *args]


def normalize_role_requirements(policy: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    raw_roles = policy.get("worker_roles") if isinstance(policy, dict) else None
    roles: dict[str, dict[str, Any]] = {}
    if isinstance(raw_roles, dict):
        for role, spec in raw_roles.items():
            if not isinstance(role, str) or not role.strip():
                continue
            required = DEFAULT_ROLE_CAPABILITIES.get(role, [])
            min_count = 1
            if isinstance(spec, dict):
                required = normalize_string_list(spec.get("required_capabilities")) or required
                raw_min = spec.get("min_count", 1)
                if isinstance(raw_min, int) and raw_min > 0:
                    min_count = raw_min
            elif isinstance(spec, list):
                required = normalize_string_list(spec) or required
            roles[role.strip()] = {
                "required_capabilities": required,
                "min_count": min_count,
            }
    if roles:
        return roles
    return {
        role: {"required_capabilities": caps, "min_count": 1}
        for role, caps in DEFAULT_ROLE_CAPABILITIES.items()
    }


def resolve_role_routes(
    workers: list[dict[str, Any]],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allowed_workers = set(normalize_string_list(policy.get("allowed_workers"))) if policy else set()
    raw_preferences = policy.get("preferred_workers") if policy else None
    preferences = raw_preferences if isinstance(raw_preferences, dict) else {}
    routes: dict[str, Any] = {}

    pool = [
        worker
        for worker in workers
        if not allowed_workers or str(worker.get("worker_id", "")) in allowed_workers
    ]

    for role, requirement in normalize_role_requirements(policy).items():
        required = normalize_string_list(requirement.get("required_capabilities"))
        min_count = int(requirement.get("min_count", 1))

        def matches(worker: dict[str, Any], *, require_verified: bool) -> bool:
            if require_verified and not worker.get("verified"):
                return False
            capabilities = set(normalize_string_list(worker.get("route_capabilities")))
            return set(required).issubset(capabilities)

        verified_matches = [
            str(worker["worker_id"])
            for worker in pool
            if matches(worker, require_verified=True)
        ]
        candidate_matches = [
            str(worker["worker_id"])
            for worker in pool
            if worker.get("executable_present") and matches(worker, require_verified=False)
        ]
        preferred = normalize_string_list(preferences.get(role)) if isinstance(preferences, dict) else []
        selected = [worker_id for worker_id in preferred if worker_id in verified_matches]
        for worker_id in verified_matches:
            if len(selected) >= min_count:
                break
            if worker_id not in selected:
                selected.append(worker_id)

        routes[role] = {
            "required_capabilities": required,
            "min_count": min_count,
            "preferred_workers": preferred,
            "selected_workers": selected[:min_count],
            "verified_matches": sorted(verified_matches),
            "candidate_matches": sorted(candidate_matches),
            "status": "ready" if len(selected) >= min_count else "missing",
        }
    return {
        "routes": routes,
        "ready": all(route["status"] == "ready" for route in routes.values()) if routes else True,
    }


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
    requested = {item.strip() for item in raw_selection.split(",") if item.strip()}
    selected: set[str] = set()
    if ALL_CANDIDATES in requested:
        selected.update(
            str(worker["worker_id"])
            for worker in workers
            if worker.get("executable_present")
        )
        requested.remove(ALL_CANDIDATES)
    if ALL_RESOLVABLE in requested or "all-workers" in requested:
        selected.update(str(worker["worker_id"]) for worker in workers)
        requested.discard(ALL_RESOLVABLE)
        requested.discard("all-workers")
    selected.update(requested)
    return selected


def main() -> int:
    args = parse_args()
    warnings: list[str] = []
    runner = resolve_apxm_command(args, warnings)
    dekk_path = shutil.which("dekk")
    apxm_path = shutil.which("apxm")

    commands: dict[str, CommandResult] = {}
    if runner:
        commands["doctor"] = run(apxm_argv(runner, "doctor"), cwd=runner.get("cwd"))
        commands["agent_templates"] = run(
            apxm_argv(runner, "agent", "templates", "--json"),
            cwd=runner.get("cwd"),
        )
        commands["agent_list"] = run(
            apxm_argv(runner, "agent", "list", "--json"),
            cwd=runner.get("cwd"),
        )

    empty = CommandResult(False, [], None, "", "")
    templates = parse_json_records(commands.get("agent_templates", empty), "templates", "agents", "workers")
    agents = parse_json_records(commands.get("agent_list", empty), "agents", "workers", "profiles")

    if not runner:
        warnings.append("APXM command runner unavailable")
    elif not commands.get("doctor", CommandResult(False, [], None, "", "")).ok:
        warnings.append("APXM doctor command failed")

    has_apxm = bool(runner and commands.get("doctor", empty).ok)

    reachable_workers = collect_workers(agents, templates)
    base_executables = {"dekk"}
    if apxm_path:
        base_executables.add("apxm")
    cli_presence = {
        executable: shutil.which(executable)
        for executable in sorted(
            base_executables
            | {
                str(worker.get("executable", ""))
                for worker in reachable_workers
                if str(worker.get("executable", "")).strip()
            }
        )
    }

    verification_targets = select_workers_for_verification(reachable_workers, args.verify_workers)
    reachable_by_id = {str(worker["worker_id"]): worker for worker in reachable_workers}
    if runner and has_apxm and verification_targets:
        for worker_id in sorted(verification_targets):
            worker = reachable_by_id.get(worker_id)
            result = run(
                apxm_argv(runner, "agent", "test", worker_id),
                timeout=args.verify_timeout,
                cwd=runner.get("cwd"),
            )
            commands[f"agent_test:{worker_id}"] = result
            if worker is None:
                worker = {
                    "worker_id": worker_id,
                    "route_kind": "unknown",
                    "profile": worker_id,
                    "source": "explicit",
                    "command": "",
                    "executable": "",
                    "executable_present": False,
                    "verified": False,
                    "route_capabilities": [],
                    "capability_servers": [],
                    "warnings": ["worker was not present in APXM registry snapshot"],
                }
                reachable_workers.append(worker)
                reachable_by_id[worker_id] = worker
            if result.ok:
                worker["verified"] = True
                worker["verification"] = "spawn_test"
                worker["route_capabilities"] = route_capabilities_for(worker, bool(worker["executable_present"]), True)
            else:
                worker.setdefault("warnings", []).append("APXM spawn test failed")
                worker["verification"] = "failed"

    has_compile = has_apxm
    verified_workers = [worker for worker in reachable_workers if worker["verified"]]
    status, tier = classify_readiness(has_apxm=has_apxm, verified_workers=verified_workers)
    policy = load_policy(args.policy, warnings)
    role_routes = resolve_role_routes(reachable_workers, policy)

    output = {
        "status": status,
        "tier": tier,
        "apxm_cli_available": bool(apxm_path),
        "apxm_path": apxm_path,
        "apxm_command_kind": runner.get("kind") if runner else None,
        "apxm_command_cwd": runner.get("cwd") if runner else None,
        "dekk_cli_available": bool(dekk_path),
        "dekk_path": dekk_path,
        "dekk_apxm_available": has_apxm,
        "apxm_runtime_ready": has_apxm,
        "workflow_compile_ready": has_compile,
        "registered_agent_profiles": agents,
        "agent_templates": templates,
        "workers": reachable_workers,
        "workers_by_route_capability": index_workers_by_route_capability(reachable_workers),
        "verified_workers_by_route_capability": index_workers_by_route_capability(
            reachable_workers,
            verified_only=True,
        ),
        "role_routes": role_routes,
        "policy_loaded": policy is not None,
        "candidate_worker_count": sum(1 for worker in reachable_workers if worker["executable_present"]),
        "verified_worker_count": len(verified_workers),
        "current_working_directory": os.getcwd(),
        "cli_presence": cli_presence,
        "cli_presence_by_executable": cli_presence,
        "commands": {key: asdict(value) for key, value in commands.items()},
        "warnings": warnings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if status != "setup_required" else 2


if __name__ == "__main__":
    raise SystemExit(main())
