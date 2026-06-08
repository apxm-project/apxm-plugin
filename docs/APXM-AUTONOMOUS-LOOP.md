# APXM Autonomous Loop

This is a non-authoritative target contract for APXM-managed autonomous loops. The plugin only teaches agents how to request or design these loops; APXM server, APXM OS, Dekk, and runtime implementations remain authoritative.

## Core Idea

```text
[External/Internal Event]
          |
          v
[Normalize + Dedupe]
          |
          v
[Trigger Match]
          |
    +-----+-------------------+
    |                         |
    v                         v
[Record Ignored]      [Policy + Budget Gate]
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v
            [Checkpoint]          [Action Dispatch]
                                          |
             +----------------------------+----------------------------+
             |                            |                            |
             v                            v                            v
         [APXM skill]                 [AIR graph]              [workflow/task]
             |                            |                            |
             +----------------------------+----------------------------+
                                          |
                                          v
                                        [Eval]
                                          |
             +----------------------------+----------------------------+
             |                            |                            |
             v                            v                            v
       [Record success]          [Emit feedback event]        [Checkpoint/cancel]
             |                            |                            |
             v                            v                            v
          [Done]                    [Loop or re-arm]               [Human/stop]
```

The important shift is that "autonomous" means APXM-owned lifecycle, not a model-owned while loop. A worker can be Codex, Claude, Gemini, Qwen, Cursor, opencode, or a custom profile, but APXM owns verification, session IDs, event records, policy, and cancellation.

## Boundary

```text
[APXM plugin]
   Agent-facing skills, preflight guidance, and draft loop contracts.

[APXM implementation repos]
   Server, OS, runtime, frontend, Dekk, and worker adapters own actual behavior.
```

## Least-Overengineered MVP

```text
[Provider event]
          |
          v
[APXM OS connector + trigger sidecar]
          |
          v
[Dedupe + policy + skill input envelope]
          |
          v
[POST /v1/skills/{id}/execute]
          |
          v
[Server-owned execution_id + run events]
          |
          +--> [REST/SSE follow]
          |
          +--> [checkpoint/resume/cancel]
          |
          +--> [rollout/session evidence]
```

For the first real implementation, APXM OS should own external provider listeners, trigger sidecars, dedupe, retry, and event-to-skill routing. APXM server should stay the confined execution gateway and observability surface. MCP remains useful for agents that need to call existing server tools, but it should not become a second trigger engine.

## Capability Surfaces To Verify

- If available in the target APXM build: server run events through `/v1/runs`, `/v1/runs/:id/events`, `/events/stream`, and `/cancel`.
- If available in the target APXM build: task queues through `/v1/tasks`, queue claim, leases, and completion.
- If available in the target APXM build: checkpoints for pause/resume flows.
- If available in the target APXM build: agent registry routes such as `/v1/agents`, `/v1/agents/register`, and `/v1/receive`.
- If available in the target APXM build: MCP tools such as `apxm_run`, `apxm_dispatch`, `apxm_plan_as_graph`, trace, capability, and skill tools.
- If available in the target APXM build: runtime `AUTONOMOUS`, `mode=recv`, `WORKFLOW_SPAWN`, and `SPAWN_AGENT`.
- If available in the target APXM OS build: trigger sidecars such as `triggers.toml`.
- If available in the target Dekk/APXM build: local `.apxmw` background workflow handles.

## Common Gaps

```text
[Current practical path]
          |
          v
[Gaps to report honestly]
          |
          +--> APXM OS trigger sidecar loader missing
          +--> target skill pack has no trigger sidecar
          +--> target APXM server lacks skill execution or run events
          +--> no verified worker route for requested role
          +--> local background workflow has no APXM follow handle
          +--> budget governor shared across loop iterations and spawned workers
```

Do not add APXM server trigger APIs for the MVP just to make the diagram look complete. When APXM OS cannot arm the trigger or the target server cannot execute/follow the skill, report the concrete gap instead of claiming the loop is registered or armed.

## OS-Managed Loop Flow

```text
[Install skill/workflow pack]
          |
          v
[Load trigger sidecar in APXM OS]
          |
          v
[Provider event arrives]
          |
          v
[APXM OS dispatches skill execution]
          |
          v
[Server returns execution_id]
          |
          +--> [follow run events]
          |
          +--> [checkpoint/resume]
          |
          +--> [cancel/stop]
```

The heavy context should live in APXM artifacts and skill packs, not in the prompt. If a frontend authors this flow later, its first output should be skill/workflow artifacts plus APXM OS trigger metadata, not a parallel runtime.

## Draft Loop Spec Shape

```json
{
  "name": "project-curator",
  "event": {
    "source": "discord",
    "kind": "message.created",
    "subject": "channel:project"
  },
  "trigger": {
    "filter": [
      { "path": "payload.author.bot", "equals": false }
    ],
    "dedupe_key": "payload.id"
  },
  "action": {
    "type": "skill",
    "target": "discord-project-curate",
    "transport": "POST /v1/skills/{id}/execute",
    "role_bindings": {
      "planner": { "required_capabilities": ["read", "graph_author"] },
      "executor": { "required_capabilities": ["execute"] },
      "verifier": { "required_capabilities": ["execute"] }
    }
  },
  "eval": {
    "type": "builtin",
    "criteria": ["trace recorded", "artifact recorded", "no blocked status"]
  },
  "feedback": {
    "on_needs_more": "emit_event",
    "on_blocked": "checkpoint",
    "on_failed": "enqueue_task"
  },
  "policy": {
    "max_iterations": 5,
    "timeout_ms": 600000,
    "max_usd": 1.5,
    "requires_approval": false
  }
}
```

For missing APXM OS trigger loading, skill execution, run observation, or worker verification, report the gap instead of claiming the loop is registered or armed. A Codex planner and Claude executor is a demo policy; the production model is registered worker roles with required capabilities and late binding by APXM.
