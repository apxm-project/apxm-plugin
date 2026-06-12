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
python3 plugins/apxm/scripts/apxm_doctor.py --policy /path/to/policy.json --verify-workers <profile-a>,<profile-b>
```

Expected: `role_routes` reports selected verified workers or concrete missing capabilities. Role names are resolved through policy; pass role names to `--verify-workers` only if they are actual registered APXM profile IDs. Provider names are preferences, not assumptions.

## Worker Spawn

```bash
dekk apxm agent test <profile>
```

Expected: each route either becomes verified by APXM or reports a concrete spawn/auth/protocol failure.

## Canonical AIR

```bash
dekk apxm validate crates/tools/apxm-server/skills/prompt-as-workflow/examples/refactor.air
dekk apxm analyze crates/tools/apxm-server/skills/prompt-as-workflow/examples/refactor.air
dekk apxm explain crates/tools/apxm-server/skills/prompt-as-workflow/examples/refactor.air
dekk apxm compile crates/tools/apxm-server/skills/prompt-as-workflow/examples/refactor.air -o /tmp/apxm-refactor.apxmobj
```

Expected: canonical `.air` validates, analyzes, explains, and compiles.

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
python3 plugins/apxm/scripts/apxm_doctor.py --apxm-cwd /path/to/apxm
dekk apxm agent list --json
dekk apxm agent templates --json
dekk apxm process list --json
```

Expected: loop design starts from APXM OS trigger sidecars, existing APXM server skill execution, verified workers, and concrete follow/stop handles. The plugin should report missing APXM OS trigger loading, missing skill execution, missing run observation, missing worker verification, or missing background workflow handles instead of claiming that the trigger was armed.

Native goal CLI smoke:

```bash
dekk apxm goal "bounded orchestration smoke" --dry-run --json
dekk apxm goal "bounded orchestration smoke" --no-follow --json
dekk apxm goal --status <goal_id> --json
dekk apxm goal --events <goal_id> --json
dekk apxm goal --cancel <goal_id> --json
```

Expected: `goal` returns a `goal_id`, current `execution_id`, artifact paths,
control handles, worker plan, and workflow/session handles. `--dry-run` must validate and
materialize the bundle without starting workers.

Native MCP orchestration smoke:

```text
tools/list includes goal_start
tools/list includes goal_status, goal_events, and goal_cancel
goal_start explicit bounded workers -> goal_id + execution_id
goal_events({goal_id, since: 0}) -> orchestrator_sleep
page events with since = next_seq
goal_events -> orchestrator_wake or terminal event
goal_status -> succeeded or failed
```

Expected: the orchestrator does not manually prompt workers after start. A
parked or long-running orchestration can be interrupted with
`goal_cancel`, and the final status reports failure with the
`goal_cancel` reason.

Design-only checks must not spawn-test every candidate worker. Use explicit spawn verification only when execution policy must bind workers:

```bash
python3 plugins/apxm/scripts/apxm_doctor.py --apxm-cwd /path/to/apxm --verify-workers <profile-a>,<profile-b>,<profile-c>
```

Expected: role routes select verified workers or report concrete missing roles. Role names are not profile IDs unless explicitly registered that way. Provider names are examples only.

Caller coverage:

```text
[APXM OS]      trigger sidecar -> POST /v1/skills/{id}/execute -> run events
[Agent/MCP]    existing APXM MCP tool, native workflow tool, or skill call -> trace/follow
[Frontend]     writes artifacts/specs -> observes REST/SSE
[Dekk CLI]     local validate/execute/background -> session/process/rollout follow
```

Plan-splitting coverage:

```text
[objective/event] -> [roles] -> [verified worker routes] -> [compact briefs] -> [fan-in eval]
```

Expected: every worker brief includes objective, input refs, constraints, expected artifact, evidence/check command, budget, timeout, and stop conditions. Worker-authored workflows remain proposals until APXM validates and admits them.

Interruption coverage:

```text
[cancel|timeout|duplicate|worker failure|checkpoint]
      |
      v
[APXM OS re-arm/suppress] or [APXM server cancel/checkpoint/resume] or [task lease/fail] or [Dekk/APXM process stop]
```

Expected: every governed loop path has a follow handle and a stop/resume/cancel policy. A raw shell background process is not a governed loop.
