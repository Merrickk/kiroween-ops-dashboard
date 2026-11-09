"""Vercel serverless entry point.

Vercel's Python runtime serves the module-level ASGI ``app`` from this file.
The real application lives in the repo root (app.py); it is bundled next to
this function via ``includeFiles`` in vercel.json, so we add the root to the
import path instead of duplicating any logic. ``handler`` (Mangum) is
exported as well for runtimes that prefer it; lifespan is off because
serverless functions cannot run the background scheduler thread.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402
from mangum import Mangum  # noqa: E402

handler = Mangum(app, lifespan="off")
