---
name: apxm-council
description: Use when a decision needs a traceable APXM council with multiple worker perspectives, dissent, critique, evidence, and a final recommendation. Use for architecture choices, risk reviews, plan reviews, and high-impact tradeoff analysis.
---

# APXM Council

Use this skill to ask APXM for a structured council. A council is not a loose prompt debate; APXM should select verified workers, collect independent views, preserve dissent, and produce a traceable recommendation.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

If `apxm` is not installed globally and Dekk needs the APXM worktree, set `APXM_WORKTREE=/path/to/apxm` or pass `--apxm-cwd /path/to/apxm`.

3. If no APXM route is ready, return `setup_required` with the doctor warnings.
4. Create a compact council request in `.apxm/requests/` and hand it to `apxm-compile-and-execute`.

If a native council command is present in `dekk apxm --help`, it may replace the request handoff:

```bash
dekk apxm council --task "<decision or question>" --policy <policy.json>
```

5. If a native orchestration command is present, a council can also route through it:

```bash
dekk apxm orchestrate --workflow council --task "<decision or question>" --policy <policy.json>
```

## Council Rules

- Ask for independent first-pass positions before synthesis.
- Include dissenting views. Do not report consensus when reviewers disagree.
- Separate evidence from judgment.
- Prefer small councils: 3 to 5 workers unless the user asks for more.
- Use APXM worker discovery instead of assuming specific hosts.
- Require a live budget policy for headless or paid worker routes.

## When To Load References

Load `references/council-contract.md` when creating a council request or evaluating council output.

## Result Shape

Return: `status`, `recommendation`, `majority_view`, `dissenting_views`, `evidence`, `confidence`, `trace_id`, `warnings`, and `follow_up`.
