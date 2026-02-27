from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from .. import models, schemas
from ..database import get_db
from .employees import _to_response as emp_to_response

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    total_employees = db.query(func.count(models.Employee.id)).scalar() or 0
    total_departments = (
        db.query(func.count(func.distinct(models.Employee.department))).scalar() or 0
    )

    today_records = (
        db.query(models.Attendance).filter(models.Attendance.date == today).all()
    )
    present_today = sum(1 for r in today_records if r.status in ("Present", "Late", "Half Day"))
    absent_today = sum(1 for r in today_records if r.status == "Absent")
    late_today = sum(1 for r in today_records if r.status == "Late")

    attendance_rate_today = (
        round(present_today / total_employees * 100, 1) if total_employees > 0 else 0.0
    )

    attendance_this_week = (
        db.query(func.count(models.Attendance.id))
        .filter(models.Attendance.date >= week_start, models.Attendance.date <= today)
        .scalar()
        or 0
    )

    recent_employees = (
        db.query(models.Employee).order_by(models.Employee.created_at.desc()).limit(5).all()
    )

    return schemas.DashboardStats(
        total_employees=total_employees,
        total_departments=total_departments,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        attendance_rate_today=attendance_rate_today,
        attendance_this_week=attendance_this_week,
        recent_employees=[emp_to_response(e, db) for e in recent_employees],
    )
