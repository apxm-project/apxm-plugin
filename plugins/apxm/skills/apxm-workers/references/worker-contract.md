# APXM Worker Contract

## Worker Descriptor

```json
{
  "worker_id": "worker-alpha",
  "route_kind": "acp",
  "profile": "worker-alpha",
  "source": "custom",
  "command": "worker-alpha --acp",
  "executable": "worker-alpha",
  "executable_present": true,
  "verified": true,
  "capabilities": ["read", "write", "execute", "critique", "graph_author"],
  "capability_servers": [],
  "budget": {
    "budget_usd": 1.0,
    "timeout_seconds": 600
  },
  "warnings": []
}
```

## Readiness Tiers

- Tier 0: APXM unavailable.
- Tier 1: APXM available, no execution host verified.
- Tier 2: one execution route verified.
- Tier 3: multiple routes verified.
- Tier 4: budgeted headless hosts verified.

## Role Descriptors

```json
{
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
    }
  },
  "preferred_workers": {
    "planner": ["worker-alpha"],
    "executor": ["worker-beta"]
  }
}
```

`preferred_workers` is a tie-breaker, not an admission bypass. APXM must still verify the route and satisfy policy.

## Graph Authorship

Workers can propose:

- APXM `PlanGraph` JSON.
- Python frontend workflow source using APXM graph APIs.
- A child workflow request.

APXM must validate and compile the proposal before execution.
