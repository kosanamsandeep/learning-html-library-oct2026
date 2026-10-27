"""
=============================================================================
PROJECT 8: AUTHENTICATION PLATFORM
=============================================================================
FILE: providers/local_auth_provider.py
PURPOSE: LOCAL authentication - username/password validation

This is ONE implementation of the AuthProvider interface.
The app doesn't know this exists - it only knows about the interface!
=============================================================================
"""

import uuid
import hashlib
from datetime import datetime, timedelta

from interfaces.auth_provider import (
    AuthProvider,
    PasswordHasher,
    TokenStore,
    AuthUser,
    AuthToken,
    AuthResult,
)


class SimplePasswordHasher(PasswordHasher):
    """
    Simple password hashing implementation.

    NOTE: In production, use bcrypt or argon2!
    This uses SHA-256 + salt for demonstration purposes.
    """

    def hash_password(self, password: str) -> str:
        """Hash password with a salt."""
        salt = uuid.uuid4().hex[:16]
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}:{hashed}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against stored hash."""
        parts = hashed.split(":")
        if len(parts) != 2:
            return False
        salt, stored_hash = parts
        computed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return computed == stored_hash


class MemoryTokenStore(TokenStore):
    """In-memory token storage."""

    def __init__(self) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._tokens: dict[str, AuthToken] = {}

    def store_token(self, token: AuthToken) -> None:
        """Perform the store token step used by this project."""
        self._tokens[token.token] = token

    def get_token(self, token_str: str) -> AuthToken | None:
        """Return the requested item or information if it exists."""
        token = self._tokens.get(token_str)
        if token and token.is_expired:
            del self._tokens[token_str]
            return None
        return token

    def revoke_token(self, token_str: str) -> bool:
        """Perform the revoke token step used by this project."""
        if token_str in self._tokens:
            del self._tokens[token_str]
            return True
        return False

    def cleanup_expired(self) -> int:
        """Perform the cleanup expired step used by this project."""
        expired = [k for k, v in self._tokens.items() if v.is_expired]
        for k in expired:
            del self._tokens[k]
        return len(expired)


class LocalAuthProvider(AuthProvider):
    """
    Local username/password authentication.

    IMPLEMENTS AuthProvider interface:
    - authenticate(): check username + password
    - validate_token(): verify a JWT-like token
    - revoke_token(): logout

    DEPENDS ON INTERFACES (not concrete classes):
    - PasswordHasher (could be bcrypt, argon2, etc.)
    - TokenStore (could be memory, Redis, etc.)

    This is DEPENDENCY INVERSION:
    - This class depends on ABSTRACTIONS
    - Not on concrete implementations
    """

    def __init__(self, hasher: PasswordHasher, token_store: TokenStore) -> None:
        """
        DEPENDENCY INJECTION of both the hasher and token store.

        We can swap either without changing this class!
        """
        self._hasher = hasher
        self._token_store = token_store
        # Simulated user database
        self._users: dict[str, dict] = {}

    def register_user(
        self, username: str, password: str, email: str, roles: list[str] | None = None
    ) -> str:
        """Register a new user (setup method)."""
        if username in self._users:
            raise ValueError(f"User '{username}' already exists")

        user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
        self._users[username] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hash": self._hasher.hash_password(password),
            "roles": roles or ["user"],
        }
        return user_id

    def authenticate(self, credentials: dict) -> AuthResult:
        """
        Authenticate with username and password.

        INTERFACE IMPLEMENTATION:
        - Receives generic dict (interface contract)
        - Extracts username/password (provider-specific)
        - Returns standard AuthResult (interface contract)
        """
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        # Find user
        user_data = self._users.get(username)
        if user_data is None:
            return AuthResult(success=False, error="Invalid username or password")

        # Verify password using injected hasher
        if not self._hasher.verify_password(password, user_data["password_hash"]):
            return AuthResult(success=False, error="Invalid username or password")

        # Create token
        token = AuthToken(
            token=uuid.uuid4().hex,
            user_id=user_data["user_id"],
            expires_at=datetime.now() + timedelta(hours=24),
        )
        self._token_store.store_token(token)

        # Create auth user
        auth_user = AuthUser(
            user_id=user_data["user_id"],
            username=username,
            email=user_data["email"],
            roles=user_data["roles"],
            provider="local",
            authenticated_at=datetime.now(),
        )

        return AuthResult(success=True, user=auth_user, token=token)

    def validate_token(self, token_str: str) -> AuthResult:
        """Validate a token and return user info."""
        token = self._token_store.get_token(token_str)
        if token is None:
            return AuthResult(success=False, error="Invalid or expired token")

        # Find user by ID
        for user_data in self._users.values():
            if user_data["user_id"] == token.user_id:
                auth_user = AuthUser(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    roles=user_data["roles"],
                    provider="local",
                    authenticated_at=datetime.now(),
                )
                return AuthResult(success=True, user=auth_user, token=token)

        return AuthResult(success=False, error="User not found")

    def revoke_token(self, token_str: str) -> bool:
        """Perform the revoke token step used by this project."""
        return self._token_store.revoke_token(token_str)

    def get_provider_name(self) -> str:
        """Return the requested item or information if it exists."""
        return "local"
