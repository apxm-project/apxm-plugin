---
name: apxm-follow-workflow
description: Use when following, watching, replaying, archiving, or explaining APXM workflow/run progress through APXM OS observability surfaces such as watch, rollout list, rollout replay, rollout archive, process list, and workflow sessions.
---

# APXM Follow Workflow

Use this skill when the user wants to follow APXM work as it runs, launch a workflow in the background, inspect a completed workflow, or produce a traceable replay/archive. APXM OS has four follow modes: background workflow handles, live server streaming, offline rollout replay, and emitted session inspection. Workflow runs should expose a top-level session directory with `manifest.json`, `live.json`, `trace.ndjson`, `results.json`, and `metrics.json`, plus child step sessions.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. If APXM is unavailable, return `setup_required`. Use the same APXM command route the doctor selected (`apxm` or `dekk apxm`).
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

7. For background workflow launch and local follow handles, use:

```bash
dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json
dekk apxm session inspect <workflow-session-dir> --json
dekk apxm process list --json
```

The background response should include `pid`, `session_dir`, `log_file`, and `command`. The workflow-root session should contain `background.json`, `trace.ndjson`, `live.json`, and final `results.json` when complete.

8. For workflow/session output, use:

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
dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json
dekk apxm session list --session-root <dir> --json
dekk apxm session inspect <workflow-session-dir> --json
```

If Dekk does not expose `workflow`, call the APXM binary directly from the APXM repo:

```bash
./target/release/apxm workflow run <workflow.apxmw> --session-root <dir> --json
./target/release/apxm workflow run <workflow.apxmw> --background --session-root <dir> --json
```

## Rules

- Do not confuse workflow following with workflow execution. Watching/replay is observability.
- Live `watch` requires `apxm-server` and a valid `thread_id`.
- `rollout replay` and `rollout archive` work offline from rollout storage.
- `session inspect` works from execution session output even when no rollout was recorded.
- Workflow-root sessions are the canonical offline follow handle for `.apxmw` runs; child step sessions provide graph-level detail.
- Background `.apxmw` runs should be launched by APXM itself, not by shelling out with `&`, so APXM can return `pid`, `session_dir`, `log_file`, and record `background.json`.
- Prefer `rollout archive` when the user needs reproducibility or handoff.
- Include the `thread_id`, server base, rollout source, and archive path in the final answer.
- If the workflow has no rollout yet, inspect emitted session output and explain what must create a rollout.

## When To Load References

Load `references/follow-contract.md` when designing a follow workflow, diagnosing observability gaps, or explaining live versus offline trace behavior.

## Result Shape

Return: `status`, `mode`, `pid`, `thread_id`, `session_dir`, `log_file`, `live_watch`, `rollout_replay`, `archive`, `processes`, `warnings`, and `next_action`.
