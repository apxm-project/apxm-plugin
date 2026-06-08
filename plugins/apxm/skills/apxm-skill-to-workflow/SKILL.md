---
name: apxm-skill-to-workflow
description: Use when converting a Codex skill, Claude/Superpowers-style skill, or local agent procedure into an APXM workflow pack with graph, policy, compile targets, verification, and conversion notes.
---

# APXM Skill To Workflow

Use this skill to convert an agent skill into an APXM workflow. The output should preserve the skill's trigger and procedural knowledge while moving orchestration, worker admission, policy, and traceability into APXM.

## Quick Start

1. Identify the source skill directory and read only its `SKILL.md` plus directly relevant resources.
2. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
3. Run preflight:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

4. Prefer the native converter when present:

```bash
dekk apxm skills workflowize <skill-dir> --out <target-dir>
```

5. If the converter is not available, scaffold a workflow pack manually and mark it `scaffolded`, not `compiled`.

## Workflow Pack Shape

Create these files in the target directory:

- `skill.toml`: source skill metadata, trigger, required inputs, and policy defaults.
- `workflow.py`: APXM Python frontend workflow or graph builder.
- `skill.air.json`: compiled or hand-authored APXM graph target when possible.
- `conversion_report.json`: decisions, unsupported features, validation status, and next action.

## Conversion Rules

- Keep the original skill as the human-facing trigger layer.
- Move repeatable branching, fan-out, verification, and execution into APXM.
- Preserve safety boundaries and setup checks.
- Do not require Claude or Codex unless the source skill explicitly requires them.
- Do not claim a workflow is compiled unless APXM validation and compile succeeded.
- If a skill contains broad instructions, convert only the stable workflow skeleton and leave judgment to workers.

## When To Load References

Load `references/conversion-contract.md` before writing `skill.toml`, `workflow.py`, or `conversion_report.json`.

## Result Shape

Return: `status`, `source_skill`, `workflow_pack`, `compiled`, `validated`, `unsupported_features`, `artifacts`, and `next_action`.
