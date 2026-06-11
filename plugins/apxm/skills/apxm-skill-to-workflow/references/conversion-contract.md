# APXM Skill Conversion Contract

## Classification

Classify the source skill before conversion:

- `single_route`: deterministic sequence with one worker or tool route.
- `fanout_fanin`: independent subtasks followed by synthesis.
- `council`: independent perspectives, critique, dissent, recommendation.
- `verify`: artifact, trace, schema, or test verification.
- `adapter`: thin wrapper over a CLI, API, or MCP surface.

## `skill.toml`

```toml
name = "source-skill-name"
kind = "fanout_fanin"
source = "./path/to/source/skill"
entrypoint = "workflow.py"

[policy]
budget_usd = 1.0
max_parallelism = 3
write_mode = "review_then_apply"

[inputs]
task = "string"
context_paths = "string[]"
```

## `conversion_report.json`

```json
{
  "status": "scaffolded",
  "source_skill": "source-skill-name",
  "workflow_kind": "fanout_fanin",
  "compiled": false,
  "validated": false,
  "unsupported_features": [],
  "notes": [],
  "next_action": "Run dekk apxm validate and compile when APXM is ready."
}
```

## Guardrails

- The converted workflow should call other APXM skills only through explicit workflow nodes.
- Keep prompts brief and artifact-oriented.
- Record anything that stayed manual in `unsupported_features`.
- Use canonical `skill.air` for executable workflow artifacts.
- Use `workflow.apxmw` for multi-step workflow files that need Dekk `workflow validate|analyze|execute` or direct APXM `workflow validate|analyze|run`.
