---
name: apxm-autonomous-agent
description: Use when designing, registering, running, following, or stopping APXM autonomous agents that react to events, triggers, background loops, task queues, or feedback cycles through APXM server, APXM OS, MCP, REST/SSE, or Dekk.
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

3. Discover workers by capability, not brand:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers all-candidates
dekk apxm agent list --json
dekk apxm agent templates --json
```

4. Prefer the server control plane:

```text
[Need autonomous loop]
        |
        +--> [APXM server/MCP available] -> [MCP for agents, REST/SSE for UI]
        |
        +--> [APXM OS connector exists]  -> [OS receives provider event, server owns run]
        |
        +--> [No server]                 -> [Dekk/APXM background workflow fallback]
```

5. If no native trigger registry exists in the current APXM build, create the loop spec or workflow pack and report `trigger_registry_missing`. Do not claim the server armed the trigger.

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
          [skill]                  [graph]              [workflow/task]
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

## Current Useful APXM Surfaces

- Server/MCP: `apxm_run`, `apxm_dispatch`, `apxm_plan_as_graph`, `apxm_trace_fetch`, capability and skill inventory/call tools.
- Server REST/SSE: `/v1/runs`, `/v1/runs/:id/events`, `/events/stream`, `/cancel`, `/v1/tasks`, `/v1/checkpoints`, `/v1/agents/register`, `/v1/receive`, `/v1/mcp`.
- Runtime: `AUTONOMOUS` plan/action/eval loops, `mode=recv` event polling, tool-enabled autonomous turns, `WORKFLOW_SPAWN`, `SPAWN_AGENT`, task claiming, checkpoints.
- APXM OS: external provider listeners and trigger sidecars, such as Discord `triggers.toml`.
- Dekk/APXM CLI: local workflow validation, execution, background `.apxmw` follow handles, rollout replay, session inspect.

## Rules

- APXM server is the preferred owner for long-running autonomous agents because it can own `execution_id`, `session_id`, retained events, cancellation, session roots, policy, worker admission, and rollout records.
- APXM OS should own provider adapters and external listeners. It should feed normalized events into APXM server instead of embedding runtime policy in connector code.
- MCP should be a thin agent-facing control surface. It should not duplicate APXM scheduling, trigger matching, or policy.
- A background agent must be a server-owned run or an APXM-launched background workflow. Do not use shell backgrounding as the control plane.
- Every loop must declare `max_iterations`, timeout, budget, cancel path, idempotency key, and approval/checkpoint conditions.
- Any worker may propose a graph, but APXM must validate, compile, and admit it before execution.
- Do not assume Claude and Codex exist. They are example worker bindings only.
- Feedback should be a structured event, task, memory update, or checkpoint, not hidden prompt recursion outside APXM.

## When To Load References

Load `references/loop-contract.md` before writing a loop spec, trigger schema, server API proposal, APXM OS connector plan, or background-agent lifecycle plan.

## Result Shape

Return: `status`, `control_plane`, `event_sources`, `triggers`, `actions`, `evals`, `feedback`, `workers`, `run_ids`, `follow_surface`, `budget_policy`, `cancel_path`, `gaps`, and `next_action`.
