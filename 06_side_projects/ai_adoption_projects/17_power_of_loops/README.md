# Power of Loops — Recurring Tasks & Autonomous Iteration

A demonstration project for Claude Code's `/loop` command and scheduling patterns.

## What's inside

| File | Description |
|------|-------------|
| `index.html` | Explainable documentation page with Mermaid diagrams |
| `examples/01_poll_ci.py` | Simulated CI poller — fixed-interval loop pattern |
| `examples/02_deploy_monitor.py` | Simulated deploy watcher — dynamic-pacing loop pattern |
| `examples/03_loop_until_dry.py` | Bug hunter simulator — loop-until-dry pattern |
| `skill_template/SKILL.md` | Reusable loop skill template |

## Three Loop Patterns

**Pattern A — Fixed Interval:** Poll at a regular cadence (e.g. `/loop 5m "check CI status"`).
- Script: `examples/01_poll_ci.py --loop --interval 5`

**Pattern B — Dynamic Pacing:** Claude decides the interval based on context.
- Script: `examples/02_deploy_monitor.py --watch --interval 3`

**Pattern C — Loop-Until-Dry:** Exhaust a search space, stop after K dry rounds.
- Script: `examples/03_loop_until_dry.py --auto --dry-threshold 3`

## Quick start

```bash
# One-shot CI poll
python examples/01_poll_ci.py

# Watch a deployment (dynamic pacing)
python examples/02_deploy_monitor.py --watch

# Auto bug hunt until dry
python examples/03_loop_until_dry.py --auto
```

## Open the explainer

Open `index.html` in a browser to see the Mermaid-based documentation, loop decision tree, and code examples.

## Skill installation

See `skill_template/SKILL.md` for instructions on turning any loop into a reusable Claude Code slash command.
