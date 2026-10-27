"""PROJECT 5: CONTACT MANAGEMENT - Demo"""

from services.contact_service import ContactService
from schemas.contact_schema import ContactSchema
import json


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("     CONTACT MANAGEMENT - Nested Schemas Demo")
    print("=" * 60)

    service = ContactService()

    # Create a complex contact with nested data
    print("\n📋 Creating contact with nested objects...")
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "company": "TechCorp",
        "job_title": "Senior Engineer",
        "addresses": [
            {
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102",
                "address_type": "WORK",
            },
            {
                "street": "456 Oak Ave",
                "city": "Oakland",
                "state": "CA",
                "zip_code": "94601",
                "address_type": "HOME",
            },
        ],
        "phones": [
            {"number": "+1-555-0100", "phone_type": "MOBILE", "is_primary": True},
            {"number": "+1-555-0200", "phone_type": "WORK", "is_primary": False},
        ],
        "emails": [
            {
                "email": "john.doe@techcorp.com",
                "email_type": "WORK",
                "is_primary": True,
            },
            {"email": "john.doe@gmail.com", "email_type": "PERSONAL"},
        ],
        "tags": ["vip", "engineer", "west-coast"],
        "notes": "Key contact for Platform team",
    }

    result = service.create_contact(contact_data)
    print(f"  Created: {result['full_name']} ({result['contact_id']})")
    print(f"  Primary Email: {result['primary_email']}")
    print(f"  Primary Phone: {result['primary_phone']}")
    print(f"  Addresses: {len(result['addresses'])}")
    print(f"  Tags: {result['tags']}")

    # Show nested validation
    print("\n❌ Nested Validation Errors Demo:")
    bad_data = {
        "first_name": "",
        "last_name": "Smith",
        "addresses": [
            {"street": "", "city": "NY", "state": "NY", "zip_code": "INVALID"}
        ],
        "emails": [],  # Required!
    }
    errors = ContactSchema.validate_create(bad_data)
    for err in errors:
        print(f"    ⚠️  {err}")

    # Search
    print("\n🔍 Search Demo:")
    results = service.search_contacts("john")
    print(f"  Found {len(results)} contact(s) matching 'john'")

    # Tag-based lookup
    print("\n🏷️  Tag-based lookup (tag='vip'):")
    tagged = service.get_contacts_by_tag("vip")
    for c in tagged:
        print(f"    {c['full_name']} - {c['company']}")

    # Full serialized output
    print("\n📄 Full Serialized Output (what API would return):")
    print(json.dumps(result, indent=2, default=str)[:500] + "...")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
