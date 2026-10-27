"""
=============================================================================
PROJECT 7: HEALTHTRACK
=============================================================================
FILE: api/health_api.py
PURPOSE: API layer - the "front door" of the system

THIS IS THE TOP LAYER:
- Receives raw requests (simulated as method calls here)
- Creates DTOs from raw data
- Calls service layer
- Formats responses

IN REAL WORLD: This would be Flask/FastAPI route handlers.
Here we simulate it to focus on architecture.
=============================================================================
"""

from dtos.health_dtos import CreateHealthRecordDTO, AddVitalsDTO
from services.health_service import HealthService


class HealthAPI:
    """
    API layer - simulates HTTP endpoint handlers.

    LAYER RESPONSIBILITIES:
    - Parse raw input (in real app: JSON from HTTP request)
    - Create DTO from parsed input
    - Call service method
    - Handle errors (return proper error codes)
    - Return formatted response (in real app: JSON HTTP response)

    WHAT THIS LAYER DOES NOT DO:
    - Business logic (that's service)
    - Data access (that's repository)
    - Validation logic (that's DTO)
    """

    def __init__(self, service: HealthService) -> None:
        """Initialize the object with the dependencies or starting values it needs."""
        self._service = service

    def create_record(self, request_data: dict) -> dict:
        """
        POST /api/health-records

        Simulates an HTTP POST endpoint.
        """
        try:
            # Step 1: Create DTO from raw request data
            dto = CreateHealthRecordDTO(
                patient_name=request_data.get("patient_name", ""),
                date_of_birth=request_data.get("date_of_birth", ""),
                blood_type=request_data.get("blood_type", ""),
                allergies=request_data.get("allergies", []),
                medications=request_data.get("medications", []),
            )

            # Step 2: Call service (validates + creates + returns)
            response_dto = self._service.create_record(dto)

            # Step 3: Return success response
            return {"status": 201, "data": response_dto.to_dict()}

        except ValueError as e:
            return {"status": 400, "error": str(e)}

    def add_vitals(self, record_id: str, request_data: dict) -> dict:
        """POST /api/health-records/{id}/vitals"""
        try:
            dto = AddVitalsDTO(
                heart_rate=request_data.get("heart_rate", 0),
                blood_pressure_sys=request_data.get("blood_pressure_sys", 0),
                blood_pressure_dia=request_data.get("blood_pressure_dia", 0),
                temperature=request_data.get("temperature", 0.0),
                oxygen_saturation=request_data.get("oxygen_saturation", 0),
            )

            response_dto = self._service.add_vitals(record_id, dto)
            return {"status": 200, "data": response_dto.to_dict()}

        except ValueError as e:
            return {"status": 400, "error": str(e)}

    def get_record(self, record_id: str) -> dict:
        """GET /api/health-records/{id}"""
        response_dto = self._service.get_record(record_id)
        if response_dto is None:
            return {"status": 404, "error": "Record not found"}
        return {"status": 200, "data": response_dto.to_dict()}

    def get_all_records(self) -> dict:
        """GET /api/health-records"""
        records = self._service.get_all_records()
        return {
            "status": 200,
            "data": [r.to_dict() for r in records],
            "count": len(records),
        }

    def get_alerts(self) -> dict:
        """GET /api/health-records/alerts"""
        abnormal = self._service.get_abnormal_vitals()
        return {
            "status": 200,
            "data": [r.to_dict() for r in abnormal],
            "alert_count": len(abnormal),
        }
