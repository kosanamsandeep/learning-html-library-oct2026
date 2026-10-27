# Deploy Watcher Skill — Reusable Loop Command

Place this file in your project's `.claude/skills/` directory (create it if it doesn't exist).
Once installed, run `/deploy-watch` in Claude Code to start the loop.

```yaml
name: deploy-watcher
description: |
  Watch a deployment progress through build -> push -> canary -> production.
  Reports each stage and exits on success, failure, or rollback.
  Demonstrates the dynamic-pacing loop pattern — Claude adjusts the
  check interval based on which stage the deploy is in.

trigger:
  type: slash_command
  command: deploy-watch

action: |
  Check the deployment status by running:
  python examples/02_deploy_monitor.py --watch --interval 3
  Report the current stage, elapsed time, and any failures.
  If the deploy is still in progress, suggest the next check interval
  based on the current stage:
    - build stage: check every 2s (changes fast)
    - push stage: check every 3s
    - canary stage: check every 5s (needs observation time)
    - production stage: check every 8s (gradual rollout)
    - rollback: check every 2s (want quick visibility)

loop:
  default_interval: 10s
  stop_conditions:
    - Deploy status is "success" or "failed"
    - Rollback detected
    - User presses Esc to exit
  dynamic_pacing: true
    # When enabled, Claude can override default_interval based on context.

notes: |
  This skill is part of the "Power of Loops" demonstration project.
  See the full project at:
  https://github.com/your-org/power-of-loops
```

## How to install

1. Create a `.claude/skills/` directory in your project root:
   ```bash
   mkdir -p .claude/skills/
   ```

2. Save this file as `.claude/skills/deploy-watcher.SKILL.md` (or copy it there).

3. In Claude Code, type `/deploy-watch` to start the loop.

## Customization

| Parameter | Description | Default |
|-----------|-------------|---------|
| `default_interval` | How often to check by default | `10s` |
| `dynamic_pacing` | Let Claude pick the interval | `true` |
| `stop_conditions` | Events that end the loop | success, failure, rollback |

To create your own loop skill, copy this template and change:
- `name` and `command` to your skill name
- `action` to your custom check logic
- `loop` settings to match your desired cadence

## Related skills

- **CI Poller** — `/loop 5m "check CI status"` (fixed-interval pattern)
- **Bug Hunter** — `/loop 1m "find bugs -- stop after 3 dry rounds"` (loop-until-dry pattern)
- **Audit Sweeper** — `/loop 30s "audit next file -- stop when all files checked"` (exhaustion pattern)
