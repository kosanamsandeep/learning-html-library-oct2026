"""Password validator built test-first in P5.

We arrived at this implementation by writing one failing test at a time and
making it pass with the smallest possible code change. The README walks
through each Red-Green-Refactor step.
"""

from __future__ import annotations

import string
from dataclasses import dataclass

MIN_LENGTH = 8
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:,.?/"


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


def validate_password(password: str) -> ValidationResult:
    errors: list[str] = []

    if len(password) < MIN_LENGTH:
        errors.append(f"must be at least {MIN_LENGTH} characters")
    if " " in password:
        errors.append("must not contain spaces")
    if not any(c.isupper() for c in password):
        errors.append("must contain at least one uppercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("must contain at least one digit")
    if not any(c in SPECIAL_CHARS for c in password):
        errors.append("must contain at least one special character")

    return ValidationResult(ok=not errors, errors=errors)
