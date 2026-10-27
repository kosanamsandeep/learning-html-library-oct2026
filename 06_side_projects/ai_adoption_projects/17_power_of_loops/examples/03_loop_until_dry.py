#!/usr/bin/env python3
"""
03_loop_until_dry.py — Bug Hunter Simulator

Demonstrates the "loop-until-dry" pattern: each iteration finds 0-N bugs
with diminishing returns. The hunt stops after K consecutive dry (empty)
rounds.

Claude Code analogue: /loop 1m "find remaining bugs — stop after 3 empty rounds"

Typical usage:
    python 03_loop_until_dry.py
    python 03_loop_until_dry.py --dry-threshold 5 --total-bugs 30
    python 03_loop_until_dry.py --seed 42
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Bug taxonomy
# ---------------------------------------------------------------------------

BUG_TYPES = [
    ("null-pointer",       "NullPointerException / None dereference"),
    ("off-by-one",         "Off-by-one error in loop boundary"),
    ("race-condition",     "Potential race condition (unsynchronized access)"),
    ("memory-leak",        "Resource not released / memory leak"),
    ("sql-injection",      "SQL injection via string concatenation"),
    ("xss-vulnerability",  "Cross-site scripting via unescaped output"),
    ("hardcoded-secret",   "Hardcoded API key or password"),
    ("infinite-loop",      "Loop lacks termination condition"),
    ("dead-code",          "Unreachable branch / dead code path"),
    ("type-confusion",     "Type mismatch or implicit coercion bug"),
    ("logical-flip",       "Inverted boolean / wrong comparison operator"),
    ("unhandled-edge",     "Unhandled edge case in input validation"),
]

SEVERITIES = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = [0.35, 0.35, 0.20, 0.10]


class BugHunter:
    """
    Simulates a bug-hunting loop that finds bugs with diminishing returns.
    Mirrors the loop-until-dry pattern used in security audits and code reviews.
    """

    def __init__(self, total_bugs: int = 20, dry_threshold: int = 3, seed: int | None = None):
        self.total_bugs = total_bugs
        self.dry_threshold = dry_threshold
        self.rng = random.Random(seed)

        # Pre-generate the pool of "undiscovered" bugs
        self.undiscovered: list[dict] = []
        for i in range(total_bugs):
            bug_type, desc = self.rng.choice(BUG_TYPES)
            severity = self.rng.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
            self.undiscovered.append({
                "id": f"BUG-{i+1:03d}",
                "type": bug_type,
                "description": desc,
                "severity": severity,
                "found_at_iteration": None,
            })

        self.found: list[dict] = []
        self.dry_rounds = 0
        self.iteration = 0
        self.started_at = datetime.now()

    def hunt(self) -> list[dict]:
        """
        Perform one hunting iteration. Returns bugs found this round.
        Bugs are found with diminishing probability as the pool shrinks.
        """
        self.iteration += 1

        if not self.undiscovered:
            return []

        # Determine how many bugs we find this round.
        # As the pool shrinks, find fewer bugs — sigmoid-like decay.
        remaining = len(self.undiscovered)
        total = self.total_bugs

        # Base find rate: high when many bugs remain, low when few remain.
        ratio = remaining / total  # 1.0 → 0.0
        max_find = max(1, int(ratio * 4))  # At most ~4 bugs, at least 1

        # Add randomness
        n_find = self.rng.randint(0, max_find)
        n_find = min(n_find, remaining)

        if n_find == 0:
            self.dry_rounds += 1
            return []

        # Pick bugs from the pool (without replacement)
        found_this_round = self.rng.sample(self.undiscovered, n_find)
        for bug in found_this_round:
            bug["found_at_iteration"] = self.iteration
            self.found.append(bug)
            self.undiscovered.remove(bug)

        self.dry_rounds = 0  # reset dry counter on a find
        return found_this_round

    def should_stop(self) -> bool:
        """Stop when we've had K consecutive dry rounds."""
        return self.dry_rounds >= self.dry_threshold or not self.undiscovered

    def summary(self) -> dict:
        elapsed = (datetime.now() - self.started_at).total_seconds()
        return {
            "total_bugs": self.total_bugs,
            "found": len(self.found),
            "remaining": len(self.undiscovered),
            "iterations": self.iteration,
            "dry_rounds": self.dry_rounds,
            "dry_threshold": self.dry_threshold,
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_formatted": str(timedelta(seconds=round(elapsed))),
            "found_by_severity": {
                s: len([b for b in self.found if b["severity"] == s])
                for s in SEVERITIES
            },
        }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

SEVERITY_ICONS = {"low": "🔹", "medium": "🔶", "high": "🔴", "critical": "💥"}


def print_bug(bug: dict) -> None:
    icon = SEVERITY_ICONS.get(bug["severity"], "🐛")
    print(
        f"    {icon} {bug['id']:<8s} "
        f"[{bug['severity']:<8s}] "
        f"{bug['type']:<20s} "
        f"{bug['description']}"
    )


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_simulation(
    total_bugs: int = 20,
    dry_threshold: int = 3,
    seed: int | None = None,
    auto: bool = False,
    interval: int = 1,
) -> None:
    """
    Run the bug hunt. When auto=True, iterates automatically until dry;
    otherwise pauses between rounds (simulating /loop).
    """
    hunter = BugHunter(total_bugs=total_bugs, dry_threshold=dry_threshold, seed=seed)

    print(f"\n{'='*60}")
    print(f"  Bug Hunter — Loop-Until-Dry Pattern")
    print(f"  Total bugs in pool: {total_bugs}")
    print(f"  Dry threshold: {dry_threshold} consecutive empty rounds")
    if seed is not None:
        print(f"  Random seed: {seed}")
    print(f"  Auto mode: {'ON' if auto else 'OFF'} (auto-iterates)")
    if auto:
        print(f"  Interval between hunts: {interval}s")
    print(f"{'='*60}\n")

    while not hunter.should_stop():
        found = hunter.hunt()

        if found:
            print(f"--- Round #{hunter.iteration} — found {len(found)} bug(s) ---")
            for bug in found:
                print_bug(bug)
        else:
            print(f"--- Round #{hunter.iteration} — no bugs found (dry: {hunter.dry_rounds}/{dry_threshold}) ---")

        if not hunter.should_stop() and auto:
            time.sleep(interval)
        elif not hunter.should_stop():
            # In non-auto mode, prompt to continue
            print(f"  [Dry rounds: {hunter.dry_rounds}/{dry_threshold}]")
            try:
                resp = input("  Continue hunting? [Y/n]: ").strip().lower()
                if resp in ("n", "no"):
                    break
            except (EOFError, KeyboardInterrupt):
                print()
                break

    summary = hunter.summary()
    print()
    print(f"  {'='*50}")
    print(f"  HUNT COMPLETE")
    print(f"  {'='*50}")
    print(f"  Iterations:       {summary['iterations']}")
    print(f"  Bugs found:       {summary['found']} / {summary['total_bugs']}")
    print(f"  Remaining:        {summary['remaining']}")
    print(f"  Dry rounds:       {summary['dry_rounds']} (threshold: {summary['dry_threshold']})")
    print(f"  Time elapsed:     {summary['elapsed_formatted']}")
    print()
    print(f"  Breakdown by severity:")
    for sev in SEVERITIES:
        count = summary["found_by_severity"][sev]
        icon = SEVERITY_ICONS[sev]
        bar = "█" * count + "░" * (max(0, 10 - count))
        print(f"    {icon} {sev:<10s} {count:3d}  {bar}")
    print()

    if summary["remaining"] > 0:
        print(f"  💡 Tip: Increase dry threshold or reduce interval to find more bugs.")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bug Hunter Simulator — demonstrates loop-until-dry pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                          # interactive hunt (press Enter to continue)\n"
            "  %(prog)s --auto                   # auto-run until dry\n"
            "  %(prog)s --auto --interval 2      # auto with 2s between hunts\n"
            "  %(prog)s --dry-threshold 5        # stop after 5 empty rounds\n"
            "  %(prog)s --total-bugs 50          # larger bug pool\n"
            "  %(prog)s --seed 42                # reproducible results\n"
        ),
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Auto-iterate until dry (no prompts)"
    )
    parser.add_argument(
        "--interval", type=int, default=1,
        help="Seconds between auto-hunt iterations (default: 1)"
    )
    parser.add_argument(
        "--dry-threshold", type=int, default=3,
        help="Consecutive dry rounds before stopping (default: 3)"
    )
    parser.add_argument(
        "--total-bugs", type=int, default=20,
        help="Total number of bugs in the pool (default: 20)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible runs"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_simulation(
        total_bugs=args.total_bugs,
        dry_threshold=args.dry_threshold,
        seed=args.seed,
        auto=args.auto,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
