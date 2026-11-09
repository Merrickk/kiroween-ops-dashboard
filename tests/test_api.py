"""API tests via FastAPI TestClient, using a throwaway SQLite file."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
import store


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(store, "DB_PATH", db)
    monkeypatch.setattr(app_module.store, "DB_PATH", db)
    store.init_db(db)
    with TestClient(app_module.app) as c:
        yield c


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_hosts_crud(client):
    r = client.post("/api/hosts", json={"name": "demo", "address": "https://example.com"})
    assert r.status_code == 201
    host = r.json()
    assert host["name"] == "demo" and host["status"] == "unknown"

    hosts = client.get("/api/hosts").json()
    assert len(hosts) == 1

    assert client.delete(f"/api/hosts/{host['id']}").status_code == 200
    assert client.get("/api/hosts").json() == []


def test_deploys_need_existing_host(client):
    r = client.post("/api/deploys", json={"host_id": 999, "summary": "x"})
    assert r.status_code == 404

    host = client.post("/api/hosts", json={"name": "h", "address": "https://example.com"}).json()
    r = client.post(
        "/api/deploys",
        json={"host_id": host["id"], "summary": "deploy v1", "actor": "elmo", "result": "success"},
    )
    assert r.status_code == 201
    assert client.get("/api/deploys").json()[0]["summary"] == "deploy v1"


def test_run_checks_records_results(client, monkeypatch):
    host = client.post("/api/hosts", json={"name": "local", "address": "http://127.0.0.1:1/"}).json()
    # Offline verdict must not depend on real network: probe fails fast on refused port.
    results = client.post("/api/checks/run").json()
    assert len(results) == 1
    assert results[0]["ok"] is False
    checks = client.get("/api/checks").json()
    assert len(checks) == 1 and checks[0]["host_id"] == host["id"]


def test_offline_only_after_two_consecutive_failures(client):
    """Spec: consecutive 2 failures → offline; a single failure must not flip status."""
    client.post("/api/hosts", json={"name": "local", "address": "http://127.0.0.1:1/"})
    # First failure — should NOT be offline yet (avoid single-flap false positive).
    client.post("/api/checks/run")
    h = client.get("/api/hosts").json()[0]
    assert h["status"] != "offline"
    # Second consecutive failure — now offline.
    client.post("/api/checks/run")
    h = client.get("/api/hosts").json()[0]
    assert h["status"] == "offline"
