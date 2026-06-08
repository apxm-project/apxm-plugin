---
name: apxm-workers
description: Use when discovering, validating, selecting, or briefing APXM workers, including asking a verified worker to propose an APXM graph. Use whenever orchestration depends on which agents or LLM hosts are registered and ready.
---

# APXM Workers

Use this skill to reason about APXM workers from the APXM registry and preflight output. Do not infer readiness from brand names or assume Claude and Codex are installed.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

3. Treat the doctor snapshot as the source of truth for the current environment.
4. Before execution, request explicit spawn verification for the intended workers:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers codex,claude
```

Use `--verify-workers all-candidates` only when the user accepts adapter startup/network cost.

5. If available, inspect APXM worker state:

```bash
dekk apxm agent list --json
dekk apxm agent templates --json
```

## Selection Rules

- A present executable is a candidate, not a verified worker.
- A verified worker must be spawnable, promptable, observable, and stoppable by APXM.
- Prefer workers by capability and policy fit, not provider preference.
- Any verified worker may propose a `PlanGraph`, Python frontend workflow, or child workflow.
- Worker-authored graphs are untrusted until APXM validates, compiles, and admits them.
- When no verified execution route exists, return a setup plan instead of fabricating execution.

## Worker Brief

Use compact briefs:

- objective
- relevant paths or inputs
- constraints
- expected output artifact
- verification criteria
- budget and stop conditions

Do not send broad repository dumps or hidden reasoning.

## When To Load References

Load `references/worker-contract.md` when building a worker roster, capability matrix, or graph-authoring request.

## Result Shape

Return: `status`, `tier`, `selected_workers`, `capability_gaps`, `policy_constraints`, `graph_authoring_allowed`, and `warnings`.
