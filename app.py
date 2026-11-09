"""Ops dashboard: FastAPI + SQLite + 15-minute health-check scheduler.

Run:  pip install -r requirements.txt && python app.py
Then open http://localhost:8000
"""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import prober
import store

BASE_DIR = Path(__file__).parent
CHECK_INTERVAL_SECONDS = 15 * 60
OFFLINE_AFTER_FAILURES = 2

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_db()
    # No scheduler thread on Vercel: serverless functions cannot run
    # background loops. Checks there run on demand via /api/checks/run.
    if os.environ.get("VERCEL") != "1":
        thread = threading.Thread(target=_scheduler_loop, daemon=True)
        thread.start()
    yield


app = FastAPI(title="ops-dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class HostIn(BaseModel):
    name: str
    address: str
    kind: str = "server"


class DeployIn(BaseModel):
    host_id: int
    summary: str
    actor: str = ""
    result: str = "success"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scheduler_loop() -> None:
    while True:
        try:
            run_all_checks()
        except Exception:  # noqa: BLE001 - scheduler must never die
            pass
        time.sleep(CHECK_INTERVAL_SECONDS)


def run_all_checks() -> list[dict]:
    """Probe every host once, record results, update statuses. Returns results.

    Probes run in parallel so a serverless invocation (10s limit on Vercel
    Hobby) finishes in time; DB writes stay sequential on one connection.
    """
    results = []
    with store.connect() as conn:
        store.ensure_seeded(conn)
        hosts = store.list_hosts(conn)
        with ThreadPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(prober.probe_host, [h["address"] for h in hosts]))
        for host, outcome in zip(hosts, outcomes):
            store.add_check(conn, host["id"], outcome["ok"], outcome["latency_ms"], outcome["detail"])
            # Offline only after N consecutive failures.
            if outcome["ok"]:
                new_status = "online"
                last_seen = _now_iso()
            else:
                recent = conn.execute(
                    "SELECT ok FROM checks WHERE host_id = ? ORDER BY id DESC LIMIT ?",
                    (host["id"], OFFLINE_AFTER_FAILURES),
                ).fetchall()
                failures = sum(1 for r in recent if r["ok"] == 0)
                new_status = "offline" if failures >= OFFLINE_AFTER_FAILURES else host["status"]
                last_seen = host["last_seen_at"]
            store.update_host_status(
                conn,
                host["id"],
                new_status,
                outcome["latency_ms"],
                last_seen,
                outcome["cert_expires_at"] or host["cert_expires_at"],
            )
            results.append({"host_id": host["id"], "name": host["name"], **outcome})
    return results


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/hosts")
def api_list_hosts() -> list[dict]:
    with store.connect() as conn:
        store.ensure_seeded(conn)
        return store.list_hosts(conn)


@app.post("/api/hosts", status_code=201)
def api_add_host(body: HostIn) -> dict:
    with store.connect() as conn:
        return store.add_host(conn, body.name, body.address, body.kind)


@app.delete("/api/hosts/{host_id}")
def api_delete_host(host_id: int) -> dict:
    with store.connect() as conn:
        if not store.delete_host(conn, host_id):
            raise HTTPException(status_code=404, detail="host not found")
    return {"deleted": host_id}


@app.get("/api/deploys")
def api_list_deploys() -> list[dict]:
    with store.connect() as conn:
        return store.list_deploys(conn)


@app.post("/api/deploys", status_code=201)
def api_add_deploy(body: DeployIn) -> dict:
    with store.connect() as conn:
        if store.get_host(conn, body.host_id) is None:
            raise HTTPException(status_code=404, detail="host not found")
        if body.result not in ("success", "failed"):
            raise HTTPException(status_code=400, detail="result must be success or failed")
        return store.add_deploy(conn, body.host_id, body.summary, body.actor, body.result)


@app.get("/api/checks")
def api_list_checks() -> list[dict]:
    with store.connect() as conn:
        return store.list_checks(conn)


@app.post("/api/checks/run")
def api_run_checks() -> list[dict]:
    return run_all_checks()


if __name__ == "__main__":
    import os

    import uvicorn

    store.init_db()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
