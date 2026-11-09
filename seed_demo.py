"""Seed the deployed demo dashboard with real hosts so judges see data.

Usage:
    python seed_demo.py https://ops-dashboard-xxxx.onrender.com

Only adds hosts/deploys via the public API; never deploys proxy nodes.
Hosts are auto-seeded on Vercel, so this script is mainly useful for
persistent deployments (Render / own machine).
"""

import json
import sys
import urllib.request

HOSTS = [
    {"name": "tv.ztech.eu.cc", "address": "https://tv.ztech.eu.cc", "kind": "domain"},
    {"name": "example.com", "address": "https://example.com", "kind": "domain"},
]


def call(base: str, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> None:
    base = sys.argv[1]
    print("health:", call(base, "GET", "/healthz"))
    created = []
    for host in HOSTS:
        created.append(call(base, "POST", "/api/hosts", host))
    print("hosts:", [(h["id"], h["name"]) for h in created])
    if created:
        deploy = call(
            base,
            "POST",
            "/api/deploys",
            {
                "host_id": created[0]["id"],
                "summary": "seed demo data",
                "actor": "elmo",
                "result": "success",
            },
        )
        print("deploy:", deploy["id"], deploy["summary"])
    print("checks:", call(base, "POST", "/api/checks/run"))


if __name__ == "__main__":
    main()
