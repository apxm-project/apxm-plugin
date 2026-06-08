---
name: apxm-mcp
description: Use when designing, reviewing, or using APXM MCP/server control-plane wrappers. Prefer APXM server HTTP MCP for controllable runs and sessions; keep MCP thin and free of orchestration business logic or secrets.
---

# APXM MCP

Use this skill for APXM MCP adapter work. The MCP layer is an interface, not the runtime. APXM server/Dekk remains the execution authority.

## Control Plane Order

1. Prefer APXM server HTTP MCP (`POST /v1/mcp`) when available. Agents call MCP tools; APXM server owns `execution_id`, `session_id`, server-controlled session directories, event streams, run records, cancellation, policy, and worker admission.
2. Use APXM server REST/SSE directly when building a frontend, Dekk wrapper, or watcher. REST/SSE is the UI/control surface; MCP is the agent-facing surface.
3. Use `dekk apxm` CLI when no server is available or when launching the current local background `.apxmw` workflow mode.
4. Use the direct APXM binary only as a developer fallback.

## Rules

- MCP tools should be thin wrappers over APXM server/Dekk capabilities.
- Do not store secrets in MCP arguments, logs, or generated artifacts.
- Do not duplicate APXM scheduling, policy, or worker admission logic in MCP.
- Return APXM `execution_id`, `session_id`, `session_dir`, trace IDs, and structured command results.
- Keep long-running execution cancellable.
- Do not accept arbitrary client-supplied `session_root`; session roots are server-controlled.
- Use explicit schemas for request and response payloads.

## Existing Useful Surface

- `apxm_validate`, `apxm_compile`, `apxm_ops_list`: compile-only MCP tools.
- `apxm_run`: compile and run canonical AIR through server admission.
- `apxm_dispatch`: constrained fan-out spec lowered to AIR and executed by APXM.
- `apxm_plan_as_graph`: natural-language task to validated plan graph, optionally executed.
- `apxm_trace_fetch`, `apxm_capability_list`, `apxm_skills_list`, `apxm_skill_call`: trace, capability, and skill surfaces.

## Workflow Launch Pattern

Until a native `apxm_workflow_start` MCP tool exists, launch a `.apxmw` through server/MCP by wrapping it in a tiny AIR graph with one `WORKFLOW_SPAWN` node and calling `apxm_run` with a server-safe `session_id`. Do not include `session_root` in the graph or MCP arguments.

```text
[Agent]
   |
   v
[HTTP MCP apxm_run]
   |
   v
[APXM server validates AIR + policy]
   |
   v
[WORKFLOW_SPAWN host bridge]
   |
   v
[workflow session dir + child step sessions]
```

Use `dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json` only when a detached local CLI workflow is desired or the server control plane is unavailable.

## Target Tool Surface

- `apxm_workflow_start`: server-owned workflow launch; returns `execution_id`, `session_id`, `session_dir`.
- `apxm_workflow_status`: summary from run/session records.
- `apxm_workflow_events`: retained events or follow cursor.
- `apxm_workflow_cancel`: cancel by server-owned `execution_id`.
- `apxm_workers`: verified worker roster and capabilities.
- `apxm_doctor`: local readiness and route discovery.

## Current Plugin Boundary

Do not add `mcpServers` to `plugin.json` unless a real `.mcp.json` points at an APXM server or stdio MCP binary that exists in the target environment. The plugin distributes skills; APXM server/Dekk owns execution.

## Result Shape

Return: `status`, `mcp_surface`, `server_base`, `execution_id`, `session_id`, `session_dir`, `mapped_command`, `schema_notes`, `security_notes`, and `next_action`.
