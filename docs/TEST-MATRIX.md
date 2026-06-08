# APXM Plugin Test Matrix

Use this matrix to test the plugin without collapsing distinct readiness states into one vague pass/fail.

## Packaging

```bash
python3 /home/raherrer/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/apxm
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: plugin schema is valid and doctor classification tests pass.

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
python3 plugins/apxm/scripts/apxm_doctor.py --verify-workers codex,claude
dekk apxm agent templates --json
dekk apxm agent list --json
```

Expected: APXM templates are visible. Candidate executables do not count as verified workers until an APXM spawn test succeeds. When `codex` and `claude` spawn successfully, doctor should report Tier 3 unless live budget enforcement is also verified.

## Worker Spawn

```bash
dekk apxm agent test codex
dekk apxm agent test claude
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
```

Expected: live follow mode uses `watch` against a running server and thread id. Session follow mode inspects emitted session directories. Offline rollout mode uses rollout replay/archive after a rollout exists.
