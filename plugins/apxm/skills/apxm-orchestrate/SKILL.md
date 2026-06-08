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

3. If preflight returns `setup_required`, stop and return the setup gap. Do not pretend orchestration ran.
4. Before fan-out execution, verify the intended workers:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers codex,claude
```

5. If an executable canonical APXM graph already exists, prefer:

```bash
dekk apxm execute <workflow.air>
```

6. For a natural-language task, prefer the native orchestration surface when present:

```bash
dekk apxm orchestrate --task "<brief objective>" --policy <policy.json>
```

If that command is not available yet, produce a compact APXM request under `.apxm/requests/` and hand it to the compile/execute path. The request should contain only objective, constraints, desired artifacts, worker requirements, budget, and verification requirements. Do not pass PlanGraph JSON directly to `dekk apxm validate`; current APXM validation expects canonical `.air`.

## Delegation Rules

- Keep delegated prompts short. Send objectives, constraints, inputs, expected artifacts, and success checks.
- Use APXM worker discovery, not hard-coded assumptions about Claude, Codex, or any other host.
- Treat worker-authored graphs as proposals until APXM validates and adopts them.
- Require a budget policy before expensive or headless fan-out.
- Prefer fan-out for independent subtasks and fan-in for synthesis, critique, merge, or verification.
- Persist trace IDs and artifact paths in the final answer.

## When To Load References

- Load `references/workflow-contract.md` when designing the graph or explaining the orchestration flow.
- Load `references/policy-schema.md` when creating a policy object.

## Result Shape

Return: `status`, `workflow_id`, `trace_id`, `workers_used`, `artifacts`, `verification`, `budget`, `warnings`, and `next_action`.
