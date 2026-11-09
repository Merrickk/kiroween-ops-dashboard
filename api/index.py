"""Vercel serverless entry point.

Vercel's Python runtime serves the module-level ASGI ``app`` from this file
natively. The real application lives in the repo root (app.py); it is bundled
next to this function via ``includeFiles`` in vercel.json, so we add the root
to the import path instead of duplicating any logic.

Do NOT export a Mangum ``handler`` here: when both ``app`` and ``handler``
exist, the runtime invokes Mangum with the rewritten path ("/api/index") for
every request, so FastAPI 404s on all routes. Exporting only ``app`` makes
the runtime pass the original request path through.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402
