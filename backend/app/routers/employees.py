from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _to_response(emp: models.Employee, db: Session) -> schemas.EmployeeResponse:
    present_days = (
        db.query(func.count(models.Attendance.id))
        .filter(
            models.Attendance.employee_id == emp.id,
            models.Attendance.status == "Present",
        )
        .scalar()
        or 0
    )
    return schemas.EmployeeResponse(
        id=emp.id,
        employee_id=emp.employee_id,
        full_name=emp.full_name,
        email=emp.email,
        department=emp.department,
        position=emp.position,
        phone=emp.phone,
        created_at=emp.created_at,
        total_present_days=present_days,
    )


@router.get("", response_model=list[schemas.EmployeeResponse])
def list_employees(
    search: Optional[str] = Query(None, description="Search by name, email, or ID"),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Employee)
    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            models.Employee.full_name.ilike(term)
            | models.Employee.email.ilike(term)
            | models.Employee.employee_id.ilike(term)
        )
    if department:
        query = query.filter(models.Employee.department == department)
    employees = query.order_by(models.Employee.created_at.desc()).all()
    return [_to_response(emp, db) for emp in employees]


@router.post("", response_model=schemas.EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    # Check duplicate employee_id
    if db.query(models.Employee).filter(models.Employee.employee_id == payload.employee_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with ID '{payload.employee_id}' already exists.",
        )
    # Check duplicate email
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with email '{payload.email}' already exists.",
        )

    emp = models.Employee(**payload.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return _to_response(emp, db)


@router.get("/departments", response_model=list[str])
def get_departments(db: Session = Depends(get_db)):
    rows = db.query(models.Employee.department).distinct().order_by(models.Employee.department).all()
    return [r[0] for r in rows]


@router.get("/{employee_id}", response_model=schemas.EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return _to_response(emp, db)


@router.put("/{employee_id}", response_model=schemas.EmployeeResponse)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != emp.email:
        if db.query(models.Employee).filter(models.Employee.email == update_data["email"]).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{update_data['email']}' is already in use.",
            )

    for key, value in update_data.items():
        setattr(emp, key, value)

    db.commit()
    db.refresh(emp)
    return _to_response(emp, db)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    db.delete(emp)
    db.commit()
