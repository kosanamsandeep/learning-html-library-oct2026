"""
=============================================================================
PROJECT 5: CONTACT MANAGEMENT SYSTEM
=============================================================================
FILE: schemas/contact_schema.py
PURPOSE: Advanced schemas with NESTING, VALIDATION, and TRANSFORMATION

WHAT YOU LEARN HERE:
- NESTED SCHEMAS: Schema within schema (like Address inside Contact)
- COMPUTED FIELDS: Fields that don't exist in the model but appear in output
- CONDITIONAL VALIDATION: Rules that depend on other fields
- SCHEMA AS CONTRACT: The schema IS the API documentation

WHY SCHEMAS OVER SIMPLE DTOs:
- DTOs (Project 4) used @dataclass + manual validate()
- Schemas are more DECLARATIVE (describe rules, don't code them)
- Schemas can serialize/deserialize automatically
- Real frameworks (Marshmallow, Pydantic) use this pattern

FOR LEARNING: We build our own mini-schema system to understand the concept.
In production, you'd use Pydantic or Marshmallow.
=============================================================================
"""

from dataclasses import dataclass, field
from typing import Any
import re

# =============================================================================
# NESTED SCHEMAS - Define validation for sub-objects
# =============================================================================


@dataclass
class AddressSchema:
    """
    Schema for validating address data.

    NESTED SCHEMA CONCEPT:
    - ContactSchema contains AddressSchema (nested)
    - Each level validates independently
    - Errors are namespaced: "addresses[0].zip_code: invalid format"
    """

    VALID_TYPES = ["HOME", "WORK", "OTHER"]

    @staticmethod
    def validate(data: dict) -> list[str]:
        """Validate address data."""
        errors: list[str] = []

        if not data.get("street", "").strip():
            errors.append("street is required")

        if not data.get("city", "").strip():
            errors.append("city is required")

        if not data.get("state", "").strip():
            errors.append("state is required")

        zip_code = data.get("zip_code", "")
        if not zip_code:
            errors.append("zip_code is required")
        elif not re.match(r"^\d{5}(-\d{4})?$", zip_code):
            errors.append("zip_code must be in format 12345 or 12345-6789")

        addr_type = data.get("address_type", "HOME")
        if addr_type not in AddressSchema.VALID_TYPES:
            errors.append(f"address_type must be one of {AddressSchema.VALID_TYPES}")

        return errors

    @staticmethod
    def to_model(data: dict) -> dict:
        """Transform and clean raw data for model creation."""
        return {
            "street": data["street"].strip(),
            "city": data["city"].strip(),
            "state": data["state"].strip().upper(),
            "zip_code": data["zip_code"].strip(),
            "country": data.get("country", "US").strip().upper(),
            "address_type": data.get("address_type", "HOME").upper(),
        }


@dataclass
class PhoneSchema:
    """Schema for phone number validation."""

    VALID_TYPES = ["MOBILE", "HOME", "WORK"]

    @staticmethod
    def validate(data: dict) -> list[str]:
        """Perform the validate step used by this project."""
        errors: list[str] = []

        number = data.get("number", "")
        if not number:
            errors.append("number is required")
        elif not re.match(r"^\+?[\d\s\-\(\)]{7,15}$", number):
            errors.append("invalid phone number format")

        phone_type = data.get("phone_type", "MOBILE")
        if phone_type not in PhoneSchema.VALID_TYPES:
            errors.append(f"phone_type must be one of {PhoneSchema.VALID_TYPES}")

        return errors


@dataclass
class EmailSchema:
    """Schema for email validation."""

    VALID_TYPES = ["PERSONAL", "WORK"]

    @staticmethod
    def validate(data: dict) -> list[str]:
        """Perform the validate step used by this project."""
        errors: list[str] = []

        email = data.get("email", "")
        if not email:
            errors.append("email is required")
        elif not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            errors.append("invalid email format")

        email_type = data.get("email_type", "PERSONAL")
        if email_type not in EmailSchema.VALID_TYPES:
            errors.append(f"email_type must be one of {EmailSchema.VALID_TYPES}")

        return errors


# =============================================================================
# MAIN CONTACT SCHEMA - Orchestrates nested validation
# =============================================================================


class ContactSchema:
    """
    Master schema for Contact validation.

    NESTED SCHEMA PATTERN:
    - Validates top-level fields (first_name, last_name)
    - Delegates to nested schemas (AddressSchema, PhoneSchema, EmailSchema)
    - Collects ALL errors with clear paths (addresses[0].street)

    THIS IS HOW ENTERPRISE SYSTEMS WORK:
    - Define schema once
    - Use for CREATE validation
    - Use for UPDATE validation (partial)
    - Use for SERIALIZATION (model → dict)
    - Schema IS the documentation
    """

    @staticmethod
    def validate_create(data: dict) -> list[str]:
        """
        Validate data for creating a new contact.

        VALIDATES:
        1. Required top-level fields
        2. Each nested address (delegated to AddressSchema)
        3. Each nested phone (delegated to PhoneSchema)
        4. Each nested email (delegated to EmailSchema)
        5. Cross-field rules (at least one email required)
        """
        errors: list[str] = []

        # === TOP-LEVEL VALIDATION ===
        if not data.get("first_name", "").strip():
            errors.append("first_name is required")

        if not data.get("last_name", "").strip():
            errors.append("last_name is required")

        # === NESTED: ADDRESSES (optional but validate if provided) ===
        addresses = data.get("addresses", [])
        for i, addr in enumerate(addresses):
            addr_errors = AddressSchema.validate(addr)
            for err in addr_errors:
                errors.append(f"addresses[{i}].{err}")

        # === NESTED: PHONES ===
        phones = data.get("phones", [])
        for i, phone in enumerate(phones):
            phone_errors = PhoneSchema.validate(phone)
            for err in phone_errors:
                errors.append(f"phones[{i}].{err}")

        # === NESTED: EMAILS (at least one required) ===
        emails = data.get("emails", [])
        if not emails:
            errors.append("at least one email is required")
        else:
            for i, email in enumerate(emails):
                email_errors = EmailSchema.validate(email)
                for err in email_errors:
                    errors.append(f"emails[{i}].{err}")

        # === CROSS-FIELD VALIDATION ===
        # If company is provided, job_title should also be provided
        if data.get("company") and not data.get("job_title"):
            errors.append("job_title is recommended when company is provided")

        return errors

    @staticmethod
    def validate_update(data: dict) -> list[str]:
        """Validate partial update (only check provided fields)."""
        errors: list[str] = []

        if "first_name" in data and not data["first_name"].strip():
            errors.append("first_name cannot be empty")

        if "last_name" in data and not data["last_name"].strip():
            errors.append("last_name cannot be empty")

        if "addresses" in data:
            for i, addr in enumerate(data["addresses"]):
                addr_errors = AddressSchema.validate(addr)
                for err in addr_errors:
                    errors.append(f"addresses[{i}].{err}")

        return errors

    @staticmethod
    def serialize(contact: Any) -> dict:
        """
        Convert Contact model to dictionary (for API response).

        THIS IS SERIALIZATION:
        - Model → Dict → JSON
        - Controls exactly what the client sees
        - Adds computed fields (full_name, primary_email)
        """
        return {
            "contact_id": contact.contact_id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,  # COMPUTED FIELD
            "company": contact.company,
            "job_title": contact.job_title,
            "primary_email": contact.primary_email,  # COMPUTED FIELD
            "primary_phone": contact.primary_phone,  # COMPUTED FIELD
            "addresses": [
                {
                    "street": a.street,
                    "city": a.city,
                    "state": a.state,
                    "zip_code": a.zip_code,
                    "country": a.country,
                    "address_type": a.address_type,
                    "full_address": a.get_full_address(),  # COMPUTED
                }
                for a in contact.addresses
            ],
            "phones": [
                {
                    "number": p.number,
                    "phone_type": p.phone_type,
                    "is_primary": p.is_primary,
                }
                for p in contact.phones
            ],
            "emails": [
                {
                    "email": e.email,
                    "email_type": e.email_type,
                    "is_primary": e.is_primary,
                }
                for e in contact.emails
            ],
            "tags": contact.tags,
            "notes": contact.notes,
            "created_at": contact.created_at.isoformat(),
            "updated_at": contact.updated_at.isoformat(),
        }
