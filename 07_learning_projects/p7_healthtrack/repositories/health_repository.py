"""
PROJECT 7: HEALTHTRACK - Repository Layer
Abstract interface + in-memory implementation.
"""

from abc import ABC, abstractmethod
from models.health_record import HealthRecord


class BaseHealthRepository(ABC):
    """Abstract repository interface for health records."""

    @abstractmethod
    def save(self, record: HealthRecord) -> HealthRecord:
        """Perform the save step used by this project."""
        pass

    @abstractmethod
    def get_by_id(self, record_id: str) -> HealthRecord | None:
        """Return the requested item or information if it exists."""
        pass

    @abstractmethod
    def get_by_patient_id(self, patient_id: str) -> HealthRecord | None:
        """Return the requested item or information if it exists."""
        pass

    @abstractmethod
    def get_all(self) -> list[HealthRecord]:
        """Return the requested item or information if it exists."""
        pass

    @abstractmethod
    def update(self, record: HealthRecord) -> HealthRecord | None:
        """Perform the update step used by this project."""
        pass

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        """Perform the delete step used by this project."""
        pass


class MemoryHealthRepository(BaseHealthRepository):
    """In-memory implementation for development and testing."""

    def __init__(self) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._records: dict[str, HealthRecord] = {}
        self._patient_index: dict[str, str] = {}  # patient_id → record_id

    def save(self, record: HealthRecord) -> HealthRecord:
        """Perform the save step used by this project."""
        self._records[record.record_id] = record
        self._patient_index[record.patient_id] = record.record_id
        return record

    def get_by_id(self, record_id: str) -> HealthRecord | None:
        """Return the requested item or information if it exists."""
        return self._records.get(record_id)

    def get_by_patient_id(self, patient_id: str) -> HealthRecord | None:
        """Return the requested item or information if it exists."""
        record_id = self._patient_index.get(patient_id)
        if record_id:
            return self._records.get(record_id)
        return None

    def get_all(self) -> list[HealthRecord]:
        """Return the requested item or information if it exists."""
        return list(self._records.values())

    def update(self, record: HealthRecord) -> HealthRecord | None:
        """Perform the update step used by this project."""
        if record.record_id not in self._records:
            return None
        self._records[record.record_id] = record
        return record

    def delete(self, record_id: str) -> bool:
        """Perform the delete step used by this project."""
        record = self._records.get(record_id)
        if record is None:
            return False
        del self._records[record_id]
        del self._patient_index[record.patient_id]
        return True
