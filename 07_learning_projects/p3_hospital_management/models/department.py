"""
=============================================================================
PROJECT 3: HOSPITAL MANAGEMENT SYSTEM
=============================================================================
FILE: models/department.py
PURPOSE: Department - shows MULTI-LEVEL composition

Doctor HAS Appointments, Department HAS Doctors
This shows how composition scales to complex systems.
=============================================================================
"""

from .doctor import Doctor


class Department:
    """
    Hospital department containing multiple doctors.

    MULTI-LEVEL COMPOSITION:
    Department HAS Doctors
        Doctor HAS Appointments
            Appointment HAS Patient

    This is a tree/graph of composed objects.
    Each level is independent and reusable!
    """

    def __init__(self, name: str, floor: int) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.name: str = name
        self.floor: int = floor
        self._doctors: dict[str, Doctor] = {}

    def add_doctor(self, doctor: Doctor) -> None:
        """Add a doctor to this department."""
        self._doctors[doctor.doctor_id] = doctor

    def remove_doctor(self, doctor_id: str) -> bool:
        """Remove a doctor from the department."""
        if doctor_id in self._doctors:
            del self._doctors[doctor_id]
            return True
        return False

    def get_doctors(self) -> list[Doctor]:
        """Get all doctors in this department."""
        return list(self._doctors.values())

    def get_doctor(self, doctor_id: str) -> Doctor | None:
        """Find a specific doctor."""
        return self._doctors.get(doctor_id)

    def get_total_patients(self) -> int:
        """Count total unique patients across all doctors."""
        all_patient_ids = set()
        for doctor in self._doctors.values():
            for patient in doctor.get_patients():
                all_patient_ids.add(patient.patient_id)
        return len(all_patient_ids)

    def __str__(self) -> str:
        """Perform the str step used by this project."""
        return (
            f"Department({self.name}, Floor {self.floor}, "
            f"{len(self._doctors)} doctors)"
        )
