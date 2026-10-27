"""
PROJECT 8: AUTHENTICATION PLATFORM - Demo
Demonstrates plug-and-play auth providers via interfaces.
"""

from providers.local_auth_provider import (
    LocalAuthProvider,
    SimplePasswordHasher,
    MemoryTokenStore,
)
from providers.api_key_provider import ApiKeyProvider
from services.auth_service import AuthService


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("     AUTHENTICATION PLATFORM - Interfaces & DI Demo")
    print("=" * 60)

    # === WIRE UP (Dependency Injection) ===
    hasher = SimplePasswordHasher()
    token_store = MemoryTokenStore()

    # Create providers (each implements AuthProvider interface)
    local_provider = LocalAuthProvider(hasher, token_store)
    api_key_provider = ApiKeyProvider(token_store)

    # Register providers with the service
    auth_service = AuthService()
    auth_service.register_provider(local_provider)
    auth_service.register_provider(api_key_provider)

    print(f"\n  Available providers: {auth_service.get_available_providers()}")

    # === Setup: Register users and API keys ===
    local_provider.register_user(
        "alice", "secure_pass_123", "alice@example.com", ["admin", "user"]
    )
    local_provider.register_user("bob", "bob_pass_456", "bob@example.com", ["user"])
    payment_key = api_key_provider.register_api_key(
        "payment-service", ["service", "payment"]
    )

    # === Demo 1: Local authentication ===
    print("\n🔐 Demo 1: Local Authentication (username/password)")
    result = auth_service.authenticate(
        "local", {"username": "alice", "password": "secure_pass_123"}
    )
    print(f"  Success: {result.success}")
    print(f"  User: {result.user.username} (roles: {result.user.roles})")
    print(f"  Token: {result.token.token[:16]}...")
    alice_token = result.token.token

    # === Demo 2: Failed authentication ===
    print("\n❌ Demo 2: Failed Authentication")
    bad_result = auth_service.authenticate(
        "local", {"username": "alice", "password": "wrong!"}
    )
    print(f"  Success: {bad_result.success}")
    print(f"  Error: {bad_result.error}")

    # === Demo 3: API Key authentication ===
    print("\n🔑 Demo 3: API Key Authentication")
    result2 = auth_service.authenticate("api_key", {"api_key": payment_key})
    print(f"  Success: {result2.success}")
    print(f"  Service: {result2.user.username} (roles: {result2.user.roles})")
    print(f"  Provider: {result2.user.provider}")

    # === Demo 4: Token validation (works across providers!) ===
    print("\n✅ Demo 4: Token Validation")
    validation = auth_service.validate_token(alice_token)
    print(f"  Token valid: {validation.success}")
    print(f"  Belongs to: {validation.user.username}")

    # === Demo 5: Logout ===
    print("\n🚪 Demo 5: Logout (revoke token)")
    auth_service.logout(alice_token)
    validation_after = auth_service.validate_token(alice_token)
    print(f"  Token valid after logout: {validation_after.success}")
    print(f"  Error: {validation_after.error}")

    # === Demo 6: Unknown provider ===
    print("\n❓ Demo 6: Unknown Provider")
    unknown = auth_service.authenticate("oauth", {"code": "abc"})
    print(f"  Success: {unknown.success}")
    print(f"  Error: {unknown.error}")

    print("\n🔌 KEY INSIGHT: Same AuthService interface, different providers!")
    print("   Adding OAuth? Just create OAuthProvider implementing AuthProvider.")
    print("   Register it. Done. No other code changes needed!")
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
