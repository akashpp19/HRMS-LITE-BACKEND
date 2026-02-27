from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Literal, Optional
import re


# ─── Employee Schemas ──────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50, examples=["EMP001"])
    full_name: str = Field(..., min_length=2, max_length=200, examples=["Jane Doe"])
    email: EmailStr
    department: str = Field(..., min_length=1, max_length=100, examples=["Engineering"])
    position: Optional[str] = Field(None, max_length=100, examples=["Software Engineer"])
    phone: Optional[str] = Field(None, max_length=30, examples=["+1-555-0100"])

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Employee ID cannot be blank")
        return v.upper()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not re.match(r"^[+\d\s\-().]{7,20}$", v):
            raise ValueError("Invalid phone number format")
        return v if v else None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)


class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: str
    department: str
    position: Optional[str]
    phone: Optional[str]
    created_at: datetime
    total_present_days: Optional[int] = 0

    model_config = {"from_attributes": True}


# ─── Attendance Schemas ────────────────────────────────────────────────────────

AttendanceStatus = Literal["Present", "Absent", "Late", "Half Day"]


class AttendanceCreate(BaseModel):
    employee_id: int = Field(..., gt=0)
    date: date
    status: AttendanceStatus
    note: Optional[str] = Field(None, max_length=300)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        from datetime import date as date_type, timedelta
        # Allow up to 1 day ahead of UTC to accommodate clients in timezones
        # east of UTC (e.g. UTC+5 users marking today's local date at night).
        max_allowed = date_type.today() + timedelta(days=1)
        if v > max_allowed:
            raise ValueError("Cannot mark attendance for a future date")
        return v


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus
    note: Optional[str] = Field(None, max_length=300)


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    status: str
    note: Optional[str]
    created_at: datetime
    employee_name: str
    employee_code: str

    model_config = {"from_attributes": True}


# ─── Dashboard Schema ──────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_employees: int
    total_departments: int
    present_today: int
    absent_today: int
    late_today: int
    attendance_rate_today: float
    attendance_this_week: int
    recent_employees: list[EmployeeResponse]
