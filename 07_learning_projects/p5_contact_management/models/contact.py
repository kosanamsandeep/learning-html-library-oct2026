"""
=============================================================================
PROJECT 5: CONTACT MANAGEMENT SYSTEM
=============================================================================
FILE: models/contact.py
PURPOSE: Contact domain models with NESTED objects

WHAT YOU LEARN HERE:
- Complex domain models with nested objects
- Address, Phone, Email are separate VALUE OBJECTS
- A Contact COMPOSES multiple nested objects
- This is real-world data modeling (no flat structures!)
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Address:
    """
    VALUE OBJECT: An address with no identity of its own.

    WHY A SEPARATE CLASS?
    - Addresses have their own validation rules
    - Multiple entities can have addresses (Contact, Company, etc.)
    - Reusable across the system
    """

    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    address_type: str = "HOME"  # HOME, WORK, OTHER

    def get_full_address(self) -> str:
        """Return the requested item or information if it exists."""
        return (
            f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"
        )


@dataclass
class PhoneNumber:
    """Value object for phone numbers."""

    number: str
    phone_type: str = "MOBILE"  # MOBILE, HOME, WORK
    is_primary: bool = False


@dataclass
class EmailAddress:
    """Value object for email addresses."""

    email: str
    email_type: str = "PERSONAL"  # PERSONAL, WORK
    is_primary: bool = False


@dataclass
class Contact:
    """
    Main Contact entity - COMPOSED of nested value objects.

    REAL-WORLD COMPLEXITY:
    - A contact can have MULTIPLE addresses, phones, emails
    - Each has a type (home, work) and one is primary
    - This models how CRMs actually work (Salesforce, HubSpot)

    NESTED COMPOSITION:
    Contact
    ├── List[Address]          (one-to-many)
    ├── List[PhoneNumber]      (one-to-many)
    ├── List[EmailAddress]     (one-to-many)
    └── Dict[str, str] tags    (metadata)
    """

    contact_id: str
    first_name: str
    last_name: str
    company: str = ""
    job_title: str = ""
    addresses: list[Address] = field(default_factory=list)
    phones: list[PhoneNumber] = field(default_factory=list)
    emails: list[EmailAddress] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def full_name(self) -> str:
        """Perform the full name step used by this project."""
        return f"{self.first_name} {self.last_name}"

    @property
    def primary_email(self) -> str | None:
        """Get the primary email address."""
        for email in self.emails:
            if email.is_primary:
                return email.email
        return self.emails[0].email if self.emails else None

    @property
    def primary_phone(self) -> str | None:
        """Get the primary phone number."""
        for phone in self.phones:
            if phone.is_primary:
                return phone.number
        return self.phones[0].number if self.phones else None

    def add_tag(self, tag: str) -> None:
        """Add a tag (lowercase, no duplicates)."""
        tag_lower = tag.lower().strip()
        if tag_lower and tag_lower not in self.tags:
            self.tags.append(tag_lower)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> bool:
        """Remove an item from the current collection or state."""
        tag_lower = tag.lower().strip()
        if tag_lower in self.tags:
            self.tags.remove(tag_lower)
            self.updated_at = datetime.now()
            return True
        return False
