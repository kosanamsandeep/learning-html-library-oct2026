"""
=============================================================================
PROJECT 3: HOSPITAL MANAGEMENT SYSTEM
=============================================================================
FILE: services/hospital_service.py
PURPOSE: Orchestrates hospital operations using composed objects
=============================================================================
"""

from datetime import datetime
from models.patient import Patient
from models.doctor import Doctor
from models.department import Department
from models.appointment import Appointment


class HospitalService:
    """
    Top-level service managing the hospital.

    COMPOSITION AT SCALE:
    Hospital HAS Departments HAS Doctors HAS Appointments HAS Patients

    Each level is independently testable and modifiable!
    """

    def __init__(self, hospital_name: str) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.hospital_name: str = hospital_name
        self._departments: dict[str, Department] = {}
        self._patients: dict[str, Patient] = {}  # All patients registry
        self._doctors: dict[str, Doctor] = {}  # All doctors registry

    def add_department(self, name: str, floor: int) -> Department:
        """Create and add a department."""
        dept = Department(name=name, floor=floor)
        self._departments[name] = dept
        return dept

    def register_patient(
        self, patient_id: str, name: str, age: int, condition: str = ""
    ) -> Patient:
        """Register a new patient."""
        if patient_id in self._patients:
            raise ValueError(f"Patient {patient_id} already registered")
        patient = Patient(patient_id, name, age, condition)
        self._patients[patient_id] = patient
        return patient

    def hire_doctor(
        self, doctor_id: str, name: str, specialty: str, department_name: str
    ) -> Doctor:
        """Hire a doctor and assign to department."""
        if department_name not in self._departments:
            raise ValueError(f"Department '{department_name}' not found")

        doctor = Doctor(doctor_id, name, specialty)
        self._doctors[doctor_id] = doctor
        self._departments[department_name].add_doctor(doctor)
        return doctor

    def book_appointment(
        self,
        appointment_id: str,
        patient_id: str,
        doctor_id: str,
        scheduled_time: datetime,
        reason: str = "",
    ) -> Appointment:
        """
        Book an appointment - this shows composition connecting objects.

        The appointment COMPOSES a patient and doctor together
        without either needing to know about the other's internals.
        """
        patient = self._patients.get(patient_id)
        if patient is None:
            raise ValueError(f"Patient {patient_id} not found")

        doctor = self._doctors.get(doctor_id)
        if doctor is None:
            raise ValueError(f"Doctor {doctor_id} not found")

        return doctor.schedule_appointment(
            appointment_id, patient, scheduled_time, reason
        )

    def complete_appointment(
        self, doctor_id: str, appointment_id: str, notes: str
    ) -> bool:
        """Complete an appointment and update patient history."""
        doctor = self._doctors.get(doctor_id)
        if doctor is None:
            return False

        for apt in doctor.get_appointments(status="SCHEDULED"):
            if apt.appointment_id == appointment_id:
                apt.complete(notes)
                return True
        return False

    def get_patient(self, patient_id: str) -> Patient | None:
        """Return the requested item or information if it exists."""
        return self._patients.get(patient_id)

    def get_doctor(self, doctor_id: str) -> Doctor | None:
        """Return the requested item or information if it exists."""
        return self._doctors.get(doctor_id)

    def get_department(self, name: str) -> Department | None:
        """Return the requested item or information if it exists."""
        return self._departments.get(name)

    def get_hospital_stats(self) -> dict:
        """Get hospital-wide statistics."""
        return {
            "departments": len(self._departments),
            "doctors": len(self._doctors),
            "patients": len(self._patients),
            "hospital": self.hospital_name,
        }
