from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


def _to_response(att: models.Attendance) -> schemas.AttendanceResponse:
    return schemas.AttendanceResponse(
        id=att.id,
        employee_id=att.employee_id,
        date=att.date,
        status=att.status,
        note=att.note,
        created_at=att.created_at,
        employee_name=att.employee.full_name,
        employee_code=att.employee.employee_id,
    )


@router.get("", response_model=list[schemas.AttendanceResponse])
def list_attendance(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Attendance).join(models.Attendance.employee)
    if date_from:
        query = query.filter(models.Attendance.date >= date_from)
    if date_to:
        query = query.filter(models.Attendance.date <= date_to)
    if employee_id:
        query = query.filter(models.Attendance.employee_id == employee_id)
    if status:
        query = query.filter(models.Attendance.status == status)
    records = query.order_by(models.Attendance.date.desc(), models.Attendance.id.desc()).all()
    return [_to_response(r) for r in records]


@router.post("", response_model=schemas.AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(payload: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    existing = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.employee_id == payload.employee_id,
            models.Attendance.date == payload.date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attendance for {emp.full_name} on {payload.date} is already recorded.",
        )

    record = models.Attendance(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    # Re-fetch with joined employee
    record = db.query(models.Attendance).filter(models.Attendance.id == record.id).first()
    return _to_response(record)


@router.put("/{attendance_id}", response_model=schemas.AttendanceResponse)
def update_attendance(attendance_id: int, payload: schemas.AttendanceUpdate, db: Session = Depends(get_db)):
    record = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    record.status = payload.status
    record.note = payload.note
    db.commit()
    db.refresh(record)
    record = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    return _to_response(record)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    record = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    db.delete(record)
    db.commit()


@router.get("/employee/{employee_id}", response_model=list[schemas.AttendanceResponse])
def get_employee_attendance(
    employee_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    query = db.query(models.Attendance).filter(models.Attendance.employee_id == employee_id)
    if date_from:
        query = query.filter(models.Attendance.date >= date_from)
    if date_to:
        query = query.filter(models.Attendance.date <= date_to)
    records = query.order_by(models.Attendance.date.desc()).all()
    return [_to_response(r) for r in records]
