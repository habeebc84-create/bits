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
# Dev: the app is often opened via localhost OR a LAN IP, and the backend never
# uses credentials/cookies — so permit any origin. Prod: pin to FRONTEND_ORIGIN.
_app_origins = ["*"] if not settings.is_prod else [settings.FRONTEND_ORIGIN]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_app_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
