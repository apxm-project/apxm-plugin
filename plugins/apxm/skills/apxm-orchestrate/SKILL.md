---
name: apxm-orchestrate
description: Use when a task should be decomposed, delegated to verified APXM workers, run as an APXM graph, or coordinated through fan-out/fan-in orchestration. Use for large code, research, analysis, or implementation workflows where APXM/Dekk should remain the execution authority.
---

# APXM Orchestrate

Use this skill to route substantial work through APXM. Do not simulate a worker swarm in prompt text when APXM can own the graph, policy checks, worker admission, execution, and trace.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. If preflight returns `setup_required`, stop and return the setup gap. Do not pretend orchestration ran.
4. Before fan-out execution, verify the intended workers:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers <worker-a>,<worker-b>
```

Use `--policy <policy.json>` when a policy declares `worker_roles`, `preferred_workers`, or `allowed_workers`; the doctor will report role routes and missing capabilities.

5. If the target APXM HTTP MCP inventory lists `apxm_orchestrate_start`, use
   the native server-owned path for natural-language task fan-out:

```text
apxm_orchestrate_start -> execution_id + workflow_path + bundle_dir
apxm_workflow_events   -> page retained events with since/next_seq
apxm_workflow_status   -> confirm running/succeeded/failed
apxm_workflow_cancel   -> stop by execution_id
```

Call `apxm_orchestrate_start` once only after the caller/planner has resolved a
bounded `workers` DAG for this pass. Include optional `context`, `event`,
`trigger`, and an explicit `workspace` policy. For real ACP workers, include
`admit_capabilities: ["SPAWN_AGENT"]`. After start, do not manually prompt
workers; APXM owns worker spawn, fan-in, gate/eval, feedback, events, and
cancellation for that pass.

Observe workflow lifecycle events in `apxm_workflow_events`: `workflow_started`,
`workflow_step_started`, `workflow_step_completed`, and `workflow_finished`.
Use `workflow_started.payload.session_dir` as the workflow-root session and each
`workflow_step_completed.payload.session_dir` as the child step session handle.
Wake the caller/planner only on `orchestrator_wake` or terminal workflow events.

6. If an executable canonical APXM graph already exists, prefer:

```bash
dekk apxm execute <workflow.air>
```

7. If native orchestration is not advertised, create a compact APXM request under `.apxm/requests/` and hand it to the compile/execute path. The request should contain only objective, constraints, desired artifacts, worker requirements, budget, and verification requirements. Do not pass PlanGraph JSON directly to `dekk apxm validate`; current APXM validation expects canonical `.air`.

If a native orchestration command is present in `dekk apxm --help`, it may replace the request handoff:

```bash
dekk apxm orchestrate --task "<brief objective>" --policy <policy.json>
```

## Delegation Rules

- Keep delegated prompts short. Send objectives, constraints, inputs, expected artifacts, and success checks.
- Use APXM worker discovery, not hard-coded assumptions about Claude, Codex, or any other host.
- Model the workflow by roles (`planner/orchestrator`, `executor`, `reviewer`, `critic`, `verifier`, `synthesizer`) and let APXM/policy bind those roles to verified worker profiles.
- Treat worker-authored graphs as proposals until APXM validates and adopts them.
- Require a budget policy before expensive or headless fan-out.
- Prefer fan-out for independent subtasks and fan-in for synthesis, critique, merge, or verification.
- Persist trace IDs and artifact paths in the final answer.

## When To Load References

- Load `references/workflow-contract.md` when designing the graph or explaining the orchestration flow.
- Load `references/policy-schema.md` when creating a policy object.

## Result Shape

Return: `status`, `workflow_id`, `trace_id`, `workers_used`, `artifacts`, `verification`, `budget`, `warnings`, and `next_action`.
