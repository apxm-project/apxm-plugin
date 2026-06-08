# APXM Policy Schema

Use compact JSON policies. Include only fields that matter for the run.

```json
{
  "budget_usd": 2.0,
  "deadline_seconds": 1800,
  "max_parallelism": 4,
  "worker_roles": {
    "planner": {
      "required_capabilities": ["read", "graph_author"],
      "min_count": 1
    },
    "executor": {
      "required_capabilities": ["execute"],
      "min_count": 1
    },
    "reviewer": {
      "required_capabilities": ["read"],
      "min_count": 1
    },
    "verifier": {
      "required_capabilities": ["execute"],
      "min_count": 1
    }
  },
  "preferred_workers": {
    "planner": ["worker-alpha"],
    "executor": ["worker-beta"]
  },
  "allowed_workers": ["worker-alpha", "worker-beta", "worker-gamma"],
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
- `worker_roles` describes required capabilities. It should not name providers unless a role truly requires a provider-specific feature.
- `preferred_workers` is optional. Use it for examples like Codex-as-planner and Claude-as-executor, but treat that as a preference over verified APXM profiles, not a hard runtime assumption.
- `allowed_workers` is optional. Omit it to let APXM choose from all verified workers.
- `write_mode` should be conservative for shared repos: `read_only`, `patch_proposal`, or `review_then_apply`.
- `merge_strategy` should stay orchestrator-owned until APXM has first-class cross-host merge support.
