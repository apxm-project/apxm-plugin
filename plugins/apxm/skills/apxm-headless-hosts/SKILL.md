---
name: apxm-headless-hosts
description: Use when configuring, diagnosing, or validating APXM ACP/headless agent hosts, noninteractive CLI routes, worker templates, prompt envelopes, budgets, timeouts, and kill-switch behavior.
---

# APXM Headless Hosts

Use this skill to debug APXM host readiness. Do not equate an installed CLI with a verified APXM worker.

## Quick Start

1. Resolve `PLUGIN_ROOT` as the directory two levels above this skill directory.
2. Run:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py"
```

3. Verify specific candidate routes before using them:

```bash
python3 "$PLUGIN_ROOT/scripts/apxm_doctor.py" --verify-workers codex,claude
```

4. Inspect APXM host state when available:

```bash
dekk apxm agent templates --json
dekk apxm agent list --json
dekk apxm doctor
```

## Host Readiness Checks

- Executable is on `PATH`.
- Authentication is configured outside the prompt.
- Noninteractive or ACP mode is supported.
- APXM can spawn the process.
- APXM can send a prompt and receive a bounded response.
- APXM can capture stdout, stderr, exit status, and trace metadata.
- APXM can enforce timeout, cancellation, and budget stop.
- The route has a clear write policy for repository changes.

## Budget Rule

Headless cost envelopes must be live and verified before expensive orchestration. Static plan estimates are not enough for a Tier 4 host.

## Result Shape

Return: `status`, `tier`, `candidate_hosts`, `verified_hosts`, `failed_checks`, `budget_ready`, and `next_action`.
