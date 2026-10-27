"""
=============================================================================
PROJECT 7: HEALTHTRACK - FULL LAYERED ARCHITECTURE
=============================================================================
FILE: models/health_record.py
PURPOSE: Domain models for health tracking

This project COMBINES everything from Projects 1-6 into one layered system:
- Models (P1-3), DTOs (P4), Schemas (P5), Repositories (P6)
- Plus a proper API layer that ties it all together
=============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, date


@dataclass
class VitalSigns:
    """Value object for vital signs measurement."""

    heart_rate: int  # BPM
    blood_pressure_sys: int  # Systolic (top number)
    blood_pressure_dia: int  # Diastolic (bottom number)
    temperature: float  # Celsius
    oxygen_saturation: int  # Percentage
    measured_at: datetime = field(default_factory=datetime.now)

    @property
    def blood_pressure(self) -> str:
        """Perform the blood pressure step used by this project."""
        return f"{self.blood_pressure_sys}/{self.blood_pressure_dia}"

    def is_normal(self) -> bool:
        """Check if all vitals are in normal range."""
        return (
            60 <= self.heart_rate <= 100
            and 90 <= self.blood_pressure_sys <= 140
            and 60 <= self.blood_pressure_dia <= 90
            and 36.1 <= self.temperature <= 37.2
            and 95 <= self.oxygen_saturation <= 100
        )


@dataclass
class HealthRecord:
    """Main health record for a patient."""

    record_id: str
    patient_id: str
    patient_name: str
    date_of_birth: date
    blood_type: str
    allergies: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    vitals_history: list[VitalSigns] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def age(self) -> int:
        """Perform the age step used by this project."""
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    @property
    def latest_vitals(self) -> VitalSigns | None:
        """Perform the latest vitals step used by this project."""
        return self.vitals_history[-1] if self.vitals_history else None

    def add_vitals(self, vitals: VitalSigns) -> None:
        """Add a new item to the in-memory collection, repository, or workflow."""
        self.vitals_history.append(vitals)
        self.updated_at = datetime.now()

    def add_note(self, note: str) -> None:
        """Add a new item to the in-memory collection, repository, or workflow."""
        self.notes.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}")
        self.updated_at = datetime.now()
