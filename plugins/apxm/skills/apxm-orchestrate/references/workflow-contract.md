# APXM Orchestration Contract

APXM owns execution. Skills only prepare intent, call APXM/Dekk, and report traceable results.

## Flowchart

```text
[User goal]
    |
    v
[APXM skill selects workflow type]
    |
    v
[apxm_doctor preflight]
    |
    +--> [setup_required] --> [return missing APXM/runtime/worker gap]
    |
    v
[Create compact request or use existing canonical graph]
    |
    v
[Native MCP available?]
    |
    +--> [yes] -> [apxm_orchestrate_start once]
    |                 |
    |                 v
    |          [sleep until workflow events/status wake]
    |
    v
[APXM validates policy + worker admission]
    |
    +--> [rejected] --> [return rejection + fixable fields]
    |
    v
[APXM compiles graph]
    |
    v
[APXM schedules verified workers]
    |
    v
[Workers execute / propose child graphs]
    |
    v
[APXM fan-in synthesis + verification]
    |
    v
[Return trace ID, artifacts, evidence, warnings]
```

## Native MCP Contract

When the target APXM HTTP MCP server advertises `apxm_orchestrate_start`, prefer
it for task-to-worker orchestration:

```json
{
  "task": "brief objective",
  "context": "optional repo/product/run context",
  "event": "optional triggering event",
  "trigger": "optional trigger rule or reason",
  "workspace": { "mode": "session|shared|git_worktree" },
  "workers": [
    { "id": "planner", "role": "plan", "profile": "any-verified-profile" },
    { "id": "executor", "role": "execute", "depends_on": ["planner"] }
  ],
  "admit_capabilities": ["SPAWN_AGENT"]
}
```

The response returns `execution_id`, `session_id`, `session_dir`,
`workflow_path`, `bundle_dir`, `plan`, `control`, and `orchestration`. Store
those handles. The orchestrator agent should then go idle; APXM owns worker
spawning, prompts, fan-in, gate/eval, feedback, session output, and events.

Follow by paging:

```json
apxm_workflow_events({ "execution_id": "...", "since": 0, "limit": 100 })
```

Advance `since` to each response's `next_seq`. `done: true` only means the
current event page is exhausted; it is not workflow completion. Wake when an
event has `payload.kind` equal to `orchestrator_wake`, `execute_complete`,
`error`, or `turn_aborted`, then confirm with:

```json
apxm_workflow_status({ "execution_id": "..." })
```

For observability, also track `workflow_started`, `workflow_step_started`,
`workflow_step_completed`, and `workflow_finished`. The workflow-root session is
`workflow_started.payload.session_dir`; each completed step should expose its
child `session_dir` for graph/artifact/workflow inspection. Use those session
paths when handing off evidence or debugging a worker.

Stop only through:

```json
apxm_workflow_cancel({ "execution_id": "..." })
```

## Minimal Request Envelope

Use this shape when no native `dekk apxm orchestrate` surface is available yet:

```json
{
  "kind": "apxm.orchestrate.request",
  "objective": "Brief user-facing objective.",
  "context": ["Only the relevant file paths, docs, or constraints."],
  "desired_artifacts": ["patch", "report", "trace"],
  "worker_requirements": {
    "min_routes": 1,
    "capabilities": ["read", "execute", "graph_author"]
  },
  "policy": {
    "budget_usd": 2.0,
    "max_parallelism": 4,
    "write_mode": "review_then_apply",
    "verification": ["tests", "schema", "artifact_check"]
  }
}
```

## Admission Rules

- A CLI on `PATH` is only a candidate. A verified worker is one APXM can spawn, prompt, supervise, and stop.
- Child graphs proposed by workers are untrusted until APXM validates them.
- PlanGraph JSON is a proposal/interchange format. Lower it to canonical `.air` before `dekk apxm validate`, `analyze`, `explain`, `compile`, or `execute`.
- The final answer must distinguish APXM-verified work from locally inspected but unverified artifacts.
