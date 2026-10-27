"""
PROJECT 5: CONTACT MANAGEMENT - Service Layer
"""

import uuid
from models.contact import Contact, Address, PhoneNumber, EmailAddress
from schemas.contact_schema import ContactSchema


class ContactService:
    """Manages contacts with schema-based validation."""

    def __init__(self) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._contacts: dict[str, Contact] = {}

    def create_contact(self, data: dict) -> dict:
        """Create a contact after schema validation."""
        errors = ContactSchema.validate_create(data)
        if errors:
            raise ValueError(f"Validation errors: {errors}")

        contact_id = f"CON-{uuid.uuid4().hex[:8].upper()}"

        # Build nested objects from validated data
        addresses = [
            Address(
                **{
                    "street": a["street"].strip(),
                    "city": a["city"].strip(),
                    "state": a["state"].strip().upper(),
                    "zip_code": a["zip_code"].strip(),
                    "country": a.get("country", "US"),
                    "address_type": a.get("address_type", "HOME"),
                }
            )
            for a in data.get("addresses", [])
        ]

        phones = [
            PhoneNumber(
                number=p["number"],
                phone_type=p.get("phone_type", "MOBILE"),
                is_primary=p.get("is_primary", False),
            )
            for p in data.get("phones", [])
        ]

        emails = [
            EmailAddress(
                email=e["email"],
                email_type=e.get("email_type", "PERSONAL"),
                is_primary=e.get("is_primary", False),
            )
            for e in data.get("emails", [])
        ]

        # Ensure at least one email is primary
        if emails and not any(e.is_primary for e in emails):
            emails[0].is_primary = True

        contact = Contact(
            contact_id=contact_id,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            company=data.get("company", ""),
            job_title=data.get("job_title", ""),
            addresses=addresses,
            phones=phones,
            emails=emails,
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )

        self._contacts[contact_id] = contact
        return ContactSchema.serialize(contact)

    def get_contact(self, contact_id: str) -> dict | None:
        """Return the requested item or information if it exists."""
        contact = self._contacts.get(contact_id)
        if contact is None:
            return None
        return ContactSchema.serialize(contact)

    def search_contacts(self, query: str) -> list[dict]:
        """Search contacts by name, company, or email."""
        query_lower = query.lower()
        results = []
        for contact in self._contacts.values():
            if (
                query_lower in contact.full_name.lower()
                or query_lower in contact.company.lower()
                or any(query_lower in e.email.lower() for e in contact.emails)
            ):
                results.append(ContactSchema.serialize(contact))
        return results

    def get_contacts_by_tag(self, tag: str) -> list[dict]:
        """Find contacts with a specific tag."""
        tag_lower = tag.lower()
        return [
            ContactSchema.serialize(c)
            for c in self._contacts.values()
            if tag_lower in c.tags
        ]

    def get_all_contacts(self) -> list[dict]:
        """Return the requested item or information if it exists."""
        return [ContactSchema.serialize(c) for c in self._contacts.values()]
