"""
=============================================================================
PROJECT 3: HOSPITAL MANAGEMENT SYSTEM
=============================================================================
FILE: models/appointment.py
PURPOSE: Appointment - COMPOSED of a Patient and a time slot

WHAT YOU LEARN HERE:
- COMPOSITION: Appointment HAS-A Patient (contains a reference to one)
- An Appointment CANNOT exist without a Patient
- This is a "strong" HAS-A relationship

COMPOSITION vs INHERITANCE:
- Inheritance: "SavingsAccount IS-A Account" (identity)
- Composition: "Appointment HAS-A Patient" (contains)
- Rule of thumb: If you can say "X has a Y" → use composition
=============================================================================
"""

from datetime import datetime
from .patient import Patient


class Appointment:
    """
    Represents a medical appointment.

    COMPOSITION IN ACTION:
    - This class CONTAINS a Patient object (HAS-A)
    - It doesn't inherit from Patient
    - It uses Patient's data but adds appointment-specific info

    WHY NOT INHERIT FROM PATIENT?
    - "Appointment IS-A Patient" makes NO sense
    - "Appointment HAS-A Patient" makes perfect sense
    - Inheritance would give appointment methods like add_to_history()
      which don't belong on an appointment!
    """

    def __init__(
        self,
        appointment_id: str,
        patient: Patient,  # COMPOSITION: contains a Patient
        doctor_name: str,
        scheduled_time: datetime,
        reason: str = "",
    ) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.appointment_id: str = appointment_id
        self.patient: Patient = patient  # HAS-A Patient
        self.doctor_name: str = doctor_name
        self.scheduled_time: datetime = scheduled_time
        self.reason: str = reason
        self.status: str = "SCHEDULED"  # SCHEDULED, COMPLETED, CANCELLED
        self.notes: str = ""

    def complete(self, notes: str = "") -> None:
        """Mark appointment as completed and add notes."""
        self.status = "COMPLETED"
        self.notes = notes
        # Update patient's medical history (composition allows this!)
        self.patient.add_to_history(
            f"[{self.scheduled_time.strftime('%Y-%m-%d')}] "
            f"Dr. {self.doctor_name}: {notes}"
        )

    def cancel(self, reason: str = "") -> None:
        """Cancel the appointment."""
        self.status = "CANCELLED"
        self.notes = f"Cancelled: {reason}"

    def is_upcoming(self) -> bool:
        """Check if appointment is in the future."""
        return self.status == "SCHEDULED" and self.scheduled_time > datetime.now()

    def __str__(self) -> str:
        """Perform the str step used by this project."""
        return (
            f"Appointment({self.appointment_id}: "
            f"{self.patient.name} with Dr. {self.doctor_name} "
            f"on {self.scheduled_time.strftime('%Y-%m-%d %H:%M')} "
            f"[{self.status}])"
        )
