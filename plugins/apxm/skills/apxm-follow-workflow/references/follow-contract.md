# APXM Follow Workflow Contract

## Modes

```text
[Need progress visibility]
        |
        v
[Choose the strongest available handle]
        |
   +-------------+-----------+-----------+-----------+
   |             |           |           |           |
   v             v           v           v           v
[server/MCP] [local .apxmw] [thread_id] [rollout id] [session dir]
   |             |           |           |           |
   v             v           v           v           v
[run id]     [background] [watch]    [replay]    [inspect]
   |             |           |           |           |
   v             v           v           v           v
[cancel/events] [pid/log] [expand]  [archive]   [child sessions]
   |             |           |           |           |
   +-------------+-----------+-----------+-----------+
        |
        v
[Report traceable status]
```

## Server/MCP Control

When an APXM server-managed `execution_id` is available, prefer server control over local process management. Use run detail, event stream, and cancel endpoints through Dekk/watch or MCP wrappers. MCP-started workflow work should still produce session files; use `session_dir` for offline inspection and `execution_id` for live control.

## Live Watch

`dekk apxm watch <thread_id>` connects to `GET /v1/runs/<thread_id>/events/stream` on `APXM_SERVER_BASE` or the APXM default server. Use `--expand <node_id>` to fetch one node detail before streaming.

## Offline Rollout

`dekk apxm rollout replay <thread_id>` reads persisted rollout JSONL from APXM rollout storage and renders the same tree shape as watch. `rollout archive` bundles the rollout JSONL, spilled blobs, and optional skill source into a reproducibility archive.

## Session Inspection

`dekk apxm session list` and `dekk apxm session inspect <session-id-or-path>` read execution session output emitted by `apxm run`, `apxm execute`, and `apxm workflow run`. Workflow roots should be listed as first-class sessions with `manifest.json`, `live.json`, `trace.ndjson`, `results.json`, and `metrics.json`; child step sessions carry graph-level node traces and outputs. Use sessions when no rollout exists or when the user wants a local/offline handle.

## Background Workflow

`dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json` starts a detached APXM child process and returns follow handles. The JSON should include `pid`, `session_dir`, `log_file`, and `command`. The workflow-root session should immediately contain `manifest.json`, `live.json`, `trace.ndjson`, and `background.json`; final `results.json` and `metrics.json` appear when the child completes. Use `dekk apxm process list` for process visibility and `dekk apxm session inspect <workflow-session-dir> --json` for state.

## Workflow File Lifecycle

```text
[workflow.apxmw]
      |
      v
[workflow validate]
      |
      v
[workflow analyze]
      |
      v
[workflow execute --session-root ...]
      |
      v
[workflow session dir]
      |
      +--> [watch live]
      |
      +--> [rollout replay/archive later]
      |
      +--> [session inspect workflow root]
      |
      +--> [inspect child step sessions]
```

## Background Lifecycle

```text
[workflow execute --background --session-root ...]
      |
      v
[APXM returns pid + session_dir + log_file]
      |
      +--> [process list shows running job]
      |
      +--> [session inspect reads live.json]
      |
      +--> [trace.ndjson records lifecycle/steps]
      |
      +--> [background.log captures child stdout/stderr]
      |
      v
[results.json + metrics.json when complete]
```

## Failure Modes

- No APXM binary: run APXM setup/install.
- No `apxm-server`: use offline rollout commands or start server.
- No rollout found: inspect the workflow-root session output, then run through a rollout-recording surface if regulatory replay is required.
- Background workflow missing `background.json`: APXM is too old or the workflow was launched manually with shell backgrounding; rerun through `workflow execute --background`.
- No Dekk `workflow` group: call `apxm workflow` directly or update `.dekk.toml`.
- No Dekk `session` group: call `apxm session` directly or update `.dekk.toml`.
