"""
PROJECT 3: HOSPITAL MANAGEMENT - main.py demo
"""

from datetime import datetime, timedelta
from services.hospital_service import HospitalService


def main() -> None:
    """Perform the main step used by this project."""
    print("=" * 60)
    print("     HOSPITAL MANAGEMENT - Composition Demo")
    print("=" * 60)

    hospital = HospitalService("City General Hospital")

    # Create departments
    print("\n🏥 Creating departments...")
    hospital.add_department("Cardiology", floor=2)
    hospital.add_department("Neurology", floor=3)
    hospital.add_department("Orthopedics", floor=1)

    # Hire doctors (composed into departments)
    print("👨‍⚕️ Hiring doctors...")
    dr_heart = hospital.hire_doctor("D001", "Sarah Heart", "Cardiologist", "Cardiology")
    dr_brain = hospital.hire_doctor("D002", "Mike Neuro", "Neurologist", "Neurology")
    dr_bone = hospital.hire_doctor("D003", "Lisa Bone", "Orthopedist", "Orthopedics")

    # Register patients
    print("🧑‍🤝‍🧑 Registering patients...")
    p1 = hospital.register_patient("P001", "John Doe", 45, "Chest pain")
    p2 = hospital.register_patient("P002", "Jane Smith", 32, "Headaches")
    p3 = hospital.register_patient("P003", "Bob Wilson", 58, "Knee pain")

    # Book appointments (COMPOSITION connects Doctor + Patient + Time)
    print("📅 Booking appointments...")
    tomorrow = datetime.now() + timedelta(days=1)

    apt1 = hospital.book_appointment("A001", "P001", "D001", tomorrow, "Heart checkup")
    apt2 = hospital.book_appointment(
        "A002", "P002", "D002", tomorrow + timedelta(hours=2), "Migraine evaluation"
    )
    apt3 = hospital.book_appointment(
        "A003", "P003", "D003", tomorrow + timedelta(hours=4), "Knee examination"
    )

    print(f"\n  {apt1}")
    print(f"  {apt2}")
    print(f"  {apt3}")

    # Complete an appointment (updates patient history through composition)
    print("\n✅ Completing appointment A001...")
    hospital.complete_appointment("D001", "A001", "ECG normal. Recommend stress test.")

    # Show patient history (updated through composition chain)
    print(f"\n📋 {p1.name}'s Medical History:")
    for entry in p1.get_medical_history():
        print(f"    {entry}")

    # Hospital stats
    print("\n📊 Hospital Statistics:")
    stats = hospital.get_hospital_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # Show composition relationships
    print("\n🔗 Composition Relationships:")
    print(f"    Hospital → {stats['departments']} Departments")
    cardiology = hospital.get_department("Cardiology")
    print(f"    Cardiology → {len(cardiology.get_doctors())} Doctors")
    print(f"    Dr. Heart → {len(dr_heart.get_appointments())} Appointments")
    print(f"    Dr. Heart → {dr_heart.get_patient_count()} Patients")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
