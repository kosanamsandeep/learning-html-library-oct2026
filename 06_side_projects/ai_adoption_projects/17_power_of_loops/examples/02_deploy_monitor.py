#!/usr/bin/env python3
"""
02_deploy_monitor.py — Simulated Deploy Watcher

Demonstrates the dynamic-pacing loop pattern by simulating a multi-stage
deployment pipeline. The script reports on each stage and can simulate
failures, rollbacks, and variable pacing.

Claude Code analogue: /loop 10s "check deploy status"
The interval could vary based on which stage the deploy is in.

Typical usage:
    python 02_deploy_monitor.py --watch --interval 3
    python 02_deploy_monitor.py --watch --fail-at canary
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Deployment stages
# ---------------------------------------------------------------------------

STAGES = [
    {"name": "build",       "label": "Building artifact",       "min_time": 1, "max_time": 3},
    {"name": "push",        "label": "Pushing to registry",     "min_time": 1, "max_time": 2},
    {"name": "deploy_canary", "label": "Deploying canary (10%)", "min_time": 2, "max_time": 4},
    {"name": "deploy_prod", "label": "Deploying production",    "min_time": 2, "max_time": 5},
]

ROLLBACK_STAGES = [
    {"name": "rollback_drain",  "label": "Draining traffic from new version", "min_time": 1, "max_time": 2},
    {"name": "rollback_restore", "label": "Restoring previous version",       "min_time": 1, "max_time": 3},
]


class DeploySim:
    """Simulates a multi-stage deployment with optional failures and rollbacks."""

    def __init__(self, deploy_id: str, fail_at: str | None = None):
        self.deploy_id = deploy_id
        self.fail_at = fail_at
        self.current_stage_idx = 0
        self.current_stage = STAGES[0]
        self.stage_started_at = datetime.now()
        self.started_at = datetime.now()
        self.completed = False
        self.failed = False
        self.rolled_back = False
        self.stage_progress: list[dict] = []
        self._stage_elapsed = 0.0

    def poll(self) -> dict:
        """Advance simulation and return current status."""
        elapsed = (datetime.now() - self.started_at).total_seconds()

        if self.completed:
            return self._report(elapsed)
        if self.failed:
            return self._report(elapsed)
        if self.rolled_back:
            return self._report(elapsed)

        # Time spent on current stage
        stage_elapsed = (datetime.now() - self.stage_started_at).total_seconds()
        self._stage_elapsed = stage_elapsed
        stage_def = self.current_stage

        # Simulate variable progress — report multiple times per stage
        duration_hint = random.uniform(stage_def["min_time"], stage_def["max_time"])

        # Check for failure if this is the targeted stage
        is_fail_stage = (self.fail_at and self.current_stage["name"] == self.fail_at)

        if is_fail_stage and stage_elapsed > duration_hint * 0.5:
            # Simulate failure mid-stage
            time.sleep(random.uniform(0.1, 0.3))
            self.failed = True
            self.stage_progress.append({
                "stage": stage_def["name"],
                "status": "failed",
                "reason": f"Health check failed at {stage_def['name']} stage",
            })
            return self._report(elapsed)

        if stage_elapsed >= duration_hint:
            time.sleep(random.uniform(0.1, 0.3))
            # Stage completed
            self.stage_progress.append({
                "stage": stage_def["name"],
                "status": "success",
                "duration_seconds": round(stage_elapsed, 1),
            })

            # Rollback simulation: sometimes production deploy triggers rollback
            if stage_def["name"] == "deploy_prod" and random.random() < 0.2 and not self.fail_at:
                self.rolled_back = True
                self.current_stage = ROLLBACK_STAGES[0]
                self.current_stage_idx = -1  # sentinel
                self.stage_started_at = datetime.now()
                return self._report(elapsed)

            # Check if we are in rollback stages
            if self.current_stage_idx == -1:
                # In rollback sequence
                rb_idx = ROLLBACK_STAGES.index(stage_def) + 1 if stage_def in ROLLBACK_STAGES else 0
                if rb_idx < len(ROLLBACK_STAGES):
                    self.current_stage = ROLLBACK_STAGES[rb_idx]
                    self.stage_started_at = datetime.now()
                else:
                    self.rolled_back = True
                return self._report(elapsed)

            # Normal progression
            if self.current_stage_idx + 1 < len(STAGES):
                self.current_stage_idx += 1
                self.current_stage = STAGES[self.current_stage_idx]
                self.stage_started_at = datetime.now()
            else:
                self.completed = True

        return self._report(elapsed)

    def is_done(self) -> bool:
        return self.completed or self.failed or self.rolled_back

    def _report(self, elapsed: float) -> dict:
        stage = self.current_stage if not self.is_done() else self.current_stage
        return {
            "deploy_id": self.deploy_id,
            "current_stage": stage["name"] if not self.is_done() else "---",
            "current_label": stage["label"] if not self.is_done() else "---",
            "stage_elapsed": round(self._stage_elapsed, 1),
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_formatted": str(timedelta(seconds=round(elapsed))),
            "completed": self.completed,
            "failed": self.failed,
            "rolled_back": self.rolled_back,
            "stages_completed": [s for s in self.stage_progress if s["status"] == "success"],
            "stages_failed": [s for s in self.stage_progress if s["status"] == "failed"],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

STAGE_ICONS = {
    "build": "🔨",
    "push": "📤",
    "deploy_canary": "🐤",
    "deploy_prod": "🚀",
    "rollback_drain": "🔀",
    "rollback_restore": "♻️",
}


def print_deploy_status(report: dict) -> None:
    if report["completed"]:
        print(f"  ✅ [{report['deploy_id']}] DEPLOY SUCCESS — {report['elapsed_formatted']}")
    elif report["failed"]:
        failed = report["stages_failed"]
        reason = failed[0]["reason"] if failed else "Unknown error"
        print(f"  ❌ [{report['deploy_id']}] DEPLOY FAILED — {reason}")
    elif report["rolled_back"]:
        print(f"  ⚠️  [{report['deploy_id']}] ROLLBACK — {report['elapsed_formatted']}")
    else:
        icon = STAGE_ICONS.get(report["current_stage"], "⏳")
        stages_done = len(report["stages_completed"])
        print(
            f"  {icon} [{report['deploy_id']}] "
            f"{report['current_label']:30s}  "
            f"Stage elapsed: {report['stage_elapsed']:.1f}s  "
            f"Total: {report['elapsed_formatted']}  "
            f"({stages_done}/{len(STAGES)} stages done)"
        )


def suggested_interval(report: dict) -> int:
    """Dynamic pacing: suggest next check interval based on current stage."""
    stage = report.get("current_stage", "")
    if report["completed"] or report["failed"] or report["rolled_back"]:
        return 0
    if "build" in stage:
        return 2  # fast: build changes quickly
    if "push" in stage:
        return 3
    if "canary" in stage:
        return 5  # moderate: canary needs observation
    if "prod" in stage:
        return 8  # slow: production rollout is gradual
    if "rollback" in stage:
        return 2  # fast: want to see rollback progress
    return 4


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_simulation(
    deploy_id: str,
    fail_at: str | None = None,
    watch: bool = False,
    interval: int = 3,
) -> None:
    """
    Run the deploy watch simulation. When watch=True, keeps polling until
    the deploy completes, fails, or rolls back — the interval can be
    dynamically adjusted based on the current stage.
    """
    print(f"\n{'='*65}")
    print(f"  Deploy Watcher — Deploy ID: {deploy_id}")
    if fail_at:
        print(f"  Simulated failure at stage: {fail_at}")
    print(f"  Watch mode: {'ON' if watch else 'OFF'}")
    if watch:
        print(f"  Base interval: {interval}s (dynamic pacing active)")
    print(f"{'='*65}\n")

    deploy = DeploySim(deploy_id, fail_at=fail_at)

    iteration = 0
    while not deploy.is_done():
        iteration += 1
        report = deploy.poll()

        if watch:
            suggested = suggested_interval(report)
            actual_interval = suggested if suggested > 0 else interval
            print(f"--- Check #{iteration} (pacing: {actual_interval}s) ---")
        else:
            actual_interval = 0
            print(f"--- Check #{iteration} ---")

        print_deploy_status(report)

        if deploy.is_done():
            break

        if watch:
            print(f"  Waiting {actual_interval}s...")
            time.sleep(actual_interval)
        else:
            break

    # Final report
    if not deploy.is_done():
        report = deploy.poll()
    else:
        report = deploy._report((datetime.now() - deploy.started_at).total_seconds())

    print()
    print(f"  {'='*40}")
    if report["completed"]:
        print(f"  ✅ Deployment completed successfully!")
    elif report["failed"]:
        print(f"  ❌ Deployment failed!")
    elif report["rolled_back"]:
        print(f"  ⚠️  Deployment rolled back.")
    print(f"  Total checks: {iteration}")
    print(f"  Total time: {report['elapsed_formatted']}")
    print(f"  {'='*40}")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulated Deploy Watcher — demonstrates dynamic-pacing loop pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                             # one-shot check\n"
            "  %(prog)s --watch                     # watch until completion\n"
            "  %(prog)s --watch --interval 5        # check every 5s base\n"
            "  %(prog)s --fail-at deploy_canary     # fail at canary stage\n"
            "  %(prog)s --deploy-id release-2.3     # custom deploy ID\n"
        ),
    )
    parser.add_argument("--watch", action="store_true", help="Enable watch mode (auto-recheck)")
    parser.add_argument(
        "--interval", type=int, default=3,
        help="Base check interval in seconds (default: 3, used with --watch)"
    )
    parser.add_argument(
        "--deploy-id", type=str, default=None,
        help="Custom deployment identifier (default: auto-generated)"
    )
    parser.add_argument(
        "--fail-at", type=str, default=None,
        choices=[s["name"] for s in STAGES],
        help="Force failure at a specific stage"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    deploy_id = args.deploy_id or f"deploy-{random.randint(1000, 9999)}"
    run_simulation(
        deploy_id=deploy_id,
        fail_at=args.fail_at,
        watch=args.watch,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
