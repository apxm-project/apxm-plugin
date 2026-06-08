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

3. Prefer APXM verification surfaces when present:

```bash
dekk apxm verify <trace-or-artifact>
dekk apxm trace show <trace-id> --json
dekk apxm artifacts list <trace-id> --json
```

4. If APXM verification commands are unavailable, inspect local artifacts and report `not_apxm_verified`.

## Verification Checklist

- Graph/schema validation passed.
- Policy admission was recorded.
- Worker outputs map to graph nodes.
- Required artifacts exist and are non-empty.
- Tests, linters, or domain checks ran when declared.
- Budget and timeout data were recorded for headless routes.
- Fan-in output cites worker evidence and dissent where relevant.
- No worker-authored child graph executed without APXM validation.

## Result Shape

Return: `status`, `trace_id`, `verified`, `checks`, `failures`, `warnings`, `artifact_paths`, and `next_action`.
