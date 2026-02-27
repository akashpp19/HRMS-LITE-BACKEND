# HRMS Lite — Backend API

FastAPI REST backend for the HRMS Lite application. Handles employee management, attendance tracking, and dashboard statistics. Designed to be deployed on **Render** with a **PostgreSQL** database.

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — async Python web framework
- **SQLAlchemy** — ORM with support for PostgreSQL and SQLite
- **Pydantic v2** — request/response validation
- **Uvicorn** — ASGI server
- **Alembic** — database migrations
- **python-dotenv** — environment variable management

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS, router registration
│   ├── database.py      # SQLAlchemy engine & session setup
│   ├── models.py        # ORM models (Employee, Attendance)
│   ├── schemas.py       # Pydantic request/response schemas
│   └── routers/
│       ├── employees.py  # CRUD for employees
│       ├── attendance.py # CRUD for attendance records
│       ├── dashboard.py  # Aggregated stats
│       └── seed.py       # Demo data seeding
├── api/
│   └── index.py         # Vercel/serverless entry point (unused on Render)
├── requirements.txt
├── runtime.txt
└── .env.example
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |
| **Employees** | | |
| GET | `/api/employees` | List employees (supports `?search=`, `?department=`) |
| POST | `/api/employees` | Create employee |
| GET | `/api/employees/{id}` | Get employee by ID |
| PUT | `/api/employees/{id}` | Update employee |
| DELETE | `/api/employees/{id}` | Delete employee |
| GET | `/api/employees/departments` | List all departments |
| **Attendance** | | |
| GET | `/api/attendance` | List records (supports `?date_from=`, `?date_to=`, `?employee_id=`, `?status=`) |
| POST | `/api/attendance` | Mark attendance |
| PUT | `/api/attendance/{id}` | Update attendance record |
| DELETE | `/api/attendance/{id}` | Delete attendance record |
| **Dashboard** | | |
| GET | `/api/dashboard/stats` | Today's stats, weekly trend, recent activity |
| **Seed** | | |
| POST | `/api/seed` | Populate database with demo data |

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for quick local dev)

### Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL (SQLite works out of the box if you leave it as-is)
```

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

API is now available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

### Seed demo data

```bash
curl -X POST http://localhost:8000/api/seed
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string. Falls back to `sqlite:///./hrms.db` locally. |
| `CORS_ORIGINS` | No | Comma-separated list of allowed frontend origins. Defaults to `*`. |

Example `.env`:
```env
DATABASE_URL=postgresql://user:password@host:5432/hrms
CORS_ORIGINS=https://your-app.vercel.app
```

## Deployment — Render

1. Connect your GitHub repo to Render.
2. Create a new **Web Service** with:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add a **PostgreSQL** database from the Render dashboard and copy the connection string into `DATABASE_URL`.
4. Set `CORS_ORIGINS` to your Vercel frontend URL (e.g. `https://hrms-portal.vercel.app`).

Alternatively, the root [`render.yaml`](../render.yaml) pre-configures all of this automatically.
