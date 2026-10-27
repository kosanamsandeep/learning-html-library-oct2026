"""
PROJECT 18: MULTI-TENANT SAAS PLATFORM
========================================
Patterns: Multi-Tenancy, Feature Flags, Tenant Isolation, Strategy Pattern
Inspired by: Stripe, Shopify, AWS Organizations, LaunchDarkly

Story: You're building a SaaS project management tool. Multiple companies
(tenants) share the same application, but each sees only their own data.
Features are gated by plan tier, and new features are rolled out gradually.

Key Concepts Demonstrated:
  1. Tenant isolation (data never leaks between tenants)
  2. Plan-based feature gating
  3. Feature flags (gradual rollout, A/B testing, kill switch)
  4. Context-based tenant resolution
  5. Resource limits per plan
"""

import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from tenant.models import Tenant, TenantContext, Plan, PLAN_LIMITS, TenantUser
from features.feature_flags import FeatureFlagService, FeatureFlag, FlagStrategy
from storage.tenant_store import TenantScopedStore


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 18: MULTI-TENANT SAAS PLATFORM")
    print("#  Patterns: Multi-Tenancy, Feature Flags, Tenant Isolation")
    print("#  Inspired by: Stripe, Shopify, LaunchDarkly, AWS Organizations")
    print("=" * 70)


def demo_1_tenant_isolation():
    """Demo: Data isolation between tenants."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Tenant Data Isolation")
    print("=" * 70)

    store = TenantScopedStore()

    # Create tenants
    acme = Tenant(tenant_id="acme", name="Acme Corp", plan=Plan.PROFESSIONAL)
    globex = Tenant(tenant_id="globex", name="Globex Inc", plan=Plan.STARTER)
    wayne = Tenant(tenant_id="wayne", name="Wayne Enterprises", plan=Plan.ENTERPRISE)

    # Acme creates projects
    TenantContext.set_current(acme)
    store.insert("projects", "proj-1", {"name": "Website Redesign", "status": "active"})
    store.insert("projects", "proj-2", {"name": "Mobile App", "status": "planning"})
    store.insert("projects", "proj-3", {"name": "API Migration", "status": "active"})

    # Globex creates projects
    TenantContext.set_current(globex)
    store.insert("projects", "proj-1", {"name": "Laser Cannon", "status": "secret"})
    store.insert("projects", "proj-2", {"name": "Weather Machine", "status": "active"})

    # Wayne creates projects
    TenantContext.set_current(wayne)
    store.insert("projects", "proj-1", {"name": "Batsuit v3", "status": "active"})

    # Now demonstrate isolation
    print(f"\n  Each tenant can ONLY see their own data:")

    TenantContext.set_current(acme)
    acme_projects = store.find_all("projects")
    print(f"\n    Acme Corp ({acme.plan.value}) sees {len(acme_projects)} projects:")
    for p in acme_projects:
        print(f"      - {p.data['name']} [{p.data['status']}]")

    TenantContext.set_current(globex)
    globex_projects = store.find_all("projects")
    print(
        f"\n    Globex Inc ({globex.plan.value}) sees {len(globex_projects)} projects:"
    )
    for p in globex_projects:
        print(f"      - {p.data['name']} [{p.data['status']}]")

    TenantContext.set_current(wayne)
    wayne_projects = store.find_all("projects")
    print(
        f"\n    Wayne Enterprises ({wayne.plan.value}) sees {len(wayne_projects)} project:"
    )
    for p in wayne_projects:
        print(f"      - {p.data['name']} [{p.data['status']}]")

    # Admin view (cross-tenant)
    all_records = store.get_all_records_admin("projects")
    print(f"\n    Admin view (ALL tenants): {len(all_records)} total records")

    print(f"\n  Key insight: Same 'projects' collection, same record IDs,")
    print(
        f"  but each tenant is completely isolated. Globex can never see Acme's data."
    )

    TenantContext.clear()
    return store, acme, globex, wayne


def demo_2_plan_limits():
    """Demo: Plan-based resource limits."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Plan-Based Resource Limits")
    print("=" * 70)

    print(f"\n  Plan Comparison:")
    print(f"  {'Plan':<15s} {'Users':<8s} {'Storage':<10s} {'API Calls':<12s} Features")
    print(f"  {'-'*75}")

    for plan, limits in PLAN_LIMITS.items():
        storage = (
            f"{limits.max_storage_mb}MB"
            if limits.max_storage_mb < 10000
            else f"{limits.max_storage_mb//1000}GB"
        )
        print(
            f"  {plan.value:<15s} {limits.max_users:<8d} {storage:<10s} "
            f"{limits.max_api_calls_per_day:<12,d} {len(limits.features)} features"
        )

    # Show feature differences
    print(f"\n  Feature availability by plan:")
    all_features = sorted(PLAN_LIMITS[Plan.ENTERPRISE].features)
    for feature in all_features:
        available_in = [
            p.value[0].upper() for p in Plan if feature in PLAN_LIMITS[p].features
        ]
        print(f"    {feature:<25s} {''.join(available_in)}")

    # Simulate limit enforcement
    print(f"\n  Limit enforcement example:")
    free_tenant = Tenant(tenant_id="small-biz", name="Small Biz", plan=Plan.FREE)
    print(f"    Tenant: {free_tenant.name} (plan: {free_tenant.plan.value})")
    print(f"    Max users: {free_tenant.limits.max_users}")
    print(f"    Try adding user 4: BLOCKED (limit: {free_tenant.limits.max_users})")
    print(f"    Has 'sso' feature: {'sso' in free_tenant.limits.features}")
    print(f"    Has 'basic_reports': {'basic_reports' in free_tenant.limits.features}")


def demo_3_feature_flags():
    """Demo: Feature flags for controlled rollout."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Feature Flags (Controlled Rollout)")
    print("=" * 70)

    ff_service = FeatureFlagService()

    # Define feature flags
    ff_service.register_flag(
        FeatureFlag(
            key="new_dashboard",
            name="New Dashboard UI",
            description="Redesigned dashboard with analytics",
            strategy=FlagStrategy.PERCENTAGE,
            rollout_percentage=30,  # 30% of tenants
        )
    )

    ff_service.register_flag(
        FeatureFlag(
            key="ai_suggestions",
            name="AI-Powered Suggestions",
            description="ML-based task suggestions",
            strategy=FlagStrategy.PLAN_BASED,
            allowed_plans={Plan.PROFESSIONAL, Plan.ENTERPRISE},
        )
    )

    ff_service.register_flag(
        FeatureFlag(
            key="bulk_export",
            name="Bulk Data Export",
            description="Export all project data",
            strategy=FlagStrategy.BOOLEAN,
            enabled=True,
        )
    )

    ff_service.register_flag(
        FeatureFlag(
            key="beta_gantt",
            name="Beta Gantt Chart",
            description="New Gantt chart view (beta testing)",
            strategy=FlagStrategy.TENANT_LIST,
            allowed_tenants={"acme", "wayne"},
        )
    )

    ff_service.register_flag(
        FeatureFlag(
            key="broken_feature",
            name="Broken Feature (Kill Switch)",
            description="This feature is disabled for everyone",
            strategy=FlagStrategy.BOOLEAN,
            enabled=False,  # Kill switch activated
        )
    )

    # Test with different tenants
    tenants = [
        Tenant(tenant_id="acme", name="Acme Corp", plan=Plan.PROFESSIONAL),
        Tenant(tenant_id="globex", name="Globex Inc", plan=Plan.STARTER),
        Tenant(tenant_id="wayne", name="Wayne Enterprises", plan=Plan.ENTERPRISE),
        Tenant(tenant_id="small-biz", name="Small Biz", plan=Plan.FREE),
    ]

    print(f"\n  Feature flags defined:")
    for flag in ff_service.list_flags():
        print(
            f"    {flag.key:<20s} | {flag.strategy.value:<12s} | enabled={flag.enabled}"
        )

    print(f"\n  Flag evaluation per tenant:")
    print(f"  {'Tenant':<20s}", end="")
    for flag in ff_service.list_flags():
        print(f" {flag.key:<16s}", end="")
    print()
    print(f"  {'-'*100}")

    for tenant in tenants:
        print(f"  {tenant.name:<20s}", end="")
        for flag in ff_service.list_flags():
            enabled = ff_service.is_enabled(flag.key, tenant)
            symbol = "YES" if enabled else " - "
            print(f" {symbol:<16s}", end="")
        print()

    print(f"\n  Key insight: Feature flags decouple deployment from release.")
    print(f"  Deploy code anytime; control who sees features via flags.")


def demo_4_tenant_context():
    """Demo: How tenant context flows through the application."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Tenant Context & Request Middleware")
    print("=" * 70)

    store = TenantScopedStore()
    tenants_db = {
        "acme": Tenant(tenant_id="acme", name="Acme Corp", plan=Plan.PROFESSIONAL),
        "globex": Tenant(tenant_id="globex", name="Globex Inc", plan=Plan.STARTER),
    }

    # Simulate request middleware
    def simulate_request(tenant_id: str, action: str, data: dict = None):
        """Simulates a web request with tenant resolution."""
        # Step 1: Resolve tenant from request (header, subdomain, or path)
        tenant = tenants_db.get(tenant_id)
        if not tenant:
            return {"error": f"Tenant '{tenant_id}' not found"}

        # Step 2: Set tenant context (middleware does this)
        TenantContext.set_current(tenant)

        # Step 3: Execute business logic (automatically scoped)
        try:
            if action == "create_task":
                record = store.insert("tasks", data["id"], data)
                return {"status": "created", "tenant": tenant.name, "task": data["id"]}
            elif action == "list_tasks":
                tasks = store.find_all("tasks")
                return {
                    "status": "ok",
                    "tenant": tenant.name,
                    "count": len(tasks),
                    "tasks": [t.data.get("title", t.record_id) for t in tasks],
                }
        finally:
            # Step 4: Clear context after request
            TenantContext.clear()

    print(f"\n  Simulating HTTP requests with tenant resolution:\n")

    # Acme creates tasks
    requests = [
        ("acme", "create_task", {"id": "t1", "title": "Design mockups"}),
        ("acme", "create_task", {"id": "t2", "title": "Build API"}),
        ("globex", "create_task", {"id": "t1", "title": "World domination plan"}),
        ("acme", "list_tasks", None),
        ("globex", "list_tasks", None),
    ]

    for tenant_id, action, data in requests:
        result = simulate_request(tenant_id, action, data)
        print(f"    [{tenant_id}] {action}: {result}")

    print(f"\n  Flow: Request -> Resolve Tenant -> Set Context -> Execute -> Clear")
    print(f"  The business logic NEVER manually filters by tenant_id.")
    print(f"  The storage layer does it automatically via TenantContext.")


def demo_5_tenant_overrides():
    """Demo: Per-tenant feature flag overrides and A/B testing."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Tenant Overrides & Gradual Rollout")
    print("=" * 70)

    ff_service = FeatureFlagService()

    # A feature rolling out to 50%
    ff_service.register_flag(
        FeatureFlag(
            key="new_editor",
            name="New Rich Text Editor",
            strategy=FlagStrategy.PERCENTAGE,
            rollout_percentage=50,
            # Override: force-enable for beta tester, force-disable for problematic tenant
            tenant_overrides={
                "beta-tester": True,  # Always on
                "problematic": False,  # Always off (had issues)
            },
        )
    )

    # Generate 10 tenants to show rollout distribution
    test_tenants = [
        Tenant(tenant_id=f"tenant-{i:03d}", name=f"Company {i}", plan=Plan.STARTER)
        for i in range(20)
    ]

    # Add special tenants
    beta = Tenant(tenant_id="beta-tester", name="Beta Tester Co", plan=Plan.STARTER)
    problem = Tenant(
        tenant_id="problematic", name="Problematic Corp", plan=Plan.ENTERPRISE
    )

    print(f"\n  Feature: 'new_editor' (50% rollout)")
    print(f"  Override: beta-tester=ALWAYS ON, problematic=ALWAYS OFF\n")

    enabled_count = 0
    print(f"  Regular tenants (50% should get the feature):")
    for t in test_tenants:
        enabled = ff_service.is_enabled("new_editor", t)
        if enabled:
            enabled_count += 1

    print(
        f"    {enabled_count}/{len(test_tenants)} tenants have the feature "
        f"({enabled_count/len(test_tenants)*100:.0f}%)"
    )

    print(f"\n  Override tenants:")
    print(f"    beta-tester: {ff_service.is_enabled('new_editor', beta)} (forced ON)")
    print(
        f"    problematic: {ff_service.is_enabled('new_editor', problem)} (forced OFF)"
    )

    print(f"\n  Key insight: Percentage rollout is DETERMINISTIC (hash-based).")
    print(f"  Same tenant always gets same result (no flickering).")
    print(f"  Overrides let you force-enable for beta or force-disable for issues.")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  MULTI-TENANCY:
     - Multiple customers share ONE application
     - Each tenant's data is ISOLATED
     - Tenant resolved from: subdomain, header, JWT, path
     - Context propagated via ContextVar (thread-safe)

  ISOLATION STRATEGIES:
     - Shared DB + Row filter (this project) - cheapest, most common
     - Shared DB + Schema per tenant - moderate isolation
     - DB per tenant - maximum isolation (enterprise)

  FEATURE FLAGS:
     - Decouple DEPLOYMENT from RELEASE
     - Strategies: boolean, plan-based, percentage, tenant-list
     - Percentage rollout: deterministic hash (no flickering)
     - Overrides: per-tenant force on/off
     - Kill switch: instant disable without deploy

  PLAN-BASED GATING:
     - Features gated by subscription tier
     - Resource limits per plan (users, storage, API calls)
     - Upgrade path drives revenue

  REAL-WORLD EXAMPLES:
     - Stripe: Organization-based multi-tenancy
     - Shopify: Each store is a tenant
     - LaunchDarkly: Feature flag as a service
     - AWS Organizations: Account-level isolation
     - Salesforce: Multi-tenant pioneer (shared DB)
    """)


if __name__ == "__main__":
    print_header()
    demo_1_tenant_isolation()
    demo_2_plan_limits()
    demo_3_feature_flags()
    demo_4_tenant_context()
    demo_5_tenant_overrides()
    print_summary()
