# APXM Autonomous Loop

This is the target architecture for APXM-managed autonomous agents: event -> trigger -> action -> eval -> feedback, with APXM server and APXM OS owning the control plane instead of individual agent prompts.

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

## Ownership

```text
[APXM plugin]
   Teaches agents how to request APXM loops.
   Ships skills, flowcharts, and contracts.

[APXM OS]
   Connects to providers such as Discord, GitHub, cron, file watchers, and webhooks.
   Normalizes external events and forwards them to APXM server.

[APXM server]
   Owns event intake, trigger registry, policy, budget, run/session IDs,
   retained events, SSE, cancellation, checkpoints, task queues, and worker admission.

[APXM runtime]
   Executes graphs, autonomous nodes, workflow spawn, agent spawn,
   tool calls, eval nodes, and feedback actions.

[Dekk/APXM CLI]
   Developer and fallback surface for validation, workflow execution,
   background `.apxmw` jobs, session inspect, watch, and rollout replay.
```

## Why Server/MCP First

```text
[Agent wants to start or call loop]
          |
          v
[APXM server HTTP MCP]
          |
          v
[Server-owned run/session]
          |
          +--> [REST/SSE follow from frontend]
          |
          +--> [MCP status/events for agents]
          |
          +--> [cancel/checkpoint/resume]
          |
          +--> [rollout/session archive]
```

MCP is the right agent-facing interface because Claude, Codex, and other hosts can all call it. REST/SSE is the right UI and watcher interface. The CLI stays useful, but it should not be the primary control plane for always-on agents because local processes do not naturally provide durable IDs, trigger state, policy, or multi-session supervision.

## What Exists Now

- Server events: `/v1/runs`, `/v1/runs/:id/events`, `/events/stream`, `/cancel`.
- Server tasks: `/v1/tasks`, queue claim, leases, completion.
- Server checkpoints: durable pause/resume with wake of parked runtime nodes.
- Server agent registry: `/v1/agents`, `/v1/agents/register`, `/v1/receive`.
- Server MCP: `apxm_run`, `apxm_dispatch`, `apxm_plan_as_graph`, trace, capability, and skill tools.
- Runtime autonomous op: plan/action/eval loop, `converse=true`, and `mode=recv` for event polling inside a graph.
- Runtime workflow spawn: server runtime can execute `WORKFLOW_SPAWN` graphs through the driver bridge.
- APXM OS trigger sidecars: existing packs can ship `triggers.toml` read by APXM OS.
- Dekk workflow background mode: local `.apxmw` jobs can return process and session follow handles.

## What Is Missing

```text
[Current building blocks]
          |
          v
[Missing durable layer]
          |
          +--> native server event intake API
          +--> server trigger registry
          +--> trigger action dispatcher
          +--> background agent lifecycle API
          +--> MCP wrappers for emit/register/start/status/stop
          +--> budget governor shared across loop iterations and spawned workers
```

The existing `AUTONOMOUS mode=recv` is useful, but it is not the whole product. It parks inside a graph and polls an endpoint. The durable product layer should let APXM server or APXM OS receive events, match triggers, start or wake loops, follow them, and stop them.

## Ideal Background Agent Flow

```text
[Register worker profiles]
          |
          v
[Verify spawn/prompt/observe/stop]
          |
          v
[Register autonomous loop]
          |
          v
[Start background agent]
          |
          v
[Server returns execution_id + session_id]
          |
          +--> [event emit / trigger]
          |
          +--> [follow events]
          |
          +--> [checkpoint/resume]
          |
          +--> [cancel/stop]
```

The front end can author this visually: source, filter, action, eval, feedback, policy, and worker role bindings. The agent-facing skill can then say something compact like: "dekk apxm execute this workflow" or "call APXM MCP to register/start this loop." The heavy context lives in APXM artifacts, not in the prompt.

## Minimal Product Contract

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
    "type": "workflow",
    "target": ".apxm/workflows/project-curate.apxmw",
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

## Practical MVP

```text
Phase 1: Plugin contract
   Add APXM autonomous-agent skill and docs.
   Teach agents to design loops without assuming a provider.

Phase 2: Workflow packs
   Store trigger/action/eval/feedback specs beside APXM workflows.
   Use existing APXM OS sidecars where provider listeners already exist.

Phase 3: Server API
   Add /v1/events, /v1/triggers, and background agent lifecycle endpoints.
   Use existing run bus, task queues, checkpoints, agent registry, and cancellation.

Phase 4: MCP tools
   Expose thin wrappers: apxm_event_emit, apxm_trigger_register,
   apxm_agent_start, apxm_agent_status, apxm_agent_stop.

Phase 5: Frontend authoring
   Visual builder writes the loop spec and compiles it to APXM workflow/graph artifacts.
```

The first implementation should avoid hard-coding Claude or Codex. A Codex planner and Claude executor is a demo policy. The production model is registered worker roles with required capabilities and late binding by APXM.
