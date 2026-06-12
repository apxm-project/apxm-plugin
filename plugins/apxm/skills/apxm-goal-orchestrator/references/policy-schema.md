# APXM Policy Schema

Use compact JSON policies. Include only fields that matter for the run.

```json
{
  "budget_usd": 2.0,
  "deadline_seconds": 1800,
  "max_parallelism": 4,
  "worker_roles": {
    "planner": {
      "required_capabilities": ["read", "workflow_author"],
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
    "critic": {
      "required_capabilities": ["read", "critique"],
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
    "on_repeated_failure": "stop_workflow"
  }
}
```

Field notes:

- `budget_usd` is a live spending ceiling, not the static `max_cost` planning gate.
- `worker_roles` describes required capabilities. It should not name providers unless a role truly requires a provider-specific feature.
- `reviewer` is a read/evidence role. Use `critic` only when the run needs explicit dissent or adversarial critique capability.
- `preferred_workers` is optional. Use neutral registered profile IDs such as `worker-alpha`; provider-specific names are preferences over verified APXM profiles, not runtime assumptions.
- `allowed_workers` is optional. Omit it to let APXM choose from all verified workers.
- `write_mode` should be conservative for shared repos: `read_only`, `patch_proposal`, or `review_then_apply`.
- `merge_strategy` should stay APXM fan-in owned until APXM has first-class cross-host merge support.
