"""Pydantic schemas for a digitized prescription."""
from __future__ import annotations
from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Frequency(str, Enum):
    OD = "once_daily"
    BD = "twice_daily"
    TDS = "thrice_daily"
    QID = "four_times_daily"
    PRN = "as_needed"
    STAT = "immediately"


class Route(str, Enum):
    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SC = "subcutaneous"
    TOPICAL = "topical"
    INHALED = "inhaled"


class Medication(BaseModel):
    name: str = Field(..., description="Brand or generic drug name as written")
    rxnorm_cui: Optional[str] = Field(None, description="RxNorm concept ID once validated")
    strength: str = Field(..., description="e.g. 500 mg, 10 ml")
    dose: str = Field(..., description="Per-administration quantity, e.g. 1 tablet")
    frequency: Frequency
    route: Route = Route.ORAL
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class Patient(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=130)
    sex: Optional[str] = None
    weight_kg: Optional[float] = None


class Prescriber(BaseModel):
    name: Optional[str] = None
    registration_no: Optional[str] = None
    clinic: Optional[str] = None


class Prescription(BaseModel):
    issued_on: Optional[date] = None
    patient: Patient = Field(default_factory=Patient)
    prescriber: Prescriber = Field(default_factory=Prescriber)
    diagnosis: Optional[str] = None
    medications: List[Medication]
    follow_up_days: Optional[int] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
