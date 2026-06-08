---
name: apxm-mcp
description: Use when designing, reviewing, or using APXM MCP wrappers. The MCP layer must remain a thin transport over dekk apxm commands and must not contain orchestration business logic or secrets.
---

# APXM MCP

Use this skill for APXM MCP adapter work. The MCP layer is an interface, not the runtime. APXM/Dekk remains the execution authority.

## Rules

- MCP tools should be thin wrappers over `dekk apxm`.
- Do not store secrets in MCP arguments, logs, or generated artifacts.
- Do not duplicate APXM scheduling, policy, or worker admission logic in MCP.
- Return APXM trace IDs and structured command results.
- Keep long-running execution cancellable.
- Use explicit schemas for request and response payloads.

## Suggested Tool Surface

- `apxm.doctor`: calls `dekk apxm doctor`.
- `apxm.workers`: calls worker registry/list surfaces.
- `apxm.validate`: calls `dekk apxm validate`.
- `apxm.compile`: calls `dekk apxm compile`.
- `apxm.execute`: calls `dekk apxm execute`.
- `apxm.verify`: calls verification/trace surfaces.
- `apxm.orchestrate`: calls native orchestration or graph execution.
- `apxm.council`: calls native council or council workflow.

## Current Plugin Boundary

Do not add `mcpServers` to `plugin.json` unless a real `.mcp.json` and server implementation are present. Until then, this skill documents the adapter contract and prevents accidental logic drift into MCP.

## Result Shape

Return: `status`, `mcp_surface`, `mapped_dekk_command`, `schema_notes`, `security_notes`, and `next_action`.
