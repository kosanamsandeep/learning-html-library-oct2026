#!/usr/bin/env python3
"""
01_poll_ci.py — Simulated CI Poller

Demonstrates the fixed-interval loop pattern by simulating a CI pipeline
that progresses through states. Use --loop to auto-recheck, mimicking
Claude Code's /loop 5m "check CI status" command.

Typical usage:
    python 01_poll_ci.py --loop --interval 2
    python 01_poll_ci.py --loop --interval 5 --run-id build-42
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Simulation state
# ---------------------------------------------------------------------------

STATES = ["pending", "queued", "running", "running", "success"]
FAILURE_SCENARIO = ["pending", "queued", "running", "failed"]


class CIRun:
    """Simulates a CI pipeline run that progresses through states."""

    def __init__(self, run_id: str, fail_prob: float = 0.15):
        self.run_id = run_id
        self.fail_prob = fail_prob
        self.state = "pending"
        self.started_at = datetime.now()
        self._step = 0
        self._failed = False
        # Roll for failure at creation time
        self._will_fail = random.random() < fail_prob

    def poll(self) -> dict:
        """Advance the simulation and return current status."""
        elapsed = (datetime.now() - self.started_at).total_seconds()

        if self.state in ("success", "failed"):
            return self._report(elapsed)

        # Determine state progression
        if self._will_fail and self._step >= len(FAILURE_SCENARIO) - 1:
            self.state = "failed"
            self._failed = True
        elif self._step < len(STATES):
            self.state = STATES[self._step]
            # Simulate variable timing per step
            time.sleep(random.uniform(0.1, 0.3))
        else:
            self.state = "success"

        self._step += 1
        return self._report(elapsed)

    def is_done(self) -> bool:
        return self.state in ("success", "failed")

    def _report(self, elapsed: float) -> dict:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_formatted": str(timedelta(seconds=round(elapsed))),
            "failed": self._failed,
            "done": self.is_done(),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

STATUS_ICONS = {
    "pending": "🕐",
    "queued": "⏳",
    "running": "🔄",
    "success": "✅",
    "failed": "❌",
}


def print_status(report: dict) -> None:
    icon = STATUS_ICONS.get(report["state"], "❓")
    print(
        f"  {icon} [{report['run_id']}] "
        f"State: {report['state'].upper():8s}  "
        f"Elapsed: {report['elapsed_formatted']}  "
        f"({report['timestamp']})"
    )


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_simulation(run_id: str, fail_prob: float = 0.15, loop: bool = False, interval: int = 2) -> None:
    """
    Run the CI poll simulation. When loop=True, keeps polling until the
    run completes — analogous to /loop <interval> "check CI status".
    """
    print(f"\n{'='*60}")
    print(f"  CI Poller — Run ID: {run_id}")
    print(f"  Fail probability: {fail_prob*100:.0f}%")
    print(f"  Loop mode: {'ON' if loop else 'OFF'}")
    if loop:
        print(f"  Check interval: {interval}s")
    print(f"{'='*60}\n")

    ci = CIRun(run_id, fail_prob=fail_prob)

    iteration = 0
    while True:
        iteration += 1
        if loop:
            print(f"--- Poll #{iteration} (checking every {interval}s) ---")
        else:
            print(f"--- Poll #{iteration} ---")

        report = ci.poll()
        print_status(report)

        if report["done"]:
            outcome = "SUCCESS" if report["state"] == "success" else "FAILED"
            print(f"\n  {'='*40}")
            print(f"  Pipeline {outcome} after {report['elapsed_formatted']}")
            print(f"  {'='*40}")
            break

        if loop:
            print(f"  Waiting {interval}s before next check...")
            time.sleep(interval)
        else:
            break

    print(f"\n  Final state: {report['state']}")
    print(f"  Total polls: {iteration}")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulated CI Poller — demonstrates fixed-interval loop pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                          # one-shot poll\n"
            "  %(prog)s --loop                   # auto-recheck every 10s (default)\n"
            "  %(prog)s --loop --interval 2      # auto-recheck every 2s\n"
            "  %(prog)s --run-id build-42        # custom run ID\n"
            "  %(prog)s --fail-prob 0.5          # 50%% chance of failure\n"
        ),
    )
    parser.add_argument("--loop", action="store_true", help="Enable loop mode (auto-recheck)")
    parser.add_argument(
        "--interval", type=int, default=10,
        help="Check interval in seconds (default: 10, used with --loop)"
    )
    parser.add_argument(
        "--run-id", type=str, default=None,
        help="Custom CI run identifier (default: auto-generated)"
    )
    parser.add_argument(
        "--fail-prob", type=float, default=0.15,
        help="Probability of pipeline failure (0.0 - 1.0, default: 0.15)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_id = args.run_id or f"ci-{random.randint(1000, 9999)}"
    run_simulation(
        run_id=run_id,
        fail_prob=args.fail_prob,
        loop=args.loop,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
