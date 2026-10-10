"""Structured logging (single line JSON-ish, stdlib only)."""
from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("signalhunter")
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        '{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}'
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger
