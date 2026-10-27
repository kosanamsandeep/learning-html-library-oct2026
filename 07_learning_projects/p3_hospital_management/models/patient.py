"""
=============================================================================
PROJECT 3: HOSPITAL MANAGEMENT SYSTEM
=============================================================================
FILE: models/patient.py
PURPOSE: Patient domain object - a simple data holder

WHAT YOU LEARN HERE:
- Objects that represent real-world entities
- This is a COMPONENT that will be COMPOSED into other objects
- Patient doesn't know about Doctor or Appointment
- Each object is independent and reusable
=============================================================================
"""


class Patient:
    """
    Represents a patient in the hospital.

    DESIGN NOTE:
    - Patient is a standalone object
    - It doesn't inherit from anything (no IS-A)
    - It will be USED BY other objects (HAS-A)
    - A Doctor HAS patients, an Appointment HAS a patient
    """

    def __init__(
        self, patient_id: str, name: str, age: int, condition: str = ""
    ) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self.patient_id: str = patient_id
        self.name: str = name
        self.age: int = age
        self.condition: str = condition  # Current medical condition
        self._medical_history: list[str] = []

    def add_to_history(self, entry: str) -> None:
        """Add a medical history entry."""
        self._medical_history.append(entry)

    def get_medical_history(self) -> list[str]:
        """Get full medical history."""
        return self._medical_history.copy()

    def __str__(self) -> str:
        """Perform the str step used by this project."""
        return f"Patient({self.patient_id}: {self.name}, age={self.age})"
