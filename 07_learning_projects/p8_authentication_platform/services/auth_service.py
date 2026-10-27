"""
=============================================================================
PROJECT 8: AUTHENTICATION PLATFORM
=============================================================================
FILE: services/auth_service.py
PURPOSE: Authentication service that works with ANY provider

KEY INSIGHT: This service depends on AuthProvider INTERFACE only.
It never imports LocalAuthProvider or ApiKeyProvider!
=============================================================================
"""

from interfaces.auth_provider import AuthProvider, AuthResult


class AuthService:
    """
    Authentication service supporting multiple providers.

    DEPENDENCY INVERSION IN ACTION:
    - This high-level module depends on abstraction (AuthProvider interface)
    - Low-level modules (Local, OAuth, API Key) also depend on abstraction
    - Neither depends on the other directly!

    MULTI-PROVIDER SUPPORT:
    - Register multiple providers
    - Route authentication to the correct one
    - Unified interface for the application
    """

    def __init__(self) -> None:
        # Registry of available auth providers
        """Initialize the object with the dependencies or starting values it needs."""
        self._providers: dict[str, AuthProvider] = {}

    def register_provider(self, provider: AuthProvider) -> None:
        """
        Register an authentication provider.

        PLUG-AND-PLAY:
        - Add new auth methods by registering new providers
        - No code changes needed in this service!
        - Open/Closed Principle: open for extension, closed for modification
        """
        name = provider.get_provider_name()
        self._providers[name] = provider

    def authenticate(self, provider_name: str, credentials: dict) -> AuthResult:
        """
        Authenticate using a specific provider.

        The service ROUTES to the correct provider.
        It doesn't know HOW each provider works internally.
        """
        provider = self._providers.get(provider_name)
        if provider is None:
            return AuthResult(
                success=False,
                error=f"Unknown provider: {provider_name}. Available: {list(self._providers.keys())}",
            )

        return provider.authenticate(credentials)

    def validate_token(self, token: str) -> AuthResult:
        """
        Validate a token against ALL providers.

        We try each provider until one recognizes the token.
        This allows mixed authentication in the same system.
        """
        for provider in self._providers.values():
            result = provider.validate_token(token)
            if result.success:
                return result

        return AuthResult(success=False, error="Token not recognized by any provider")

    def logout(self, token: str) -> bool:
        """Revoke a token (try all providers)."""
        for provider in self._providers.values():
            if provider.revoke_token(token):
                return True
        return False

    def get_available_providers(self) -> list[str]:
        """List all registered authentication providers."""
        return list(self._providers.keys())
