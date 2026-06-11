---
name: apxm-workers
description: Use when discovering, validating, selecting, or briefing APXM workers, including asking a verified worker to propose an APXM workflow. Use whenever orchestration depends on which agents or LLM hosts are registered and ready.
---

# APXM Workers

Use this skill to reason about APXM workers from the APXM registry and preflight output. Do not infer readiness from brand names or assume Claude and Codex are installed.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. Treat the doctor snapshot as the source of truth for the current environment.
4. Before execution, request explicit spawn verification for the intended workers:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers <profile-a>,<profile-b>
```

Use `--verify-workers all-candidates` for every APXM-listed profile whose executable is on `PATH`. Use `--verify-workers all-resolvable` only when the user accepts broad adapter startup/network cost across the whole APXM registry.

5. If available, inspect APXM worker state:

```bash
dekk apxm agent list --json
dekk apxm agent templates --json
```

## Selection Rules

- A present executable is a candidate, not a verified worker.
- A verified worker must be spawnable, promptable, observable, and stoppable by APXM.
- Prefer workers by capability and policy fit, not provider preference.
- Treat Codex, Claude, Gemini, Cursor, Qwen, opencode, custom ACP profiles, and future headless routes as interchangeable candidates until APXM verification and policy select them.
- Any verified worker may propose canonical AIR, Python frontend workflow source, or a child workflow.
- Worker-authored workflows are untrusted until APXM validates, compiles, and admits them.
- When no verified execution route exists, return a setup plan instead of fabricating execution.

## Role Routing

Use roles to describe what the workflow needs, then bind workers late:

- `planner` or `planner/orchestrator`: read context and propose a workflow or task split.
- `executor`: run the admitted work under APXM policy.
- `reviewer`: inspect outputs and evidence.
- `critic`: preserve dissent and adversarial critique when policy requires it.
- `verifier`: run checks and confirm artifacts.
- `synthesizer`: merge evidence into the final result.

Example only: a policy may prefer particular profile IDs for `planner` and
`executor`, but the skill must accept any verified workers with the required
capabilities.

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

Load `references/worker-contract.md` when building a worker roster, route-capability matrix, or workflow-authoring request.

## Result Shape

Return: `status`, `tier`, `selected_workers`, `role_routes`, `capability_gaps`, `policy_constraints`, `workflow_authoring_allowed`, and `warnings`.
