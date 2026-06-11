# APXM Autonomous Loop Contract

Use this contract when turning an idea like "run an agent in the background and call it when needed" into an APXM-owned workflow.

## Target Boundary

```text
[External systems]
   Discord, GitHub, cron, webhooks, files, queues, humans
          |
          v
[APXM OS connectors]
   provider auth, subscription, trigger sidecars, dedupe,
   retry, provider event normalization, event-to-skill routing
          |
          v
[APXM server execution gateway]
   skill execution, run/session IDs, retained events,
   checkpoints, cancellation, rollout/session evidence
          |
          v
[APXM runtime]
   AIR execution, autonomous nodes, workflow spawn,
   worker spawn/prompt/observe/stop, tool calls
          |
          v
[Workers]
   codex, claude, gemini, qwen, cursor, opencode, custom profiles
```

The plugin only teaches agents how to request this. APXM server, APXM OS, Dekk, and the runtime remain the execution authority.

## Caller Matrix

| Caller | Calls | Purpose | Follow/stop surface |
|---|---|---|---|
| APXM OS provider connector | `POST /v1/skills/{id}/execute` | Event-triggered loop from Discord, GitHub, cron, files, queues, or webhooks | `/v1/runs/{execution_id}/events`, checkpoint resume, run cancel |
| Agent host through MCP | Existing APXM MCP tools such as `goal_start`, `skill_call`, `run`, `trace_fetch` | Agent-initiated bounded orchestration, compile/run/follow when a human or parent agent asks | MCP result plus server run events when available |
| Dekk/APXM CLI | `dekk apxm workflow ...`, `dekk apxm session ...`, `dekk apxm rollout ...` | Local developer testing and detached workflow follow handles | session directory, process list, rollout/session inspect |
| Frontend | REST/SSE or generated workflow/trigger artifacts | Author specs and observe runs | server events, checkpoints, cancellation |
| Worker agent | APXM worker prompt/spawn route selected by policy | Execute one assigned role, propose a workflow, review, or verify | APXM runtime/process-table events, worker artifact |

No caller should bypass APXM validation/admission for worker-authored workflows or hide a long-running shell loop outside APXM.

## Canonical Loop

```text
[event]
   |
   v
[trigger]
   |
   v
[action]
   |
   v
[eval]
   |
   +--> [pass] ---------> [record + done or re-arm]
   |
   +--> [needs_more] ---> [feedback event/task] -> [trigger/action]
   |
   +--> [blocked] ------> [checkpoint]
   |
   +--> [unsafe] -------> [cancel + alert]
```

## Event Envelope

Use a stable event envelope before trigger matching:

```json
{
  "event_id": "evt_...",
  "source": "discord|github|timer|manual|apxm",
  "kind": "message.created|issue.opened|schedule.tick|run.failed",
  "subject": "repo/path/channel/thread/entity",
  "scope": "project.<name>",
  "occurred_at": "RFC3339 timestamp",
  "idempotency_key": "provider-native-id-or-hash",
  "actor": {
    "kind": "user|agent|system",
    "id": "provider-user-or-agent"
  },
  "payload": {},
  "trace": {
    "parent_execution_id": null,
    "parent_event_id": null
  }
}
```

Minimum fields: `source`, `kind`, `subject`, `idempotency_key`, and `payload`.

## Trigger Record

```json
{
  "trigger_id": "tri_project_curate",
  "enabled": true,
  "source": "discord",
  "kind": "message.created",
  "filter": {
    "all": [
      { "path": "payload.author.bot", "equals": false },
      { "path": "subject", "matches": "channel:project-.*" }
    ]
  },
  "policy": {
    "max_runs_per_minute": 10,
    "dedupe_window_ms": 86400000,
    "requires_approval": false,
    "max_usd": 1.50,
    "timeout_ms": 600000,
    "max_iterations": 5
  },
  "action": {
    "type": "skill|workflow|task",
    "target": "skill-id-or-path-or-queue",
    "inputs_from_event": {
      "message": "payload.content",
      "thread": "subject"
    }
  },
  "eval": {
    "type": "workflow|skill|builtin",
    "criteria": [
      "artifact exists",
      "declared checks pass",
      "no unresolved blocker"
    ]
  },
  "feedback": {
    "on_needs_more": "emit_event",
    "on_blocked": "checkpoint",
    "on_failed": "enqueue_task"
  }
}
```

## Action Types

- `skill`: call an installed APXM skill.
- `workflow`: launch a `.apxmw` workflow when the target APXM build exposes a workflow execution/follow surface.
- `task`: enqueue work for explicit claim/complete queue semantics.
- `agent_wake`: planned extension; only use when the target APXM build exposes it.
- `mcp_tool`: planned extension for allowlisted APXM MCP calls; only use when capability inventory confirms it.

## Plan Split And Worker Handoff

Split work by role and artifact, not by dumping one large prompt into every worker.

```text
[Objective or event]
        |
        v
[Classify required roles]
        |
        +--> planner: workflow or task split proposal
        +--> executor: bounded implementation/action
        +--> reviewer: critique and dissent
        +--> verifier: checks and evidence
        +--> synthesizer: final merge
        |
        v
[Resolve role policy against verified workers]
        |
        +--> [missing role] -> [return capability gap]
        |
        v
[Create compact worker briefs]
        |
        +--> objective
        +--> input refs, not whole repo dumps
        +--> constraints and policy
        +--> expected artifact
        +--> verification command or evidence
        +--> budget, timeout, stop conditions
        |
        v
[APXM executes workflow and records role outputs]
        |
        v
[Fan-in eval/synthesis]
```

Worker output should carry `role`, `worker_id`, `node_id` or step id, `status`, `artifact_refs`, `evidence_refs`, `warnings`, and `next_action`. A worker-authored workflow is only a proposal until APXM validates, compiles, and admits it.

## Eval Contract

Eval returns one of four states:

```json
{
  "status": "pass|needs_more|blocked|unsafe",
  "reason": "short reason",
  "evidence": [
    { "kind": "trace|artifact|test|event", "ref": "..." }
  ],
  "feedback_event": null
}
```

Only `needs_more` may automatically loop, and only while budget, timeout, and iteration limits allow it.

## Background Agent Lifecycle

```text
[APXM OS arms trigger]
          |
          v
[provider event arrives]
          |
          v
[APXM OS calls APXM server skill execution]
          |
          v
[server returns goal_id and execution_id]
          |
          +--> [follow events]
          |
          +--> [emit/call event]
          |
          +--> [checkpoint approval]
          |
          +--> [cancel/stop]
```

The loop should be inspectable through APXM server run events or APXM workflow session output. A background process without an APXM run ID or APXM OS trigger record is only a local process, not a governed autonomous loop.

## Native Orchestration Pass

Use `goal_start` when an agent has resolved one bounded event/task
into an explicit worker workflow and wants APXM to execute it:

```text
[caller/planner agent]
        |
        v
[goal_start once with explicit workers]
        |
        v
[orchestrator_sleep event]
        |
        v
[APXM workflow owns worker spawn + gate/eval + feedback]
        |
        v
[orchestrator_wake or terminal event]
        |
        v
[status confirms succeeded/failed]
```

The caller/planner should store `goal_id`, `execution_id`, `workflow_path`,
`bundle_dir`, and `session_dir`, then page `goal_events` with
`since = next_seq`. It
should not manually prompt workers after start. Real ACP workers require explicit
`admit_capabilities: ["SPAWN_AGENT"]`; provider names are policy bindings, not
requirements.

While asleep, the orchestrator can reconstruct live progress from
`workflow_started`, `workflow_step_started`, `workflow_step_completed`, and
`workflow_finished`. Treat step completion `session_dir` values as worker
evidence handles and wait for `orchestrator_wake` or terminal events before
continuing the loop.

## Interruptions

Interruptions are normal control-plane events, not exceptional prompt text.

```text
[Interrupt source]
        |
        +--> human cancel or approval denial
        +--> timeout or budget exhaustion
        +--> duplicate/superseding provider event
        +--> worker spawn/auth/protocol failure
        +--> failed eval or unsafe result
        +--> checkpoint needs human input
        |
        v
[Controller handles interrupt]
        |
        +--> APXM OS stops/re-arms provider trigger
        +--> APXM server cancel/checkpoint/resume when run id exists
        +--> task lease expires or task is completed failed
        +--> local workflow process is stopped through APXM/Dekk handle
        |
        v
[Record event + final state]
```

Each loop spec should define `interrupt_policy` with `on_cancel`, `on_timeout`, `on_duplicate`, `on_worker_failure`, `on_eval_failed`, and `on_checkpoint`. If the target APXM build lacks a stop/follow handle for the selected path, the skill must report that gap before launching.

## MVP Path

1. Keep external event loops in APXM OS.
2. Store trigger definitions beside workflow packs or skills as sidecars.
3. APXM OS normalizes events, dedupes them, applies deployment policy, and calls `POST /v1/skills/{id}/execute`.
4. Use existing run events, checkpoints, cancellation, rollout/session output, and task queues only when their current semantics fit.
5. Do not add APXM server trigger registry APIs for MVP; use APXM server as the execution gateway.

Existing or target MCP tools that may be useful after capability inventory confirms them:

```text
skill_call
run
trace_fetch
workflow_start
workflow_status
workflow_events
workflow_cancel
goal_start
goal_status
goal_events
goal_cancel
```

## Anti-Patterns

- Treating Claude, Codex, or any provider as required infrastructure.
- Running a hidden shell loop outside APXM and calling it autonomous.
- Triggering actions without dedupe, budget, timeout, and cancel controls.
- Hiding workflow semantics or sandbox policy inside provider connector code.
- Adding APXM server trigger APIs before APXM OS sidecar-to-skill execution is exhausted.
- Letting MCP tools contain orchestration business logic.
- Executing worker-authored workflows without APXM validation and admission.
