---
name: apxm-compile-and-execute
description: Use when validating, compiling, executing, running, analyzing, or explaining APXM workflow artifacts such as .air graphs, PlanGraph JSON, Python frontend workflows, and compiled APXM objects.
---

# APXM Compile And Execute

Use this skill as the direct APXM/Dekk execution path. It should be boring and traceable: validate first, compile when needed, execute with policy, then report artifacts.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. For execution, run:

```bash
"$PLUGIN_ROOT/scripts/ensure_apxm_cli.sh"
```

3. Identify the artifact type:

- `.air.json` or PlanGraph JSON: validate, analyze, then execute or compile.
- Python frontend workflow: compile to APXM graph first.
- `.apxmobj`: run directly.

## Commands

Use the available command surface that matches the artifact:

```bash
dekk apxm validate <workflow.air.json>
dekk apxm analyze <workflow.air.json>
dekk apxm explain <workflow.air.json>
dekk apxm compile <workflow.air.json> -o <workflow.apxmobj>
dekk apxm run <workflow.apxmobj>
dekk apxm execute <workflow.air.json>
```

Store generated artifacts under `.apxm/` unless the user or repo has a clearer convention.

## Rules

- Do not skip validation before execution.
- If validation fails, report the exact schema or policy gap and stop.
- If compile succeeds but execution fails, preserve both compile artifact and runtime error.
- Surface trace IDs, worker IDs, budgets, warnings, and generated files.
- Do not claim APXM execution happened when only local inspection happened.

## Result Shape

Return: `status`, `artifact_type`, `validated`, `compiled`, `executed`, `trace_id`, `artifacts`, `warnings`, and `next_action`.
