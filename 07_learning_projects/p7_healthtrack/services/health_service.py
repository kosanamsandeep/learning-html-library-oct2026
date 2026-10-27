"""
=============================================================================
PROJECT 7: HEALTHTRACK
=============================================================================
FILE: services/health_service.py
PURPOSE: Service layer - orchestrates DTOs, Models, and Repository

THE FULL PIPELINE:
    API Layer (request)
    → DTO (validate input)
    → Service (business logic)
    → Repository (persist)
    → Service (transform)
    → DTO (format output)
    → API Layer (response)
=============================================================================
"""

import uuid
from datetime import date

from models.health_record import HealthRecord, VitalSigns
from dtos.health_dtos import (
    CreateHealthRecordDTO,
    AddVitalsDTO,
    HealthRecordResponseDTO,
)
from repositories.health_repository import BaseHealthRepository


class HealthService:
    """
    Business logic layer.

    SITS BETWEEN: API/DTOs (above) and Repository (below)
    RESPONSIBILITIES:
    - Validate business rules
    - Transform DTOs → Models → DTOs
    - Orchestrate repository operations
    """

    def __init__(self, repository: BaseHealthRepository) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._repo = repository

    def create_record(self, dto: CreateHealthRecordDTO) -> HealthRecordResponseDTO:
        """Create a new health record from validated DTO."""
        errors = dto.validate()
        if errors:
            raise ValueError(f"Validation errors: {errors}")

        record_id = f"HR-{uuid.uuid4().hex[:8].upper()}"
        patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"

        record = HealthRecord(
            record_id=record_id,
            patient_id=patient_id,
            patient_name=dto.patient_name.strip(),
            date_of_birth=date.fromisoformat(dto.date_of_birth),
            blood_type=dto.blood_type,
            allergies=dto.allergies,
            medications=dto.medications,
        )

        saved = self._repo.save(record)
        return HealthRecordResponseDTO.from_model(saved)

    def add_vitals(self, record_id: str, dto: AddVitalsDTO) -> HealthRecordResponseDTO:
        """Add vital signs to an existing record."""
        errors = dto.validate()
        if errors:
            raise ValueError(f"Validation errors: {errors}")

        record = self._repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"Record {record_id} not found")

        vitals = VitalSigns(
            heart_rate=dto.heart_rate,
            blood_pressure_sys=dto.blood_pressure_sys,
            blood_pressure_dia=dto.blood_pressure_dia,
            temperature=dto.temperature,
            oxygen_saturation=dto.oxygen_saturation,
        )

        record.add_vitals(vitals)
        updated = self._repo.update(record)
        return HealthRecordResponseDTO.from_model(updated)

    def get_record(self, record_id: str) -> HealthRecordResponseDTO | None:
        """Return the requested item or information if it exists."""
        record = self._repo.get_by_id(record_id)
        if record is None:
            return None
        return HealthRecordResponseDTO.from_model(record)

    def get_all_records(self) -> list[HealthRecordResponseDTO]:
        """Return the requested item or information if it exists."""
        records = self._repo.get_all()
        return [HealthRecordResponseDTO.from_model(r) for r in records]

    def add_note(self, record_id: str, note: str) -> HealthRecordResponseDTO | None:
        """Add a new item to the in-memory collection, repository, or workflow."""
        record = self._repo.get_by_id(record_id)
        if record is None:
            return None
        record.add_note(note)
        updated = self._repo.update(record)
        return HealthRecordResponseDTO.from_model(updated)

    def get_abnormal_vitals(self) -> list[HealthRecordResponseDTO]:
        """Find all patients with abnormal latest vitals."""
        records = self._repo.get_all()
        abnormal = []
        for record in records:
            if record.latest_vitals and not record.latest_vitals.is_normal():
                abnormal.append(HealthRecordResponseDTO.from_model(record))
        return abnormal
