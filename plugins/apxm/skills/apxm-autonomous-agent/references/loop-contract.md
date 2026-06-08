# APXM Autonomous Loop Contract

Use this contract when turning an idea like "run an agent in the background and call it when needed" into an APXM-owned workflow.

## Boundary

```text
[External systems]
   Discord, GitHub, cron, webhooks, files, queues, humans
          |
          v
[APXM OS connectors]
   provider auth, subscription, provider event normalization
          |
          v
[APXM server control plane]
   event intake, trigger registry, policy, run/session IDs,
   event retention, task queue, checkpoints, cancellation
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
    "type": "skill|air|workflow|task|agent_wake",
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
- `air`: execute a canonical `.air` graph.
- `workflow`: launch a `.apxmw` workflow, preferably through server-owned workflow start when available.
- `task`: enqueue work for external workers to claim through `/v1/tasks`.
- `agent_wake`: deliver a message or event to a registered long-lived agent.
- `mcp_tool`: call an allowlisted APXM MCP tool; keep this thin.

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
[register worker/agent]
          |
          v
[start background loop]
          |
          v
[server returns execution_id + session_id]
          |
          +--> [follow events]
          |
          +--> [emit/call event]
          |
          +--> [checkpoint approval]
          |
          +--> [cancel/stop]
```

The agent should be inspectable through server run events or APXM workflow session output. A background process without an APXM run ID is only a local process, not a governed autonomous agent.

## MVP Path

1. Use APXM OS or a small connector to normalize provider events.
2. Store trigger definitions beside workflow packs or skills while native server trigger storage is missing.
3. Dispatch to APXM server through MCP or REST.
4. Use existing run events, tasks, checkpoints, agent registration, and workflow background sessions for observability.
5. Add native server APIs when ready:

```text
POST /v1/events
GET  /v1/triggers
POST /v1/triggers
POST /v1/triggers/{id}/enable
POST /v1/triggers/{id}/disable
POST /v1/agents/background/start
GET  /v1/agents/background/{id}
POST /v1/agents/background/{id}/stop
```

Recommended MCP tool wrappers:

```text
apxm_event_emit
apxm_trigger_register
apxm_trigger_list
apxm_agent_start
apxm_agent_status
apxm_agent_stop
apxm_workflow_start
apxm_workflow_events
apxm_workflow_cancel
```

## Anti-Patterns

- Treating Claude, Codex, or any provider as required infrastructure.
- Running a hidden shell loop outside APXM and calling it autonomous.
- Triggering actions without dedupe, budget, timeout, and cancel controls.
- Letting APXM OS connectors decide runtime policy.
- Letting MCP tools contain orchestration business logic.
- Executing worker-authored graphs without APXM validation and admission.
