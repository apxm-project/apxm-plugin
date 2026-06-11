---
name: apxm-skill-to-workflow
description: Use when converting a Codex skill, Claude/Superpowers-style skill, or local agent procedure into an APXM workflow pack with AIR source, policy, compile targets, verification, and conversion notes.
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

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

4. The current APXM CLI does not expose a native skill-to-workflow converter. Scaffold a workflow pack manually and mark it `scaffolded`, not `compiled`.
5. Validate and compile only the artifacts that APXM supports today:

```bash
dekk apxm workflow validate <target-dir>/workflow.apxmw
dekk apxm workflow analyze <target-dir>/workflow.apxmw
dekk apxm validate <target-dir>/skill.air
dekk apxm compile <target-dir>/skill.air -o <target-dir>/skill.apxmobj
```

Skip commands for artifacts that the conversion did not create.

## Workflow Pack Shape

Create these files in the target directory:

- `skill.toml`: source skill metadata, trigger, required inputs, and policy defaults.
- `workflow.py`: APXM Python frontend workflow source.
- `skill.air`: compiled or hand-authored canonical APXM workflow target when possible.
- `workflow.apxmw`: APXM multi-step workflow file when the source skill maps better to workflow steps than a single AIR unit.
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
