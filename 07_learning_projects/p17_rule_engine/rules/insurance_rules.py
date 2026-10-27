"""
Insurance Pricing Rules - Business rules for auto insurance premium calculation.

This demonstrates how complex business logic can be expressed as declarative rules
rather than tangled if/else chains.

Rule categories:
  - Base premium rules (by vehicle type)
  - Age-based adjustments
  - Driving record adjustments
  - Location-based adjustments
  - Discount rules
"""

from engine.rule_engine import (
    Rule,
    RuleEngine,
    Specification,
    Equals,
    GreaterThan,
    LessThan,
    Between,
    Contains,
    InSet,
)


def create_insurance_engine() -> RuleEngine:
    """Create a fully configured insurance pricing rule engine."""
    engine = RuleEngine()

    # ─── Base Premium Rules (by vehicle category) ─────────────────

    engine.add_rule(
        Rule(
            name="base_economy",
            condition=Equals("vehicle_category", "economy"),
            action=lambda f, r: r.update({"base_premium": 600.0}),
            priority=10,
            group="base_premium",
            description="Economy vehicles: $600 base",
        )
    )

    engine.add_rule(
        Rule(
            name="base_sedan",
            condition=Equals("vehicle_category", "sedan"),
            action=lambda f, r: r.update({"base_premium": 900.0}),
            priority=10,
            group="base_premium",
            description="Sedan vehicles: $900 base",
        )
    )

    engine.add_rule(
        Rule(
            name="base_suv",
            condition=Equals("vehicle_category", "suv"),
            action=lambda f, r: r.update({"base_premium": 1200.0}),
            priority=10,
            group="base_premium",
            description="SUV vehicles: $1200 base",
        )
    )

    engine.add_rule(
        Rule(
            name="base_sports",
            condition=Equals("vehicle_category", "sports"),
            action=lambda f, r: r.update({"base_premium": 1800.0}),
            priority=10,
            group="base_premium",
            description="Sports cars: $1800 base",
        )
    )

    engine.add_rule(
        Rule(
            name="base_luxury",
            condition=Equals("vehicle_category", "luxury"),
            action=lambda f, r: r.update({"base_premium": 2400.0}),
            priority=10,
            group="base_premium",
            description="Luxury vehicles: $2400 base",
        )
    )

    # ─── Age-Based Risk Multipliers ──────────────────────────────

    engine.add_rule(
        Rule(
            name="young_driver_high_risk",
            condition=LessThan("driver_age", 21),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("Young driver (<21)", 1.6)
            ),
            priority=20,
            group="age_risk",
            description="Drivers under 21: 60% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="young_driver_moderate_risk",
            condition=Between("driver_age", 21, 25),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("Young driver (21-25)", 1.3)
            ),
            priority=20,
            group="age_risk",
            description="Drivers 21-25: 30% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="senior_driver_risk",
            condition=GreaterThan("driver_age", 70),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("Senior driver (>70)", 1.25)
            ),
            priority=20,
            group="age_risk",
            description="Drivers over 70: 25% surcharge",
        )
    )

    # ─── Driving Record ──────────────────────────────────────────

    engine.add_rule(
        Rule(
            name="accidents_minor",
            condition=Between("accidents_3yr", 1, 2),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("1-2 accidents", 1.2)
            ),
            priority=30,
            group="driving_record",
            description="1-2 accidents in 3 years: 20% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="accidents_major",
            condition=GreaterThan("accidents_3yr", 2),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("3+ accidents", 1.5)
            ),
            priority=30,
            group="driving_record",
            description="3+ accidents: 50% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="dui_violation",
            condition=Contains("violations", "DUI"),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("DUI violation", 2.0)
            ),
            priority=25,
            group="driving_record",
            description="DUI on record: 100% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="speeding_violations",
            condition=GreaterThan("speeding_tickets", 2),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("3+ speeding tickets", 1.15)
            ),
            priority=30,
            group="driving_record",
            description="3+ speeding tickets: 15% surcharge",
        )
    )

    # ─── Location-Based Risk ─────────────────────────────────────

    engine.add_rule(
        Rule(
            name="high_risk_area",
            condition=InSet("zip_risk_zone", {"high", "very_high"}),
            action=lambda f, r: r.setdefault("multipliers", []).append(
                ("High-risk area", 1.3)
            ),
            priority=40,
            group="location",
            description="High-crime/accident area: 30% surcharge",
        )
    )

    engine.add_rule(
        Rule(
            name="low_risk_area",
            condition=Equals("zip_risk_zone", "low"),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("Low-risk area", 0.1)
            ),
            priority=40,
            group="location",
            description="Low-risk area: 10% discount",
        )
    )

    # ─── Discount Rules ──────────────────────────────────────────

    engine.add_rule(
        Rule(
            name="multi_policy_discount",
            condition=GreaterThan("total_policies", 1),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("Multi-policy", 0.1)
            ),
            priority=50,
            group="discounts",
            description="Multiple policies: 10% discount",
        )
    )

    engine.add_rule(
        Rule(
            name="good_driver_discount",
            condition=Equals("accidents_3yr", 0) & Equals("speeding_tickets", 0),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("Clean record", 0.15)
            ),
            priority=50,
            group="discounts",
            description="No accidents, no tickets: 15% discount",
        )
    )

    engine.add_rule(
        Rule(
            name="loyalty_discount",
            condition=GreaterThan("years_as_customer", 5),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("Loyalty (5+ years)", 0.08)
            ),
            priority=50,
            group="discounts",
            description="5+ years as customer: 8% discount",
        )
    )

    engine.add_rule(
        Rule(
            name="safe_vehicle_discount",
            condition=GreaterThan("safety_rating", 4),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("High safety rating", 0.05)
            ),
            priority=50,
            group="discounts",
            description="Safety rating > 4: 5% discount",
        )
    )

    engine.add_rule(
        Rule(
            name="low_mileage_discount",
            condition=LessThan("annual_mileage", 8000),
            action=lambda f, r: r.setdefault("discounts", []).append(
                ("Low mileage", 0.07)
            ),
            priority=50,
            group="discounts",
            description="Under 8000 miles/year: 7% discount",
        )
    )

    return engine


def calculate_premium(results: dict) -> float:
    """Calculate final premium from rule engine results."""
    base = results.get("base_premium", 1000.0)
    multipliers = results.get("multipliers", [])
    discounts = results.get("discounts", [])

    # Apply multipliers
    premium = base
    for _, mult in multipliers:
        premium *= mult

    # Apply discounts (percentage of final)
    total_discount = sum(d for _, d in discounts)
    total_discount = min(total_discount, 0.4)  # Cap at 40% discount
    premium *= 1 - total_discount

    return round(premium, 2)
