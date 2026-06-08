# APXM Worker Contract

## Worker Descriptor

```json
{
  "worker_id": "codex",
  "route_kind": "acp",
  "profile": "codex",
  "command": "codex ...",
  "verified": true,
  "capabilities": ["read", "write", "execute", "critique", "graph_author"],
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

## Graph Authorship

Workers can propose:

- APXM `PlanGraph` JSON.
- Python frontend workflow source using APXM graph APIs.
- A child workflow request.

APXM must validate and compile the proposal before execution.
