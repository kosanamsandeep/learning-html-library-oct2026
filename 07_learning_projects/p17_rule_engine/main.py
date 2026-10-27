"""
PROJECT 17: RULE ENGINE - Insurance Premium Calculator
=======================================================
Patterns: Specification Pattern, Chain of Responsibility, Strategy, Interpreter
Inspired by: Drools, Easy Rules, CLIPS, Business Rules Engines

Story: You're building an insurance pricing system. Premium calculation depends
on dozens of business rules (age, vehicle, driving record, location, discounts).
Instead of a 500-line if/else chain, you build a rule engine where business
analysts can add/modify rules without touching core code.

Key Concepts Demonstrated:
  1. Specification Pattern (composable predicates)
  2. Rule Engine (declarative business logic)
  3. Priority-based evaluation
  4. Rule composition (AND, OR, NOT)
  5. Separation of rules from engine
"""

import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from engine.rule_engine import (
    RuleEngine,
    Rule,
    Equals,
    GreaterThan,
    LessThan,
    Between,
    Contains,
    InSet,
)
from rules.insurance_rules import create_insurance_engine, calculate_premium


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 17: RULE ENGINE - Insurance Premium Calculator")
    print("#  Patterns: Specification, Chain of Responsibility, Strategy")
    print("#  Inspired by: Drools, Easy Rules, CLIPS")
    print("=" * 70)


def demo_1_specification_pattern():
    """Demo: Composable specifications (AND, OR, NOT)."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Specification Pattern (Composable Predicates)")
    print("=" * 70)

    # Simple specifications
    is_young = LessThan("age", 25)
    is_senior = GreaterThan("age", 65)
    drives_sports = Equals("vehicle", "sports")
    has_dui = Contains("violations", "DUI")
    clean_record = Equals("accidents", 0)

    # Composite specifications
    high_risk = (is_young & drives_sports) | has_dui
    safe_driver = clean_record & ~is_young & ~is_senior

    # Test candidates
    candidates = [
        {
            "name": "Alex",
            "age": 19,
            "vehicle": "sports",
            "violations": [],
            "accidents": 0,
        },
        {
            "name": "Beth",
            "age": 35,
            "vehicle": "sedan",
            "violations": [],
            "accidents": 0,
        },
        {
            "name": "Carl",
            "age": 45,
            "vehicle": "suv",
            "violations": ["DUI"],
            "accidents": 2,
        },
        {
            "name": "Dana",
            "age": 72,
            "vehicle": "sedan",
            "violations": [],
            "accidents": 0,
        },
    ]

    print(f"\n  Specifications defined:")
    print(f"    high_risk = {high_risk.describe()}")
    print(f"    safe_driver = {safe_driver.describe()}")

    print(f"\n  Evaluating candidates:")
    for c in candidates:
        hr = high_risk.is_satisfied_by(c)
        sd = safe_driver.is_satisfied_by(c)
        print(
            f"    {c['name']:6s} (age={c['age']}, vehicle={c['vehicle']}) "
            f"| high_risk={hr} | safe_driver={sd}"
        )

    print(f"\n  Key insight: Specifications compose like boolean algebra.")
    print(f"  Complex conditions built from simple, testable pieces.")


def demo_2_rule_evaluation():
    """Demo: Rule engine evaluating insurance premium."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Rule Engine - Premium Calculation")
    print("=" * 70)

    engine = create_insurance_engine()

    # A standard driver
    driver = {
        "driver_age": 35,
        "vehicle_category": "sedan",
        "accidents_3yr": 0,
        "speeding_tickets": 0,
        "violations": [],
        "zip_risk_zone": "medium",
        "total_policies": 2,
        "years_as_customer": 7,
        "safety_rating": 5,
        "annual_mileage": 12000,
    }

    print(f"\n  Driver profile:")
    for k, v in driver.items():
        print(f"    {k}: {v}")

    results, rule_log = engine.evaluate_all(driver)

    print(f"\n  Rules fired:")
    for rr in rule_log:
        if rr.fired:
            print(f"    [FIRED] {rr.rule_name} (priority: {rr.priority})")

    print(f"\n  Premium breakdown:")
    print(f"    Base premium: ${results.get('base_premium', 0):.2f}")
    for name, mult in results.get("multipliers", []):
        print(f"    Multiplier: {name} (x{mult})")
    for name, disc in results.get("discounts", []):
        print(f"    Discount: {name} (-{disc*100:.0f}%)")

    premium = calculate_premium(results)
    print(f"\n    FINAL PREMIUM: ${premium:.2f}/year")


def demo_3_risk_profiles():
    """Demo: Different risk profiles produce different premiums."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Risk Profile Comparison")
    print("=" * 70)

    engine = create_insurance_engine()

    profiles = [
        {
            "name": "Safe Sarah",
            "driver_age": 40,
            "vehicle_category": "economy",
            "accidents_3yr": 0,
            "speeding_tickets": 0,
            "violations": [],
            "zip_risk_zone": "low",
            "total_policies": 3,
            "years_as_customer": 8,
            "safety_rating": 5,
            "annual_mileage": 6000,
        },
        {
            "name": "Average Andy",
            "driver_age": 30,
            "vehicle_category": "sedan",
            "accidents_3yr": 1,
            "speeding_tickets": 1,
            "violations": [],
            "zip_risk_zone": "medium",
            "total_policies": 1,
            "years_as_customer": 2,
            "safety_rating": 4,
            "annual_mileage": 15000,
        },
        {
            "name": "Risky Rick",
            "driver_age": 19,
            "vehicle_category": "sports",
            "accidents_3yr": 2,
            "speeding_tickets": 3,
            "violations": [],
            "zip_risk_zone": "high",
            "total_policies": 1,
            "years_as_customer": 0,
            "safety_rating": 3,
            "annual_mileage": 20000,
        },
        {
            "name": "DUI Dave",
            "driver_age": 28,
            "vehicle_category": "suv",
            "accidents_3yr": 3,
            "speeding_tickets": 4,
            "violations": ["DUI"],
            "zip_risk_zone": "very_high",
            "total_policies": 1,
            "years_as_customer": 1,
            "safety_rating": 3,
            "annual_mileage": 25000,
        },
    ]

    print(
        f"\n  {'Name':<15s} {'Vehicle':<10s} {'Age':<5s} {'Accidents':<10s} {'Premium':<12s} Factors"
    )
    print(f"  {'-'*80}")

    for profile in profiles:
        name = profile.pop("name")
        results, _ = engine.evaluate_all(profile)
        premium = calculate_premium(results)
        mults = [m[0] for m in results.get("multipliers", [])]
        discs = [d[0] for d in results.get("discounts", [])]
        factors = ", ".join(mults[:2]) if mults else ", ".join(discs[:2])
        print(
            f"  {name:<15s} {profile['vehicle_category']:<10s} "
            f"{profile['driver_age']:<5d} {profile['accidents_3yr']:<10d} "
            f"${premium:<11.2f} {factors}"
        )


def demo_4_rule_composition():
    """Demo: Building complex rules with composition."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Rule Composition (Building Complex Logic)")
    print("=" * 70)

    # Build a custom rule engine with composed specifications
    engine = RuleEngine()

    # Complex composed condition: VIP Customer
    # (high income OR long-time customer) AND clean record AND multiple policies
    vip_condition = (
        (GreaterThan("income", 100000) | GreaterThan("years", 10))
        & Equals("accidents", 0)
        & GreaterThan("policies", 2)
    )

    # High-risk condition: young driver with sports car in bad area
    high_risk_condition = (
        LessThan("age", 25)
        & InSet("vehicle", {"sports", "luxury"})
        & InSet("zone", {"high", "very_high"})
    )

    engine.add_rule(
        Rule(
            name="VIP_discount",
            condition=vip_condition,
            action=lambda f, r: r.update({"tier": "VIP", "discount": 0.25}),
            priority=1,
        )
    )

    engine.add_rule(
        Rule(
            name="high_risk_surcharge",
            condition=high_risk_condition,
            action=lambda f, r: r.update({"tier": "HIGH_RISK", "surcharge": 0.5}),
            priority=2,
        )
    )

    engine.add_rule(
        Rule(
            name="standard",
            condition=~vip_condition & ~high_risk_condition,
            action=lambda f, r: r.update({"tier": "STANDARD", "discount": 0}),
            priority=99,
        )
    )

    print(f"\n  Composed rules:")
    print(f"    VIP: {vip_condition.describe()}")
    print(f"    High Risk: {high_risk_condition.describe()}")

    test_cases = [
        {
            "name": "Rich Robert",
            "income": 150000,
            "years": 3,
            "accidents": 0,
            "policies": 4,
            "age": 45,
            "vehicle": "sedan",
            "zone": "low",
        },
        {
            "name": "Young Yuki",
            "age": 20,
            "vehicle": "sports",
            "zone": "high",
            "income": 30000,
            "years": 1,
            "accidents": 0,
            "policies": 1,
        },
        {
            "name": "Normal Nora",
            "age": 35,
            "vehicle": "sedan",
            "zone": "medium",
            "income": 60000,
            "years": 4,
            "accidents": 1,
            "policies": 1,
        },
    ]

    print(f"\n  Evaluation results:")
    for case in test_cases:
        name = case["name"]
        results, _ = engine.evaluate_all(case)
        tier = results.get("tier", "UNKNOWN")
        discount = results.get("discount", 0)
        surcharge = results.get("surcharge", 0)
        print(
            f"    {name:<15s} -> Tier: {tier:<12s} "
            f"| discount={discount*100:.0f}% | surcharge={surcharge*100:.0f}%"
        )


def demo_5_rule_introspection():
    """Demo: Inspecting rules, understanding why decisions were made."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Rule Introspection (Explain the Decision)")
    print("=" * 70)

    engine = create_insurance_engine()

    driver = {
        "driver_age": 23,
        "vehicle_category": "sports",
        "accidents_3yr": 1,
        "speeding_tickets": 1,
        "violations": [],
        "zip_risk_zone": "high",
        "total_policies": 1,
        "years_as_customer": 1,
        "safety_rating": 3,
        "annual_mileage": 18000,
    }

    print(
        f"\n  Driver: age={driver['driver_age']}, vehicle={driver['vehicle_category']}, "
        f"accidents={driver['accidents_3yr']}"
    )

    results, rule_log = engine.evaluate_all(driver)
    premium = calculate_premium(results)

    print(f"\n  Decision explanation (all {len(rule_log)} rules evaluated):")
    print(f"  {'Rule':<30s} {'Priority':<10s} {'Fired':<8s} Condition")
    print(f"  {'-'*90}")
    for rr in rule_log:
        fired = "YES" if rr.fired else "no"
        print(
            f"  {rr.rule_name:<30s} {rr.priority:<10d} {fired:<8s} {rr.condition_description[:40]}"
        )

    print(f"\n  Premium: ${premium:.2f}")
    print(f"\n  Key insight: Rule engines provide EXPLAINABILITY.")
    print(f"  You can trace exactly which rules fired and why.")
    print(f"  Critical for regulated industries (insurance, banking, healthcare).")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  SPECIFICATION PATTERN:
     - Composable boolean predicates
     - AND (&), OR (|), NOT (~) operators
     - Build complex from simple, testable specs
     - Reuse specs across multiple rules

  RULE ENGINE:
     - Separate business rules from execution logic
     - Rules are data, not code (can be externalized)
     - Priority-based evaluation order
     - Strategies: fire ALL, fire FIRST, by GROUP

  ADVANTAGES OVER IF/ELSE:
     - Rules are declarative, not imperative
     - Easy to add/remove/modify rules
     - Rules are self-documenting
     - Provides explainability (audit why decision was made)
     - Business analysts can understand rules

  REAL-WORLD USAGE:
     - Drools (Java): Enterprise rule engine
     - Easy Rules (Java): Lightweight rule engine
     - Business Rules Engines: Insurance, banking, fraud detection
     - Pricing engines: Dynamic pricing, promotions
     - Access control: Policy-based authorization (ABAC)
    """)


if __name__ == "__main__":
    print_header()
    demo_1_specification_pattern()
    demo_2_rule_evaluation()
    demo_3_risk_profiles()
    demo_4_rule_composition()
    demo_5_rule_introspection()
    print_summary()
