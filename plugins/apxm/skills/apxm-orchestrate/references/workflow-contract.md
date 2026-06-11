# APXM Orchestration Contract

APXM owns execution. Skills only prepare intent, call APXM/Dekk, and report traceable results.

## Flowchart

```text
[Human goal]
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
[Create resolved worker workflow or use existing canonical AIR]
    |
    v
[Choose execution surface]
    |
    +--> [CLI] -> [dekk apxm goal]
    |
    +--> [MCP] -> [goal_start once]
    |
    +--> [checked-in .apxmw] -> [workflow validate/analyze/run]
    |
    +--> [workflow synthesis] -> [prompt_as_workflow proposal]
    |
    v
[APXM validates policy + worker admission]
    |
    +--> [rejected] --> [return rejection + fixable fields]
    |
    v
[APXM compiles workflow AIR]
    |
    v
[APXM schedules verified workers]
    |
    v
[orchestrator sleeps; APXM retains events]
    |
    v
[Workers execute / propose child workflows]
    |
    v
[APXM fan-in synthesis + verification]
    |
    v
[workflow events/status wake orchestrator]
    |
    v
[Return trace ID, artifacts, evidence, warnings]
```

## Surface Selection

- `dekk apxm goal`: human or agent CLI path for one bounded worker workflow. It
  calls the server orchestration path, follows events by default, and exposes
  `--status`, `--events`, and `--cancel` for later control.
- `goal_start`: MCP path for the same server-owned pass when an
  MCP-capable agent has already resolved the worker workflow.
- `workflow_start`: MCP path for an existing `.apxmw` file.
- `dekk apxm workflow run` / `dekk apxm workflow execute`: local checked-in
  `.apxmw` execution. Use `--background` when the caller needs detached local
  follow handles instead of server-owned control.
- `prompt_as_workflow`: natural-language workflow synthesis to canonical AIR,
  with optional execution. It does not replace external-worker admission.

## Native MCP Contract

When the target APXM HTTP MCP server advertises `goal_start`, prefer
it for one-pass task-to-worker execution after the caller/planner has resolved
an explicit bounded worker workflow:

```json
{
  "task": "brief objective",
  "context": "optional repo/product/run context",
  "event": "optional triggering event",
  "trigger": "optional trigger rule or reason",
  "workspace": { "mode": "session|shared|git_worktree" },
  "workers": [
    { "id": "planner", "role": "plan this bounded pass", "profile": "worker-alpha" },
    { "id": "executor", "role": "execute the admitted work", "depends_on": ["planner"] },
    { "id": "critic", "role": "preserve dissent and missing evidence", "depends_on": ["executor"] }
  ],
  "admit_capabilities": ["SPAWN_AGENT"]
}
```

The response returns `goal_id`, `execution_id`, `session_id`, `session_dir`,
`workflow_path`, `bundle_dir`, `artifacts`, `plan`, `planning`, `control`, and
goal sleep/wake handles. Store those handles. The caller/planner agent should
then go idle; APXM owns worker spawning, prompts, fan-in, gate/eval, feedback,
session output, and events.

Follow by paging:

```json
goal_events({ "goal_id": "...", "since": 0, "limit": 100 })
```

Advance `since` to each response's `next_seq`. `done: true` only means the
current event page is exhausted; it is not goal completion. Wake when an event
has `payload.kind` equal to `orchestrator_wake`, or when status is terminal,
then confirm with:

```json
goal_status({ "goal_id": "..." })
```

For observability, also track `workflow_started`, `workflow_step_started`,
`workflow_step_completed`, and `workflow_finished`. The workflow-root session is
`workflow_started.payload.session_dir`; each completed step should expose its
child `session_dir` for workflow/artifact inspection. Use those session
paths when handing off evidence or debugging a worker.

Stop only through:

```json
goal_cancel({ "goal_id": "..." })
```

## Compact Worker Brief

Use this shape inside worker prompts, policies, or workflow specs. It is not a
separate execution API; native bounded execution goes through `dekk apxm goal`
or `goal_start`.

```json
{
  "objective": "Brief user-facing objective.",
  "context": ["Only the relevant file paths, docs, or constraints."],
  "expected_artifacts": ["patch", "report", "trace"],
  "verification": ["tests", "schema", "artifact_check"],
  "budget": { "usd": 2.0, "max_parallelism": 4 },
  "stop_conditions": ["policy rejection", "budget exhausted", "verification failed"]
}
```

`goal` is the human-facing word. Do not send a `goal` field to
`goal_start`; map human intent to `task` for the native MCP tool or
to `objective` only inside local specs and worker briefs.

## Admission Rules

- A CLI on `PATH` is only a candidate. A verified worker is one APXM can spawn, prompt, supervise, and stop.
- Child workflows proposed by workers are untrusted until APXM validates them.
- Executable workflow proposals must be canonical `.air` or Python frontend source that emits AIR before `dekk apxm validate`, `analyze`, `explain`, `compile`, or `execute`.
- The final answer must distinguish APXM-verified work from locally inspected but unverified artifacts.
