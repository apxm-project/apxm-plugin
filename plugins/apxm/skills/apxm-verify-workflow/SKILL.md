---
name: apxm-verify-workflow
description: Use when verifying APXM workflow traces, artifacts, schema validity, test evidence, worker outputs, budget records, or whether an APXM run actually satisfied its declared acceptance criteria.
---

# APXM Verify Workflow

Use this skill after APXM execution or when reviewing a workflow pack. Verification is evidence-based; file existence alone is not proof of success.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. Use APXM's current validation and evidence surfaces. Use the same APXM command route the doctor selected (`apxm` or `dekk apxm`):

```bash
dekk apxm validate <workflow.air>
dekk apxm analyze <workflow.air>
dekk apxm session inspect <session-id-or-path> --json
dekk apxm rollout replay <thread_id>
```

Use `dekk apxm workflow validate <workflow.apxmw>` and `dekk apxm workflow
analyze <workflow.apxmw>` for workflow files. When following server-owned work
through MCP, use `trace_fetch`, `workflow_status`, and
`workflow_events` if the target server advertises them.

4. If APXM verification evidence is unavailable, inspect local artifacts and report `not_apxm_verified`.

## Verification Checklist

- AIR/workflow schema validation passed.
- Policy admission was recorded.
- Worker outputs map to workflow nodes.
- Required artifacts exist and are non-empty.
- Tests, linters, or domain checks ran when declared.
- Budget and timeout data were recorded for headless routes.
- Fan-in output cites worker evidence and dissent where relevant.
- No worker-authored child AIR/workflow executed without APXM validation.

## Result Shape

Return: `status`, `trace_id`, `verified`, `checks`, `failures`, `warnings`, `artifact_paths`, and `next_action`.
