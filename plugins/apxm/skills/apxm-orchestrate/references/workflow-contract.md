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
