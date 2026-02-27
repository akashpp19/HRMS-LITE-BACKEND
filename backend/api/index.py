"""
Vercel serverless entry point for the HRMS FastAPI backend.
Vercel Python runtime discovers the `app` ASGI object in this file.
"""
import sys
import os

# Ensure the project root is on the path so `app` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app  # noqa: F401  — Vercel needs `app` at module level
