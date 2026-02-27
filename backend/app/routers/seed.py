"""
Seed router — populates the database with demo employee + attendance data.
  POST   /api/seed  — seed (skips existing)
  DELETE /api/seed  — wipe all data and re-seed
Protected by X-Seed-Secret header (default: "hrms-seed"; set SEED_SECRET env var to change).
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date, timedelta
import os
from .. import models
from ..database import get_db

router = APIRouter(prefix="/api", tags=["Seed"])

SEED_SECRET = os.getenv("SEED_SECRET", "hrms-seed")

SEED_EMPLOYEES = [
    {"employee_id": "EMP001", "full_name": "Emma Thompson",  "email": "emma.thompson@company.com",  "department": "Engineering", "position": "Python Developer",   "phone": "+1 555-0101"},
    {"employee_id": "EMP002", "full_name": "James Wilson",   "email": "james.wilson@company.com",   "department": "Engineering", "position": "Frontend Developer", "phone": "+1 555-0102"},
    {"employee_id": "EMP003", "full_name": "Sarah Mitchell", "email": "sarah.mitchell@company.com", "department": "Design",      "position": "UI/UX Designer",     "phone": "+1 555-0103"},
    {"employee_id": "EMP004", "full_name": "Daniel Carter",  "email": "daniel.carter@company.com",  "department": "Marketing",   "position": "Marketing Manager",  "phone": "+1 555-0104"},
    {"employee_id": "EMP005", "full_name": "Olivia Bennett", "email": "olivia.bennett@company.com", "department": "HR",          "position": "HR Specialist",      "phone": "+1 555-0105"},
]

ATTENDANCE_SCHEDULE = [
    # (employee_id_code, days_ago, status, note)
    ("EMP001", 0, "Present",  ""),
    ("EMP002", 0, "Late",     "Overslept"),
    ("EMP003", 0, "Present",  ""),
    ("EMP005", 0, "Present",  ""),
    ("EMP001", 1, "Present",  ""),
    ("EMP002", 1, "Present",  ""),
    ("EMP003", 1, "Absent",   "Sick leave"),
    ("EMP004", 1, "Late",     "Traffic delay"),
    ("EMP005", 1, "Present",  ""),
    ("EMP001", 2, "Present",  ""),
    ("EMP002", 2, "Present",  ""),
    ("EMP003", 2, "Present",  ""),
    ("EMP004", 2, "Present",  ""),
    ("EMP005", 2, "Half Day", "Left early"),
]


def _check_secret(x_seed_secret: str = Header(default="")):
    if x_seed_secret != SEED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Seed-Secret header.")


def _do_seed(db: Session):
    today = date.today()
    # --- Employees ---
    emp_map = {}
    created_emps = 0
    for ep in SEED_EMPLOYEES:
        existing = db.query(models.Employee).filter(models.Employee.employee_id == ep["employee_id"]).first()
        if existing:
            emp_map[ep["employee_id"]] = existing
        else:
            emp = models.Employee(**ep)
            db.add(emp)
            db.flush()
            emp_map[ep["employee_id"]] = emp
            created_emps += 1
    db.commit()
    for emp in emp_map.values():
        db.refresh(emp)

    # --- Attendance ---
    created_att = 0
    for emp_code, days_ago, status, note in ATTENDANCE_SCHEDULE:
        emp = emp_map.get(emp_code)
        if not emp:
            continue
        rec_date = today - timedelta(days=days_ago)
        existing_att = (
            db.query(models.Attendance)
            .filter(models.Attendance.employee_id == emp.id, models.Attendance.date == rec_date)
            .first()
        )
        if not existing_att:
            rec = models.Attendance(employee_id=emp.id, date=rec_date, status=status, note=note or None)
            db.add(rec)
            created_att += 1
    db.commit()
    return created_emps, created_att


@router.post("/seed", dependencies=[Depends(_check_secret)])
def seed_database(db: Session = Depends(get_db)):
    """Populate the DB with demo employees + attendance (skips existing records)."""
    created_emps, created_att = _do_seed(db)
    return {
        "ok": True,
        "employees_created": created_emps,
        "attendance_created": created_att,
        "message": "Database seeded successfully.",
    }


@router.delete("/seed", dependencies=[Depends(_check_secret)])
def clear_and_reseed(db: Session = Depends(get_db)):
    """Wipe all attendance + employees then re-seed from scratch."""
    db.query(models.Attendance).delete()
    db.query(models.Employee).delete()
    db.commit()
    created_emps, created_att = _do_seed(db)
    return {
        "ok": True,
        "employees_created": created_emps,
        "attendance_created": created_att,
        "message": "Database cleared and re-seeded.",
    }
