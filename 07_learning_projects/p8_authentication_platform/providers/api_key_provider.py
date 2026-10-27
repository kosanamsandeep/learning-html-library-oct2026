"""
=============================================================================
PROJECT 8: AUTHENTICATION PLATFORM
=============================================================================
FILE: providers/api_key_provider.py
PURPOSE: API Key authentication - ANOTHER implementation of same interface

THIS DEMONSTRATES:
- Same interface (AuthProvider), completely different mechanism
- API keys are pre-generated, no username/password at auth time
- Shows how one interface can have wildly different implementations
=============================================================================
"""

import uuid
from datetime import datetime, timedelta

from interfaces.auth_provider import (
    AuthProvider,
    AuthUser,
    AuthToken,
    AuthResult,
    TokenStore,
)


class ApiKeyProvider(AuthProvider):
    """
    API Key authentication provider.

    SAME INTERFACE as LocalAuthProvider!
    But works completely differently:
    - No username/password
    - Pre-shared API key
    - Often used for service-to-service communication
    """

    def __init__(self, token_store: TokenStore) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._token_store = token_store
        self._api_keys: dict[str, dict] = {}  # api_key → user info

    def register_api_key(
        self, service_name: str, roles: list[str] | None = None
    ) -> str:
        """Create a new API key for a service."""
        api_key = f"ak_{uuid.uuid4().hex}"
        self._api_keys[api_key] = {
            "user_id": f"SVC-{uuid.uuid4().hex[:8].upper()}",
            "username": service_name,
            "email": f"{service_name}@internal.system",
            "roles": roles or ["service"],
        }
        return api_key

    def authenticate(self, credentials: dict) -> AuthResult:
        """Authenticate using an API key."""
        api_key = credentials.get("api_key", "")

        user_data = self._api_keys.get(api_key)
        if user_data is None:
            return AuthResult(success=False, error="Invalid API key")

        # API keys create long-lived tokens
        token = AuthToken(
            token=uuid.uuid4().hex,
            user_id=user_data["user_id"],
            expires_at=datetime.now() + timedelta(days=30),
        )
        self._token_store.store_token(token)

        auth_user = AuthUser(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            roles=user_data["roles"],
            provider="api_key",
            authenticated_at=datetime.now(),
        )

        return AuthResult(success=True, user=auth_user, token=token)

    def validate_token(self, token_str: str) -> AuthResult:
        """Validate input and raise or return an error when it is not acceptable."""
        token = self._token_store.get_token(token_str)
        if token is None:
            return AuthResult(success=False, error="Invalid or expired token")

        for user_data in self._api_keys.values():
            if user_data["user_id"] == token.user_id:
                auth_user = AuthUser(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    roles=user_data["roles"],
                    provider="api_key",
                    authenticated_at=datetime.now(),
                )
                return AuthResult(success=True, user=auth_user, token=token)

        return AuthResult(success=False, error="Service not found")

    def revoke_token(self, token_str: str) -> bool:
        """Perform the revoke token step used by this project."""
        return self._token_store.revoke_token(token_str)

    def get_provider_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "api_key"
