"""
=============================================================================
PROJECT 8: AUTHENTICATION PLATFORM
=============================================================================
FILE: interfaces/auth_provider.py
PURPOSE: Define ABSTRACT INTERFACES for authentication

WHAT YOU LEARN HERE:
- ABSTRACT CLASSES as pure interfaces (no implementation)
- DEPENDENCY INVERSION: High-level modules don't depend on low-level
- PLUG-AND-PLAY: Swap authentication providers without changing app code
- Interface = "Universal Plug Point"

THE PLUG POINT ANALOGY:
- Your app is like an electrical device
- The interface is the standardized power outlet shape
- Providers are different power sources (wall, battery, solar)
- The device doesn't care WHERE power comes from!
=============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# VALUE OBJECTS (shared across implementations)
# =============================================================================


@dataclass
class AuthUser:
    """Represents an authenticated user (returned by any provider)."""

    user_id: str
    username: str
    email: str
    roles: list[str]
    provider: str  # Which auth provider was used
    authenticated_at: datetime


@dataclass
class AuthToken:
    """Represents an authentication token."""

    token: str
    user_id: str
    expires_at: datetime
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        """Return True when the checked condition is satisfied."""
        return datetime.now() > self.expires_at


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    success: bool
    user: AuthUser | None = None
    token: AuthToken | None = None
    error: str = ""


# =============================================================================
# ABSTRACT INTERFACES (the "plug points")
# =============================================================================


class AuthProvider(ABC):
    """
    INTERFACE: Any authentication provider must implement these methods.

    THIS IS THE "UNIVERSAL PLUG":
    - LocalAuthProvider implements this (username/password)
    - OAuthProvider implements this (Google/GitHub login)
    - LDAPProvider implements this (corporate directory)
    - TokenProvider implements this (API keys)

    Your application code ONLY knows about this interface.
    It never knows about the specific provider being used.
    """

    @abstractmethod
    def authenticate(self, credentials: dict) -> AuthResult:
        """
        Authenticate a user with provider-specific credentials.

        The dict format depends on the provider:
        - Local: {"username": "...", "password": "..."}
        - OAuth: {"code": "...", "redirect_uri": "..."}
        - API Key: {"api_key": "..."}
        """
        pass

    @abstractmethod
    def validate_token(self, token: str) -> AuthResult:
        """Validate an existing token and return user info."""
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """Invalidate a token (logout)."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of this provider."""
        pass


class PasswordHasher(ABC):
    """
    INTERFACE for password hashing strategies.

    WHY ABSTRACT?
    - Different algorithms: bcrypt, argon2, scrypt
    - Can upgrade algorithms without changing auth logic
    - Can use different strategies for different security levels
    """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        pass


class TokenStore(ABC):
    """
    INTERFACE for token storage.

    Tokens could be stored in:
    - Memory (fast, not persistent)
    - Redis (fast, distributed)
    - Database (persistent, slower)
    """

    @abstractmethod
    def store_token(self, token: AuthToken) -> None:
        """Perform the store token step used by this project."""
        pass

    @abstractmethod
    def get_token(self, token_str: str) -> AuthToken | None:
        """Return the requested item or information if it exists."""
        pass

    @abstractmethod
    def revoke_token(self, token_str: str) -> bool:
        """Perform the revoke token step used by this project."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired tokens, return count removed."""
        pass
