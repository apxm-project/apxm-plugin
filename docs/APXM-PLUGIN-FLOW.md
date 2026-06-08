# APXM Plugin Flow

This plugin is the distribution layer for APXM orchestration skills. It teaches agents when and how to call APXM; it does not replace APXM/Dekk.

## Ideal Flow

```text
[User asks for big work]
          |
          v
[Any capable agent triggers APXM skill]
          |
          v
[Skill runs apxm_doctor preflight]
          |
          +--------------------+
          |                    |
          v                    v
[APXM route missing]    [APXM ready]
          |                    |
          v                    v
[Return setup gap]      [Discover verified workers]
          |                    |
          v                    v
[Install apxm or set]   [Map roles to capabilities]
[APXM_WORKTREE]                |
                               v
                    [Bind preferred workers if policy allows]
                               |
                               v
                    [Create compact task request]
                               |
                               v
                    [APXM validates policy]
                               |
          +--------------------+--------------------+
          |                                         |
          v                                         v
 [Rejected by policy]                      [Policy accepted]
          |                                         |
          v                                         v
 [Return fixable gaps]                  [APXM compiles graph]
                                                    |
                                                    v
                                      [APXM schedules workers]
                                                    |
                                                    v
                                      [Workers execute/propose]
                                                    |
                                                    v
[APXM verifies artifacts]
                                                    |
                                                    v
                                      [Follow via watch/rollout]
                                                    |
                                                    v
                                      [Traceable final result]
```

## Plugin Responsibilities

- Provide concise skills that route work to APXM.
- Discover readiness through `scripts/apxm_doctor.py`.
- Encourage compact request envelopes instead of giant prompts.
- Keep councils, workers, compile/execute, verification, and MCP boundaries explicit.
- Distribute the workflow as a Codex plugin marketplace repo while keeping APXM worker routing agent-agnostic.

## APXM Responsibilities

- Validate graphs and policy.
- Admit workers.
- Compile workflows.
- Schedule and supervise agents.
- Enforce budget, timeout, cancellation, and write policy.
- Persist traces and artifacts.
- Own server-side run/session IDs, event streams, cancellation, and session roots.
- Launch long local workflows in background child processes with follow handles when the server control plane is unavailable or not requested.
- Stream live run progress and replay archived rollouts.

## Control Plane Flow

```text
[Agent or frontend wants APXM execution]
            |
            v
[Discover APXM control surface]
            |
    +-------+-----------------------------+
    |                                     |
    v                                     v
[APXM server HTTP/MCP available]   [No server control plane]
    |                                     |
    v                                     v
[Agent uses MCP tools]             [Use Dekk/APXM CLI]
    |                                     |
    v                                     v
[Server owns run/session]          [CLI returns pid/session/log]
    |                                     |
    +----------------+--------------------+
                     |
                     v
      [Follow via events, rollout, or session files]
```

The preferred agent path is MCP over APXM server because the server can own many concurrent sessions with stable IDs, retained events, cancellation, rollout records, and server-controlled session roots. Dekk and the direct CLI remain important local fallbacks and developer tools, especially for detached `.apxmw` background runs.

## Worker Model

A worker can be any APXM-verified route that supports the requested capability. Codex planning and Claude execution is a useful example policy, not a runtime requirement:

```text
[APXM registry]
      |
      v
[Templates + custom registrations + future transports]
      |
      v
[Executable/auth/protocol checks]
      |
      v
[Spawn/prompt/observe/stop verification]
      |
      +--> [not verified] -> [candidate only]
      |
      v
[Verified worker]
      |
      +--> execute task
      +--> critique output
      +--> author graph proposal
      +--> call compiled skill workflow
```

Any worker-authored graph remains untrusted until APXM validates, compiles, and admits it.

## Role Routing Flow

```text
[Workflow objective]
       |
       v
[Required roles]
       |
       +--> planner: read + graph_author
       |
       +--> executor: execute
       |
       +--> reviewer: read + critique/evidence policy
       |
       +--> verifier: execute checks
       |
       v
[APXM doctor builds worker roster]
       |
       v
[Policy filters allowed workers]
       |
       v
[Preferred workers break ties]
       |
       +--> [role missing] -> [return capability/setup gap]
       |
       v
[APXM admits verified worker routes]
       |
       v
[Graph executes with trace, budget, stop policy]
```

Example policy binding:

```json
{
  "worker_roles": {
    "planner": { "required_capabilities": ["read", "graph_author"] },
    "executor": { "required_capabilities": ["execute"] }
  },
  "preferred_workers": {
    "planner": ["codex"],
    "executor": ["claude"]
  }
}
```

The same policy shape works with `gemini`, `cursor`, `qwen`, `opencode`, or a custom profile registered by `dekk apxm agent add <name> --command "<cmd>"`.

## Skill-To-Workflow Flow

```text
[Existing SKILL.md]
      |
      v
[Classify behavior]
      |
      v
[Extract trigger, inputs, policy, checks]
      |
      v
[Scaffold APXM workflow pack]
      |
      v
[Validate and compile with APXM]
      |
      +--> [compile failed] -> [conversion report]
      |
      v
[Reusable APXM workflow]
```

The original skill stays as the trigger layer. APXM becomes the graph execution layer.

## Follow Workflow Flow

```text
[APXM workflow/run starts]
      |
      v
[execution_id/thread_id/session emitted]
      |
      +----------------+----------------+----------------+
      |                |                |                |
      v                v                v                v
[server/MCP]   [background job] [live server] [offline/session]
      |                |                |                |
      v                v                v                v
[events/cancel] [pid/log/session] [apxm watch] [replay/archive/inspect]
      |                |                |                |
      +----------------+----------------+----------------+
                       |
                       v
             [traceable progress view]
```

Server/MCP workflow mode should return `execution_id`, `session_id`, and `session_dir` so APXM can control many concurrent sessions through run events and cancellation. Background workflow mode uses `dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json` and follows `pid`, `session_dir`, `log_file`, `background.json`, and workflow-root `trace.ndjson`. Live follow mode uses `dekk apxm watch <thread_id>`. Offline follow mode uses `dekk apxm rollout list`, `dekk apxm rollout replay <thread_id>`, and `dekk apxm rollout archive <thread_id>`.
