"""SIGNAL HUNTER X — FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import get_settings
from .db import init_db
from .logging_setup import setup_logging

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
init_db()

app = FastAPI(title="SIGNAL HUNTER X", version="1.0.0",
              description="Autonomous Financial Intelligence & Hidden Signal Discovery")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
