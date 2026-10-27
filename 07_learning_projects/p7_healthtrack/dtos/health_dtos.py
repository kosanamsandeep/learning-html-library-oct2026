"""
=============================================================================
PROJECT 7: HEALTHTRACK
=============================================================================
FILE: dtos/health_dtos.py
PURPOSE: DTOs for the API layer - validates input, formats output
=============================================================================
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class CreateHealthRecordDTO:
    """Input DTO: What the API receives to create a health record."""

    patient_name: str
    date_of_birth: str  # ISO format: "1990-01-15"
    blood_type: str
    allergies: list[str]
    medications: list[str]

    def validate(self) -> list[str]:
        """Perform the validate step used by this project."""
        errors: list[str] = []
        if not self.patient_name.strip():
            errors.append("patient_name is required")
        try:
            date.fromisoformat(self.date_of_birth)
        except (ValueError, TypeError):
            errors.append("date_of_birth must be ISO format (YYYY-MM-DD)")
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        if self.blood_type not in valid_blood_types:
            errors.append(f"blood_type must be one of {valid_blood_types}")
        return errors


@dataclass
class AddVitalsDTO:
    """Input DTO: Vital signs measurement."""

    heart_rate: int
    blood_pressure_sys: int
    blood_pressure_dia: int
    temperature: float
    oxygen_saturation: int

    def validate(self) -> list[str]:
        """Perform the validate step used by this project."""
        errors: list[str] = []
        if not 20 <= self.heart_rate <= 250:
            errors.append("heart_rate must be 20-250 BPM")
        if not 50 <= self.blood_pressure_sys <= 250:
            errors.append("blood_pressure_sys must be 50-250")
        if not 30 <= self.blood_pressure_dia <= 150:
            errors.append("blood_pressure_dia must be 30-150")
        if not 30.0 <= self.temperature <= 45.0:
            errors.append("temperature must be 30-45°C")
        if not 50 <= self.oxygen_saturation <= 100:
            errors.append("oxygen_saturation must be 50-100%")
        return errors


@dataclass
class HealthRecordResponseDTO:
    """Output DTO: What the API returns (safe, formatted data)."""

    record_id: str
    patient_id: str
    patient_name: str
    age: int
    blood_type: str
    allergies: list[str]
    medications: list[str]
    latest_vitals: dict | None
    vitals_normal: bool | None
    notes_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, record: Any) -> "HealthRecordResponseDTO":
        """Create an object from another representation."""
        latest = record.latest_vitals
        return cls(
            record_id=record.record_id,
            patient_id=record.patient_id,
            patient_name=record.patient_name,
            age=record.age,
            blood_type=record.blood_type,
            allergies=record.allergies,
            medications=record.medications,
            latest_vitals=(
                {
                    "heart_rate": latest.heart_rate,
                    "blood_pressure": latest.blood_pressure,
                    "temperature": latest.temperature,
                    "oxygen_saturation": latest.oxygen_saturation,
                    "measured_at": latest.measured_at.isoformat(),
                }
                if latest
                else None
            ),
            vitals_normal=latest.is_normal() if latest else None,
            notes_count=len(record.notes),
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )

    def to_dict(self) -> dict:
        """Convert this object into another representation."""
        return {
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "age": self.age,
            "blood_type": self.blood_type,
            "allergies": self.allergies,
            "medications": self.medications,
            "latest_vitals": self.latest_vitals,
            "vitals_normal": self.vitals_normal,
            "notes_count": self.notes_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
