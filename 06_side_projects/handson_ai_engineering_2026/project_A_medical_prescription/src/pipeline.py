"""End-to-end pipeline: image -> extraction -> RxNorm validation -> persistence."""
from __future__ import annotations
import json
import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from .extractor import PrescriptionExtractor
from .rxnorm import RxNormValidator
from .schemas import Prescription

log = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "prescriptions.db"


def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS prescription (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            issued_on       TEXT,
            patient_name    TEXT,
            prescriber_name TEXT,
            diagnosis       TEXT,
            confidence      REAL,
            raw_json        TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS medication (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL REFERENCES prescription(id),
            name            TEXT NOT NULL,
            rxnorm_cui      TEXT,
            strength        TEXT,
            dose            TEXT,
            frequency       TEXT,
            route           TEXT,
            duration_days   INTEGER
        );
        """
    )
    return conn


def validate_drugs(rx: Prescription, validator: RxNormValidator) -> Prescription:
    for med in rx.medications:
        med.rxnorm_cui = validator.lookup_cui(med.name)
    return rx


def persist(rx: Prescription, conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        """INSERT INTO prescription
           (issued_on,patient_name,prescriber_name,diagnosis,confidence,raw_json)
           VALUES (?,?,?,?,?,?)""",
        (
            rx.issued_on.isoformat() if rx.issued_on else None,
            rx.patient.name,
            rx.prescriber.name,
            rx.diagnosis,
            rx.confidence,
            rx.model_dump_json(),
        ),
    )
    pid = cur.lastrowid
    conn.executemany(
        """INSERT INTO medication
           (prescription_id,name,rxnorm_cui,strength,dose,frequency,route,duration_days)
           VALUES (?,?,?,?,?,?,?,?)""",
        [
            (pid, m.name, m.rxnorm_cui, m.strength, m.dose,
             m.frequency.value, m.route.value, m.duration_days)
            for m in rx.medications
        ],
    )
    conn.commit()
    return pid


def run(image_paths: Iterable[str]) -> None:
    extractor = PrescriptionExtractor()
    validator = RxNormValidator()
    conn = _init_db()
    try:
        for p in image_paths:
            log.info("Processing %s", p)
            rx = extractor.extract(p)
            rx = validate_drugs(rx, validator)
            pid = persist(rx, conn)
            print(json.dumps({"id": pid, **rx.model_dump(mode="json")}, indent=2, default=str))
    finally:
        validator.close()
        conn.close()


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline <image1> [image2 ...]")
        sys.exit(1)
    run(sys.argv[1:])
