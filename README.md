# APXM Plugin

APXM plugin packages reusable Codex and open-agent skills for APXM-native
orchestration workflows.

This repository is a Codex marketplace root. The installable plugin lives at
`plugins/apxm`.

## What It Provides

- `apxm-council`: run a traceable multi-perspective council.
- `apxm-orchestrate`: route large tasks through APXM graph execution.
- `apxm-workers`: select verified APXM workers and request worker-authored graphs.
- `apxm-skill-to-workflow`: convert agent skills into APXM workflow packs.
- `apxm-compile-and-execute`: validate, compile, run, and inspect APXM artifacts.
- `apxm-verify-workflow`: verify traces, artifacts, and declared evidence.
- `apxm-follow-workflow`: watch live runs and replay/archive APXM rollouts.
- `apxm-headless-hosts`: debug ACP/headless host profiles.
- `apxm-mcp`: keep APXM MCP wrappers thin over `dekk apxm`.

## Boundary

The plugin is not the APXM runtime. It teaches agents how to invoke APXM
correctly. APXM/Dekk remains the execution authority.

The plugin does not assume Claude or Codex are installed. Execute-capable skills
start from preflight, map workflow roles to capabilities, and select from
verified APXM profiles. Codex-as-planner and Claude-as-executor is an example
policy binding, not a requirement.

See `docs/APXM-PLUGIN-FLOW.md` for the plain-text flowchart and boundary model.

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
