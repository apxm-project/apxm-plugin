---
name: apxm-compile-and-execute
description: Use when validating, compiling, executing, running, analyzing, or explaining APXM workflow artifacts such as canonical .air workflows, Python frontend workflows, .apxmw workflow files, and compiled APXM objects.
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

- Canonical `.air`: validate, analyze, then execute or compile.
- Python frontend workflow: emit AIR, then validate/analyze/execute.
- `.apxmw`: use `dekk apxm workflow validate|analyze|execute` when available.
- `.apxmobj`: run directly.

## Commands

Use the available command surface that matches the artifact:

```bash
dekk apxm validate <workflow.air>
dekk apxm analyze <workflow.air>
dekk apxm explain <workflow.air>
dekk apxm compile <workflow.air> -o <workflow.apxmobj>
dekk apxm run <workflow.apxmobj>
dekk apxm execute <workflow.air>
dekk apxm workflow validate <workflow.apxmw>
dekk apxm workflow analyze <workflow.apxmw>
dekk apxm workflow execute <workflow.apxmw> --json
dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json
```

When calling the APXM binary directly instead of Dekk, the workflow execution subcommand may be `apxm workflow run <workflow.apxmw> --json`.

Use background workflow execution for long-running orchestration when the user needs to keep working while APXM records follow handles. The response should include `pid`, `session_dir`, `log_file`, and `command`.

Store generated artifacts under `.apxm/` unless the user or repo has a clearer convention.

## Rules

- Do not skip validation before execution.
- Do not pass structured data examples directly to `dekk apxm validate`; executable workflows should be canonical AIR or Python source that emits AIR.
- If validation fails, report the exact schema or policy gap and stop.
- If compile succeeds but execution fails, preserve both compile artifact and runtime error.
- Surface trace IDs, worker IDs, budgets, warnings, and generated files.
- Do not claim APXM execution happened when only local inspection happened.

## Result Shape

Return: `status`, `artifact_type`, `validated`, `compiled`, `executed`, `trace_id`, `artifacts`, `warnings`, and `next_action`.
