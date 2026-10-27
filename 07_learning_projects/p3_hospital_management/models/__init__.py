"""
PROJECT 3: HOSPITAL MANAGEMENT - models package
"""

from .patient import Patient
from .appointment import Appointment
from .doctor import Doctor
from .department import Department

__all__ = ["Patient", "Appointment", "Doctor", "Department"]
