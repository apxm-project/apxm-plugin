# APXM Council Contract

## Request

```json
{
  "kind": "apxm.council.request",
  "question": "Decision or tradeoff to evaluate.",
  "context": ["Only the relevant facts, files, and constraints."],
  "perspectives": ["builder", "reviewer", "operator"],
  "policy": {
    "budget_usd": 1.5,
    "max_parallelism": 3,
    "write_mode": "read_only",
    "verification": ["evidence_check"]
  }
}
```

## Flowchart

```text
[Question]
    |
    v
[APXM selects verified council workers]
    |
    v
[Independent positions]
    |
    v
[Critique pass]
    |
    v
[Synthesis with dissent preserved]
    |
    v
[Recommendation + evidence + trace]
```

## Output Requirements

- `recommendation`: one concrete recommendation or `no_decision`.
- `majority_view`: main reasoning and evidence.
- `dissenting_views`: disagreements with rationale.
- `confidence`: low, medium, or high, with reason.
- `trace_id`: APXM trace if execution occurred.
- `warnings`: missing evidence, missing worker diversity, budget limits, or APXM setup gaps.
