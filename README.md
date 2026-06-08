# APXM Plugin

APXM plugin packages reusable agent-facing skills for APXM-native
orchestration workflows. It is distributed through the Codex plugin format, but
the runtime worker model is APXM-agent agnostic.

This repository is a Codex marketplace root. The installable plugin lives at
`plugins/apxm`.

## What It Provides

- `apxm-council`: run a traceable multi-perspective council.
- `apxm-orchestrate`: create a bounded worker DAG, execute it through APXM,
  and wait on workflow events/status.
- `apxm-autonomous-agent`: design APXM-owned event-triggered loop specs and identify missing control-plane capabilities.
- `apxm-workers`: select verified APXM workers and request worker-authored graphs.
- `apxm-skill-to-workflow`: convert agent skills into APXM workflow packs.
- `apxm-compile-and-execute`: validate, compile, run, and inspect APXM artifacts.
- `apxm-verify-workflow`: verify traces, artifacts, and declared evidence.
- `apxm-follow-workflow`: launch/follow background workflows, watch live runs, and replay/archive APXM rollouts.
- `apxm-headless-hosts`: debug ACP/headless host profiles.
- `apxm-mcp`: prefer APXM server/MCP for controllable sessions, with Dekk for local developer execution.

## Boundary

The plugin is not the APXM runtime. It teaches agents how to invoke APXM
correctly. APXM server/Dekk remains the execution authority.

The plugin does not assume any specific agent host is installed. Execute-capable skills
start from preflight, map workflow roles to capabilities, and select from
verified APXM profiles. Provider-specific pairings are example policy bindings,
not requirements.

See `docs/APXM-PLUGIN-FLOW.md` for the plain-text plugin flowchart and boundary model. See `docs/APXM-AUTONOMOUS-LOOP.md` for the autonomous event loop architecture.

## Local Check

```bash
python3 plugins/apxm/scripts/apxm_doctor.py
```

If APXM is available only through a Dekk worktree, pass it explicitly:

```bash
python3 plugins/apxm/scripts/apxm_doctor.py --apxm-cwd /path/to/apxm
```

## Install As A Marketplace

From Codex, add this repository as a plugin marketplace once it is published or
available locally:

```bash
codex plugin marketplace add /path/to/apxm-plugin
```

Then install the `APXM` plugin from the plugin browser.
