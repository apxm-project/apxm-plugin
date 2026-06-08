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
4. Use the direct APXM binary only as a developer escape hatch.

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
- `apxm_plan_as_graph`: natural-language task to validated plan graph, optionally executed.
- `apxm_trace_fetch`, `apxm_capability_list`, `apxm_skills_list`, `apxm_skill_call`: trace, capability, and skill surfaces.
- `apxm_workflow_start`, `apxm_workflow_status`, `apxm_workflow_events`, `apxm_workflow_cancel`: native workflow control when the APXM server advertises them.
- `apxm_orchestrate_start`: native one-pass execution of an explicit bounded worker DAG when the APXM HTTP MCP server advertises it.

## Workflow Launch Pattern

When the target server lists `apxm_orchestrate_start`, use it after a
caller/planner has resolved one bounded pass: call it once with `task`, optional
`context/event/trigger`, bounded `workers`, and workspace policy. For real ACP workers, include
`admit_capabilities: ["SPAWN_AGENT"]`. Store the returned `execution_id`,
`session_id`, `session_dir`, `workflow_path`, and `bundle_dir`; then follow with
`apxm_workflow_events` and `apxm_workflow_status`, and stop with
`apxm_workflow_cancel`. Do not manually prompt workers after start.

When the target server lists the native workflow tools, launch a `.apxmw` with `apxm_workflow_start`, then follow with `apxm_workflow_status` and `apxm_workflow_events`, and interrupt with `apxm_workflow_cancel`. Treat the returned `execution_id` as the live control handle and `session_dir` as the offline inspection handle.

Event consumers should keep workflow/session state from `workflow_started`,
`workflow_step_started`, `workflow_step_completed`, and `workflow_finished`.
`workflow_step_completed.payload.session_dir` is the child step session to
inspect; the top-level MCP `session_dir` remains the server-owned run session.

```text
[Agent]
   |
   v
[HTTP MCP apxm_workflow_start]
   |
   v
[APXM server validates workflow request + policy]
   |
   v
[WORKFLOW_SPAWN host bridge]
   |
   v
[workflow session dir + child step sessions]
```

If the target server does not list `apxm_workflow_start`, report the missing native workflow control surface. Use `dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json` only when a detached local CLI workflow is desired or the server control plane is unavailable.

## Workflow Tool Surface

Only call these tools when the target APXM server or MCP capability inventory confirms they exist.

- `apxm_workflow_start`: server-owned workflow launch; returns `execution_id`, `session_id`, `session_dir`.
- `apxm_workflow_status`: summary from run/session records.
- `apxm_workflow_events`: retained events or follow cursor.
- `apxm_workflow_cancel`: cancel by server-owned `execution_id`.

For readiness and worker roster checks, use local preflight
`scripts/apxm_doctor.py` and APXM agent registry commands such as
`dekk apxm agent list --json` until the target server advertises a native
worker-roster MCP tool.

External event intake, trigger sidecar loading, and provider listener lifecycle belong in APXM OS for the MVP. Do not create MCP trigger tools unless APXM core has a real server-side trigger registry.

## Current Plugin Boundary

Do not add `mcpServers` to `plugin.json` unless a real `.mcp.json` points at an APXM server or stdio MCP binary that exists in the target environment. The plugin distributes skills; APXM server/Dekk owns execution.

## Result Shape

Return: `status`, `mcp_surface`, `server_base`, `execution_id`, `session_id`, `session_dir`, `mapped_command`, `schema_notes`, `security_notes`, and `next_action`.
