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
   graph execution, autonomous nodes, workflow spawn,
   worker spawn/prompt/observe/stop, tool calls
          |
          v
[Workers]
   codex, claude, gemini, qwen, cursor, opencode, custom profiles
```

The plugin only teaches agents how to request this. APXM server, APXM OS, Dekk, and the runtime remain the execution authority.

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
    "type": "graph|skill|builtin",
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
[server returns execution_id]
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

## MVP Path

1. Keep external event loops in APXM OS.
2. Store trigger definitions beside workflow packs or skills as sidecars.
3. APXM OS normalizes events, dedupes them, applies deployment policy, and calls `POST /v1/skills/{id}/execute`.
4. Use existing run events, checkpoints, cancellation, rollout/session output, and task queues only when their current semantics fit.
5. Do not add APXM server trigger registry APIs for MVP; use APXM server as the execution gateway.

Existing or target MCP tools that may be useful after capability inventory confirms them:

```text
apxm_skill_call
apxm_run
apxm_trace_fetch
apxm_workflow_start
apxm_workflow_events
apxm_workflow_cancel
```

## Anti-Patterns

- Treating Claude, Codex, or any provider as required infrastructure.
- Running a hidden shell loop outside APXM and calling it autonomous.
- Triggering actions without dedupe, budget, timeout, and cancel controls.
- Hiding graph semantics or sandbox policy inside provider connector code.
- Adding APXM server trigger APIs before APXM OS sidecar-to-skill execution is exhausted.
- Letting MCP tools contain orchestration business logic.
- Executing worker-authored graphs without APXM validation and admission.
