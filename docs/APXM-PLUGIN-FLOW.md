# APXM Plugin Flow

This plugin is the distribution layer for APXM orchestration skills. It teaches agents when and how to call APXM; it does not replace APXM/Dekk.

## Ideal Flow

```text
[User asks for big work]
          |
          v
[Codex/agent triggers APXM skill]
          |
          v
[Skill runs apxm_doctor preflight]
          |
          +--------------------+
          |                    |
          v                    v
[APXM not ready]        [APXM ready]
          |                    |
          v                    v
[Return setup gap]      [Discover verified workers]
                               |
                               v
                    [Create compact task request]
                               |
                               v
                    [APXM validates policy]
                               |
          +--------------------+--------------------+
          |                                         |
          v                                         v
 [Rejected by policy]                      [Policy accepted]
          |                                         |
          v                                         v
 [Return fixable gaps]                  [APXM compiles graph]
                                                    |
                                                    v
                                      [APXM schedules workers]
                                                    |
                                                    v
                                      [Workers execute/propose]
                                                    |
                                                    v
                                      [APXM verifies artifacts]
                                                    |
                                                    v
                                      [Traceable final result]
```

## Plugin Responsibilities

- Provide concise skills that route work to APXM.
- Discover readiness through `scripts/apxm_doctor.py`.
- Encourage compact request envelopes instead of giant prompts.
- Keep councils, workers, compile/execute, verification, and MCP boundaries explicit.
- Distribute the workflow as a Codex plugin marketplace repo.

## APXM Responsibilities

- Validate graphs and policy.
- Admit workers.
- Compile workflows.
- Schedule and supervise agents.
- Enforce budget, timeout, cancellation, and write policy.
- Persist traces and artifacts.

## Worker Model

Claude and Codex are useful defaults, but not assumptions. A worker can be any APXM-verified route that supports the requested capability:

```text
[APXM registry]
      |
      v
[Candidate templates]
      |
      v
[Spawn/prompt/stop verification]
      |
      +--> [not verified] -> [candidate only]
      |
      v
[Verified worker]
      |
      +--> execute task
      +--> critique output
      +--> author graph proposal
      +--> call compiled skill workflow
```

Any worker-authored graph remains untrusted until APXM validates, compiles, and admits it.

## Skill-To-Workflow Flow

```text
[Existing SKILL.md]
      |
      v
[Classify behavior]
      |
      v
[Extract trigger, inputs, policy, checks]
      |
      v
[Scaffold APXM workflow pack]
      |
      v
[Validate and compile with APXM]
      |
      +--> [compile failed] -> [conversion report]
      |
      v
[Reusable APXM workflow]
```

The original skill stays as the trigger layer. APXM becomes the graph execution layer.
