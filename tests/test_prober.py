"""Prober unit tests: liveness verdicts and cert-day math."""

import socket
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import prober


class _OKHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def _serve():
    server = HTTPServer(("127.0.0.1", 0), _OKHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_probe_http_local_ok():
    server = _serve()
    port = server.server_address[1]
    ok, latency, detail = prober.probe_http(f"http://127.0.0.1:{port}/")
    assert ok is True
    assert latency is not None and latency >= 0
    assert "200" in detail
    server.shutdown()


def test_probe_http_refused_is_failure_not_exception():
    ok, latency, detail = prober.probe_http("http://127.0.0.1:1/")
    assert ok is False
    assert detail != ""


def test_cert_days_left_unreachable_returns_none():
    days, expires = prober.cert_days_left("http://127.0.0.1:1/")
    assert days is None and expires is None


def test_probe_host_local_reports_no_cert():
    server = _serve()
    port = server.server_address[1]
    out = prober.probe_host(f"http://127.0.0.1:{port}/")
    assert out["ok"] is True
    assert out["cert_days_left"] is None  # plain HTTP has no TLS cert
    server.shutdown()


# --- TLS cert-day extraction tests -------------------------------------------

def _gen_ca_cert(tmp_path):
    """Generate a self-signed CA certificate + key with openssl."""
    ca_key = tmp_path / "ca-key.pem"
    ca_cert = tmp_path / "ca-cert.pem"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(ca_key), "-out", str(ca_cert),
            "-days", "30", "-nodes", "-subj", "/CN=Test CA",
        ],
        check=True, capture_output=True,
    )
    return ca_cert, ca_key


def _gen_server_cert(tmp_path, ca_cert, ca_key):
    """Generate a server cert signed by the CA (90-day validity)."""
    srv_key = tmp_path / "srv-key.pem"
    srv_csr = tmp_path / "srv.csr"
    srv_cert = tmp_path / "srv-cert.pem"
    ext_file = tmp_path / "ext.cnf"
    ext_file.write_text("subjectAltName=IP:127.0.0.1\n")
    subprocess.run(
        [
            "openssl", "req", "-newkey", "rsa:2048",
            "-keyout", str(srv_key), "-out", str(srv_csr),
            "-nodes", "-subj", "/CN=127.0.0.1",
        ],
        check=True, capture_output=True,
    )
    subprocess.run(
        [
            "openssl", "x509", "-req", "-in", str(srv_csr),
            "-CA", str(ca_cert), "-CAkey", str(ca_key), "-CAcreateserial",
            "-out", str(srv_cert), "-days", "90",
            "-extfile", str(ext_file),
        ],
        check=True, capture_output=True,
    )
    return srv_cert, srv_key


def _serve_tls(certfile, keyfile):
    """Start a local HTTPS server, return the server object."""
    server = HTTPServer(("127.0.0.1", 0), _OKHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(certfile), str(keyfile))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_cert_days_left_local_tls(tmp_path, monkeypatch):
    """Cert extraction returns real days/expires against a local TLS server."""
    ca_cert, ca_key = _gen_ca_cert(tmp_path)
    srv_cert, srv_key = _gen_server_cert(tmp_path, ca_cert, ca_key)
    server = _serve_tls(srv_cert, srv_key)
    port = server.server_address[1]

    # Make prober trust our test CA so the handshake validates the cert.
    _orig = ssl.create_default_context

    def _trusted_ctx():
        ctx = _orig()
        ctx.check_hostname = False
        ctx.load_verify_locations(str(ca_cert))
        return ctx

    monkeypatch.setattr(ssl, "create_default_context", _trusted_ctx)

    days, expires = prober.cert_days_left(f"https://127.0.0.1:{port}/")
    assert days is not None
    assert 0 <= days <= 91  # cert is valid for 90 days
    assert expires is not None
    server.shutdown()
