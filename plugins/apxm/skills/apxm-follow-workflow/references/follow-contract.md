# APXM Follow Workflow Contract

## Modes

```text
[Need progress visibility]
        |
        v
[Do we have a live thread_id + server?]
        |
   +----+----+
   |         |
   v         v
[yes]      [no]
   |         |
   v         v
[watch]  [rollout/session list]
   |         |
   v         v
[expand] [replay/archive/inspect]
   |         |
   +----+----+
        |
        v
[Report traceable status]
```

## Live Watch

`dekk apxm watch <thread_id>` connects to `GET /v1/runs/<thread_id>/events/stream` on `APXM_SERVER_BASE` or the APXM default server. Use `--expand <node_id>` to fetch one node detail before streaming.

## Offline Rollout

`dekk apxm rollout replay <thread_id>` reads persisted rollout JSONL from APXM rollout storage and renders the same tree shape as watch. `rollout archive` bundles the rollout JSONL, spilled blobs, and optional skill source into a reproducibility archive.

## Session Inspection

`dekk apxm session list` and `dekk apxm session inspect <session-id-or-path>` read execution session output emitted by `apxm run`, `apxm execute`, and `apxm workflow run`. Workflow roots should be listed as first-class sessions with `manifest.json`, `live.json`, `results.json`, and `metrics.json`; child step sessions carry graph-level node traces and outputs. Use sessions when no rollout exists or when the user wants a local/offline handle.

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

## Failure Modes

- No APXM binary: run APXM setup/install.
- No `apxm-server`: use offline rollout commands or start server.
- No rollout found: inspect the workflow-root session output, then run through a rollout-recording surface if regulatory replay is required.
- No Dekk `workflow` group: call `apxm workflow` directly or update `.dekk.toml`.
- No Dekk `session` group: call `apxm session` directly or update `.dekk.toml`.
