---
name: apxm-autonomous-agent
description: Use when designing APXM-owned event-triggered loop specs or workflow packs, and when identifying which APXM server/MCP/Dekk capabilities are missing. Do not use as the primary skill for generic MCP usage, workflow following, worker selection, or execution.
---

# APXM Autonomous Agent

Use this skill for APXM loops shaped like event -> trigger -> action -> eval -> feedback. The goal is not to make one model prompt another model forever. The goal is to let APXM own the loop, IDs, events, workers, policy, cancellation, and evidence.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. If execution or worker binding is required, discover workers by capability. Do not spawn-test all candidates for design-only work:

```bash
dekk apxm agent list --json
dekk apxm agent templates --json
```

Use `python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers <profiles>` only when an actual execution policy must bind verified workers.

4. Prefer the existing OS-to-server path for provider-triggered loops:

```text
[Need autonomous loop]
        |
        +--> [APXM OS connector exists]  -> [OS trigger sidecar calls server skill]
        |
        +--> [Agent calls APXM directly] -> [MCP/REST skill call, then follow run events]
        |
        +--> [No server]                 -> [APXM CLI workflow with follow handles]
```

5. If APXM OS cannot arm the trigger sidecar or the target APXM server cannot execute/follow the skill, create the loop spec or workflow pack and report the concrete gap. Do not claim the trigger was armed.

## Loop Shape

```text
[External or internal event]
          |
          v
[Normalize + dedupe]
          |
          v
[Match trigger]
          |
    +-----+------------------+
    |                        |
    v                        v
[ignored event]       [Policy + budget gate]
                             |
                   +---------+---------+
                   |                   |
                   v                   v
             [checkpoint]        [Action dispatch]
                                      |
             +------------------------+------------------------+
             |                        |                        |
             v                        v                        v
          [skill]                   [AIR]               [workflow/task]
             |                        |                        |
             +------------------------+------------------------+
                                      |
                                      v
                                    [Eval]
                                      |
             +------------------------+------------------------+
             |                        |                        |
             v                        v                        v
          [success]             [feedback event]          [blocked/unsafe]
             |                        |                        |
             v                        v                        v
 [record result + memory]       [loop or re-arm]       [checkpoint/cancel]
```

## Surfaces To Confirm

Confirm these with `apxm_doctor.py`, APXM capability inventory, or the target server before claiming they exist.

- Server/MCP: `run`, `prompt_as_workflow`, `goal_start`, `goal_status`, `goal_events`, `goal_cancel`, `workflow_start`, `workflow_status`, `workflow_events`, `workflow_cancel`, `trace_fetch`, `capability_list`, `skills_list`, `skill_get`, `skill_validate`, and `skill_call`.
- Native orchestration MCP: `goal_start` for a bounded worker workflow followed by `goal_events`, `goal_status`, and `goal_cancel` for wake and interruption.
- Server REST/SSE: `/v1/runs`, `/v1/runs/{execution_id}/events`, `/v1/runs/{execution_id}/events/stream`, `/v1/runs/{execution_id}/cancel`, `/v1/tasks`, `/v1/checkpoints`, `/v1/agents/register`, `/v1/receive`, `/v1/mcp`.
- Runtime: `AUTONOMOUS` plan/action/eval loops, `mode=recv` event polling, tool-enabled autonomous turns, `WORKFLOW_SPAWN`, `SPAWN_AGENT`, task claiming, checkpoints.
- APXM OS: external provider listeners, trigger sidecars such as Discord `triggers.toml`, dedupe, retry, and event-to-skill routing.
- Dekk/APXM CLI: local workflow validation, execution, background `.apxmw` follow handles, rollout replay, session inspect.

## Rules

- Prefer APXM server for long-running autonomous agents when it exposes the needed control surfaces: `execution_id`, `session_id`, retained events, cancellation, session roots, policy, worker admission, and rollout records.
- For a bounded agent-initiated parallel pass, call `goal_start` once and then sleep. Wake only through `orchestrator_wake`, terminal goal status, or cancel.
- Put provider adapters, external listeners, trigger sidecar loading, dedupe, and retry in APXM OS when that connector layer exists. Keep workflow semantics and sandbox internals out of connector code.
- MCP should be a thin agent-facing control surface. It should not duplicate APXM scheduling, trigger matching, or policy.
- A background agent must be a server-owned run or an APXM-launched background workflow. Do not use shell backgrounding as the control plane.
- Every loop must declare `max_iterations`, timeout, budget, cancel path, idempotency key, and approval/checkpoint conditions.
- Any worker may propose a workflow, but APXM must validate, compile, and admit it before execution.
- Do not assume Claude and Codex exist. They are example worker bindings only.
- Feedback should be a structured event, task, memory update, or checkpoint, not hidden prompt recursion outside APXM.

## When To Load References

Load `references/loop-contract.md` before writing a loop spec, trigger schema, workflow-pack contract, role-splitting plan, worker handoff contract, or interruption policy. For MCP/server implementation work, use `apxm-mcp` or APXM core docs instead.

## Result Shape

Return: `status`, `caller`, `control_plane`, `event_sources`, `triggers`, `actions`, `role_split`, `worker_briefs`, `evals`, `feedback`, `interrupt_policy`, `workers`, `run_ids`, `follow_surface`, `budget_policy`, `cancel_path`, `gaps`, and `next_action`.
