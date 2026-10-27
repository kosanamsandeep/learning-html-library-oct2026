"""
PROJECT 7: HEALTHTRACK - Demo of full layered architecture
Request → API → DTO → Service → Repository → Model → Response
"""

import json
from repositories.health_repository import MemoryHealthRepository
from services.health_service import HealthService
from api.health_api import HealthAPI


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("     HEALTHTRACK - Full Layered Architecture Demo")
    print("=" * 60)
    print("\n  Flow: API → DTO → Service → Repository → Model → DTO → Response")

    # Wire up the layers (Dependency Injection)
    repo = MemoryHealthRepository()
    service = HealthService(repo)
    api = HealthAPI(service)

    # === Simulate API calls ===
    print("\n📋 POST /api/health-records (Create patient record)")
    response = api.create_record(
        {
            "patient_name": "Alice Johnson",
            "date_of_birth": "1985-03-15",
            "blood_type": "A+",
            "allergies": ["Penicillin", "Shellfish"],
            "medications": ["Lisinopril 10mg"],
        }
    )
    print(f"  Status: {response['status']}")
    record_id = response["data"]["record_id"]
    print(f"  Record ID: {record_id}")
    print(f"  Patient Age: {response['data']['age']}")

    # Add vitals
    print("\n🫀 POST /api/health-records/{id}/vitals (Normal vitals)")
    response = api.add_vitals(
        record_id,
        {
            "heart_rate": 72,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "temperature": 36.6,
            "oxygen_saturation": 98,
        },
    )
    print(f"  Status: {response['status']}")
    print(f"  Vitals Normal: {response['data']['vitals_normal']}")

    # Create another patient with abnormal vitals
    print("\n📋 Creating second patient with abnormal vitals...")
    response2 = api.create_record(
        {
            "patient_name": "Bob Smith",
            "date_of_birth": "1960-11-22",
            "blood_type": "O-",
            "allergies": [],
            "medications": ["Metformin 500mg", "Aspirin 81mg"],
        }
    )
    record_id_2 = response2["data"]["record_id"]

    api.add_vitals(
        record_id_2,
        {
            "heart_rate": 110,  # HIGH!
            "blood_pressure_sys": 160,  # HIGH!
            "blood_pressure_dia": 95,  # HIGH!
            "temperature": 37.8,  # Slightly elevated
            "oxygen_saturation": 93,  # LOW!
        },
    )

    # Get alerts
    print("\n🚨 GET /api/health-records/alerts")
    alerts = api.get_alerts()
    print(f"  Alert Count: {alerts['alert_count']}")
    for alert in alerts["data"]:
        print(f"    ⚠️  {alert['patient_name']} - Vitals abnormal!")
        if alert["latest_vitals"]:
            v = alert["latest_vitals"]
            print(
                f"       HR: {v['heart_rate']}, BP: {v['blood_pressure']}, O2: {v['oxygen_saturation']}%"
            )

    # Invalid request demo
    print("\n❌ POST /api/health-records (Invalid data)")
    bad_response = api.create_record(
        {
            "patient_name": "",
            "date_of_birth": "not-a-date",
            "blood_type": "X",
        }
    )
    print(f"  Status: {bad_response['status']}")
    print(f"  Error: {bad_response['error']}")

    # Get all records
    print("\n📊 GET /api/health-records (List all)")
    all_records = api.get_all_records()
    print(f"  Total Records: {all_records['count']}")
    for r in all_records["data"]:
        status = "✅ Normal" if r["vitals_normal"] else "⚠️ Abnormal"
        print(f"    {r['patient_name']} (age {r['age']}) - {status}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
