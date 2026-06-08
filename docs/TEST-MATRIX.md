# APXM Plugin Test Matrix

Use this matrix to test the plugin without collapsing distinct readiness states into one vague pass/fail.

## Packaging

```bash
python3 -m json.tool plugins/apxm/.codex-plugin/plugin.json >/dev/null
python3 -m unittest discover -s tests -p 'test_*.py'
codex plugin add apxm@apxm
```

Expected: plugin manifest JSON is valid, doctor classification tests pass, and Codex installs the APXM plugin from the configured marketplace.

## APXM Runtime Setup

From the APXM repo:

```bash
dekk apxm setup
dekk apxm install --no-interactive --verbose
dekk apxm doctor
```

Expected: APXM compiler is ready. Bubblewrap may warn on machines without host support; that is a sandbox limitation, not a plugin packaging failure.

## Worker Discovery

```bash
python3 plugins/apxm/scripts/apxm_doctor.py
python3 plugins/apxm/scripts/apxm_doctor.py --apxm-cwd /path/to/apxm
python3 plugins/apxm/scripts/apxm_doctor.py --verify-workers all-candidates
python3 plugins/apxm/scripts/apxm_doctor.py --verify-workers <profile-a>,<profile-b>
dekk apxm agent templates --json
dekk apxm agent list --json
```

Expected: APXM templates and custom registrations are visible. If `apxm` is not installed globally, use `--apxm-cwd` or `APXM_WORKTREE` so Dekk runs from the APXM worktree. Candidate executables do not count as verified workers until an APXM spawn test succeeds. When two distinct profiles spawn successfully, doctor should report Tier 3 unless live budget enforcement is also verified.

Optional role policy check:

```bash
python3 plugins/apxm/scripts/apxm_doctor.py --policy /path/to/policy.json --verify-workers <planner>,<executor>
```

Expected: `role_routes` reports selected verified workers or concrete missing capabilities. Provider names are preferences, not assumptions.

## Worker Spawn

```bash
dekk apxm agent test <profile>
```

Expected: each route either becomes verified by APXM or reports a concrete spawn/auth/protocol failure.

## Canonical AIR

```bash
dekk apxm validate crates/tools/apxm-server/skills/apxm-os-discord-curate/skills/discord-project-answer/skill.air
dekk apxm analyze crates/tools/apxm-server/skills/apxm-os-discord-curate/skills/discord-project-answer/skill.air
dekk apxm explain crates/tools/apxm-server/skills/apxm-os-discord-curate/skills/discord-project-answer/skill.air
dekk apxm compile crates/tools/apxm-server/skills/apxm-os-discord-curate/skills/discord-project-answer/skill.air -o /tmp/apxm-discord-project-answer.apxmobj
```

Expected: canonical `.air` validates, analyzes, explains, and compiles. PlanGraph JSON examples are proposals and should not be passed directly to `dekk apxm validate`.

## Workflow Following

```bash
dekk apxm process list
dekk apxm session list --limit 20
dekk apxm session inspect <session-id-or-path>
dekk apxm rollout list --limit 20
dekk apxm watch <thread_id>
dekk apxm rollout replay <thread_id>
dekk apxm rollout archive <thread_id> --output /tmp/apxm-rollout-<thread_id>.tar.gz
dekk apxm workflow validate <workflow.apxmw>
dekk apxm workflow analyze <workflow.apxmw>
dekk apxm workflow execute <workflow.apxmw> --session-root <dir> --json
dekk apxm workflow execute <workflow.apxmw> --background --session-root <dir> --json
```

Expected: live follow mode uses `watch` against a running server and thread id. Session follow mode inspects emitted session directories. Offline rollout mode uses rollout replay/archive after a rollout exists.

For foreground `.apxmw` execution, the returned `session_dir` must itself contain `manifest.json`, `live.json`, `trace.ndjson`, `results.json`, and `metrics.json`; `dekk apxm session list --session-root <dir>` should list the workflow root, and `session inspect <workflow-session-dir> --json` should expose `results.step_results` with child step session paths.

For background `.apxmw` execution, the returned JSON must include `pid`, `session_dir`, `log_file`, and `command`; the workflow-root session should immediately contain `manifest.json`, `live.json`, `trace.ndjson`, and `background.json`, then `results.json` and `metrics.json` after completion. `dekk apxm process list` should expose the job while it is running.

## Autonomous Loops

```bash
python3 plugins/apxm/scripts/apxm_doctor.py --verify-workers all-candidates
dekk apxm agent list --json
dekk apxm agent templates --json
dekk apxm process list --json
```

Expected: loop design starts from verified workers and APXM control surfaces, not from hard-coded provider names. If the current APXM build lacks native server trigger APIs, the plugin should produce a loop spec or workflow pack and report the trigger registry gap instead of claiming that the server armed the trigger. Background loop tests should expose either server-owned `execution_id`/`session_id` or APXM-launched workflow background handles, never a raw shell `&` process as the control plane.
