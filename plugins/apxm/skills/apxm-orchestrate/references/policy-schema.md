# APXM Policy Schema

Use compact JSON policies. Include only fields that matter for the run.

```json
{
  "budget_usd": 2.0,
  "deadline_seconds": 1800,
  "max_parallelism": 4,
  "allowed_workers": ["codex", "claude"],
  "required_capabilities": ["read", "execute", "graph_author"],
  "write_mode": "review_then_apply",
  "network": "inherit_workspace_policy",
  "secrets": "deny",
  "merge_strategy": "orchestrator_final_patch",
  "verification": ["tests", "schema", "artifact_check"],
  "kill_switch": {
    "enabled": true,
    "on_budget_exceeded": "terminate_children",
    "on_repeated_failure": "stop_graph"
  }
}
```

Field notes:

- `budget_usd` is a live spending ceiling, not the static `max_cost` planning gate.
- `allowed_workers` is optional. Omit it to let APXM choose from verified workers.
- `write_mode` should be conservative for shared repos: `read_only`, `patch_proposal`, or `review_then_apply`.
- `merge_strategy` should stay orchestrator-owned until APXM has first-class cross-host merge support.
