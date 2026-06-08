---
name: apxm-follow-workflow
description: Use when following, watching, replaying, archiving, or explaining APXM workflow/run progress through APXM OS observability surfaces such as watch, rollout list, rollout replay, rollout archive, process list, and workflow sessions.
---

# APXM Follow Workflow

Use this skill when the user wants to follow APXM work as it runs, inspect a completed workflow, or produce a traceable replay/archive. APXM OS has three follow modes: live server streaming, offline rollout replay, and emitted session inspection.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

3. If APXM is unavailable, return `setup_required`.
4. For live workflow/run progress, use:

```bash
dekk apxm watch <thread_id>
dekk apxm watch <thread_id> --expand <node_id>
```

5. For completed or offline runs, use:

```bash
dekk apxm rollout list --limit 20
dekk apxm rollout replay <thread_id>
dekk apxm rollout archive <thread_id> --output <path>
```

6. For local process visibility, use:

```bash
dekk apxm process list
```

7. For workflow/session output, use:

```bash
dekk apxm session list --limit 20
dekk apxm session inspect <session-id-or-path>
dekk apxm session diff <session-a> <session-b>
```

## Workflow Files

When the user is following APXM workflow files, prefer the workflow subcommands when Dekk exposes them:

```bash
dekk apxm workflow validate <workflow.apxmw>
dekk apxm workflow analyze <workflow.apxmw>
dekk apxm workflow execute <workflow.apxmw> --session-root <dir> --json
```

If Dekk does not expose `workflow`, call the APXM binary directly from the APXM repo:

```bash
./target/release/apxm workflow run <workflow.apxmw> --session-root <dir> --json
```

## Rules

- Do not confuse workflow following with workflow execution. Watching/replay is observability.
- Live `watch` requires `apxm-server` and a valid `thread_id`.
- `rollout replay` and `rollout archive` work offline from rollout storage.
- `session inspect` works from execution session output even when no rollout was recorded.
- Prefer `rollout archive` when the user needs reproducibility or handoff.
- Include the `thread_id`, server base, rollout source, and archive path in the final answer.
- If the workflow has no rollout yet, inspect emitted session output and explain what must create a rollout.

## When To Load References

Load `references/follow-contract.md` when designing a follow workflow, diagnosing observability gaps, or explaining live versus offline trace behavior.

## Result Shape

Return: `status`, `mode`, `thread_id`, `session_dir`, `live_watch`, `rollout_replay`, `archive`, `processes`, `warnings`, and `next_action`.
