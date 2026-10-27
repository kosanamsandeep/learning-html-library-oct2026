"""
=============================================================================
PROJECT 3: HOSPITAL MANAGEMENT SYSTEM
=============================================================================
FILE: models/doctor.py
PURPOSE: Doctor - COMPOSED WITH multiple Appointments and Patients

WHAT YOU LEARN HERE:
- ONE-TO-MANY composition: Doctor HAS MANY Appointments
- The Doctor doesn't OWN patients - it has REFERENCES to them
- Composition creates flexible, replaceable relationships

WHY COMPOSITION BEATS INHERITANCE HERE:
- A Doctor is NOT a special kind of Patient (no IS-A)
- A Doctor HAS appointments, HAS a specialty, HAS a schedule
- These are all separate concerns COMPOSED together
- If requirements change, we can add/remove components without breaking the class hierarchy
=============================================================================
"""

from datetime import datetime
from .patient import Patient
from .appointment import Appointment


class Doctor:
    """
    Represents a doctor in the hospital.

    COMPOSITION EXAMPLES:
    1. Doctor HAS-A list of Appointments (one-to-many)
    2. Doctor HAS-A specialty (simple attribute)
    3. Doctor HAS-A schedule (could be its own class later!)

    FLEXIBILITY OF COMPOSITION:
    - Want to add a "Schedule" object? Just add it as an attribute
    - Want to add "Department"? Compose it in
    - No deep inheritance hierarchies to navigate!
    """

    def __init__(self, doctor_id: str, name: str, specialty: str) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.doctor_id: str = doctor_id
        self.name: str = name
        self.specialty: str = specialty

        # COMPOSITION: Doctor HAS many appointments
        self._appointments: list[Appointment] = []

        # COMPOSITION: Doctor knows which patients they see
        self._patients: dict[str, Patient] = {}

    def schedule_appointment(
        self,
        appointment_id: str,
        patient: Patient,
        scheduled_time: datetime,
        reason: str = "",
    ) -> Appointment:
        """
        Schedule a new appointment.

        COMPOSITION IN ACTION:
        - Creates an Appointment (which HAS-A Patient)
        - Adds it to Doctor's list (Doctor HAS-MANY Appointments)
        - Tracks the patient reference

        This creates a GRAPH of relationships:
        Doctor → Appointment → Patient
        Doctor → Patient (direct reference too)
        """
        # Create the appointment (it contains the patient reference)
        appointment = Appointment(
            appointment_id=appointment_id,
            patient=patient,
            doctor_name=self.name,
            scheduled_time=scheduled_time,
            reason=reason,
        )

        # Add to doctor's appointment list
        self._appointments.append(appointment)

        # Track patient (if new)
        if patient.patient_id not in self._patients:
            self._patients[patient.patient_id] = patient

        return appointment

    def get_appointments(self, status: str | None = None) -> list[Appointment]:
        """Get appointments, optionally filtered by status."""
        if status is None:
            return self._appointments.copy()
        return [apt for apt in self._appointments if apt.status == status]

    def get_patients(self) -> list[Patient]:
        """Get all patients this doctor sees."""
        return list(self._patients.values())

    def get_patient_count(self) -> int:
        """How many unique patients does this doctor have?"""
        return len(self._patients)

    def get_todays_appointments(self) -> list[Appointment]:
        """Get appointments scheduled for today."""
        today = datetime.now().date()
        return [
            apt
            for apt in self._appointments
            if apt.scheduled_time.date() == today and apt.status == "SCHEDULED"
        ]

    def __str__(self) -> str:
        """Perform the str step used by this project."""
        return (
            f"Dr. {self.name} ({self.specialty}) - "
            f"{len(self._appointments)} appointments, "
            f"{self.get_patient_count()} patients"
        )
