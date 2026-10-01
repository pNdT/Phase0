import argparse
import hashlib
import hmac
import json
import os
import secrets
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import llm
from .core import AppError, Store, local_models
from .planner import catalog

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "phase0" / "web"
SECURITY_HEADERS = [
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),
]
SESSION_COOKIE = "__Host-phase0"
SESSION_SECONDS = 30 * 24 * 3600
PUBLIC_FILES = {"/style.css", "/login.js"}


class Response:
    def __init__(self, status, body, content_type="application/json; charset=utf-8", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.status = status
        self.body = body
        self.headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))] + SECURITY_HEADERS + (headers or [])


class App:
    """HTTP behaviour shared by the local server and the cloud (WSGI) entrypoint.

    Local mode keeps the original contract: loopback hosts only and a per-process
    session token. Cloud mode is reachable from the internet, so every page and API
    call requires a password session (signed cookie) plus a CSRF token.
    """

    def __init__(self, store, port=8765, cloud=False, password=None, secret=None, setup_error=None):
        self.store = store
        self.cloud = cloud
        self.setup_error = setup_error
        self.password = password or ""
        self.secret = (secret or hashlib.sha256(("phase0-session:" + self.password).encode()).hexdigest()).encode()
        self.token = secrets.token_urlsafe(32)
        self.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    # Sessions (cloud mode only)
    def sign(self, value):
        return hmac.new(self.secret, value.encode(), hashlib.sha256).hexdigest()

    def new_session(self):
        value = f"{int(time.time()) + SESSION_SECONDS}.{secrets.token_urlsafe(16)}"
        return value + "." + self.sign(value)

    def session(self, headers):
        for part in headers.get("cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name != SESSION_COOKIE:
                continue
            payload, _, signature = value.rpartition(".")
            expires = payload.split(".", 1)[0]
            if payload and hmac.compare_digest(self.sign(payload), signature) and expires.isdigit() \
                    and int(expires) > time.time():
                return value
        return None

    def csrf(self, session):
        return self.sign("csrf:" + session)

    def cookie(self, value, max_age):
        return ("Set-Cookie", f"{SESSION_COOKIE}={value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age={max_age}")

    # Request checks
    def origin_error(self, headers):
        host = headers.get("host", "")
        origin = headers.get("origin")
        if self.cloud:
            if not host:
                return Response(403, {"error": "Invalid host."})
            if origin and origin != "https://" + host:
                return Response(403, {"error": "Cross-origin access is disabled."})
            return None
        if host not in self.allowed_hosts:
            return Response(403, {"error": "Invalid host."})
        if origin and origin not in {"http://" + h for h in self.allowed_hosts}:
            return Response(403, {"error": "Cross-origin access is disabled."})
        return None

    def page(self, filename, token):
        content = (WEB / filename).read_text(encoding="utf-8")
        content = content.replace("__SESSION_TOKEN__", token).replace("__DEPLOYMENT__", "cloud" if self.cloud else "local")
        return Response(200, content, "text/html; charset=utf-8")

    def static(self, path):
        mime = {"js": "text/javascript", "css": "text/css"}[path.rsplit(".", 1)[-1]]
        return Response(200, (WEB / path[1:]).read_text(encoding="utf-8"), mime + "; charset=utf-8")

    def handle(self, method, raw_path, headers, body=b""):
        """headers: mapping with lower-case names. Returns a Response."""
        headers = {key.lower(): value for key, value in headers.items()}
        path = urlsplit(raw_path).path
        rejected = self.origin_error(headers)
        if rejected:
            return rejected
        if self.setup_error:
            return Response(503, {"error": self.setup_error}) if path.startswith("/api/") else \
                Response(503, "Phase 0 is not configured: " + self.setup_error, "text/plain; charset=utf-8")
        if method == "GET" and path in PUBLIC_FILES:
            return self.static(path)
        session = None
        if self.cloud:
            if method == "POST" and path == "/api/login":
                return self.login(headers, body)
            session = self.session(headers)
            if not session:
                if method == "GET" and path in {"/", "/index.html"}:
                    return self.page("login.html", "")
                return Response(401, {"error": "Sign in again to continue."})
            token = self.csrf(session)
        else:
            token = self.token
        if method == "GET" and path in {"/", "/index.html"}:
            return self.page("index.html", token)
        if method == "GET" and path == "/app.js":
            return self.static(path)
        if not path.startswith("/api/"):
            return Response(404, {"error": "Not found."})
        if not secrets.compare_digest(headers.get("x-phase0-token", ""), token):
            return Response(403, {"error": "Refresh the application to renew the session."})
        if method == "GET":
            return self.get(path)
        if method == "POST":
            if self.cloud and path == "/api/logout":
                return Response(200, {"ok": True}, headers=[self.cookie("", 0)])
            return self.post(path, headers, body)
        return Response(405, {"error": "Method not allowed."})

    def login(self, headers, body):
        try:
            password = json.loads(body).get("password")
        except (ValueError, TypeError, AttributeError):
            password = None
        if not isinstance(password, str) or not self.password or not hmac.compare_digest(
                hashlib.sha256(password.encode()).digest(), hashlib.sha256(self.password.encode()).digest()):
            time.sleep(1)  # Slows guessing; use a long password anyway.
            return Response(401, {"error": "Wrong password."})
        return Response(200, {"ok": True}, headers=[self.cookie(self.new_session(), SESSION_SECONDS)])

    def get(self, path):
        try:
            if path == "/api/status":
                base = {"provider": llm.provider(), "provider_label": llm.label(), "local": llm.is_local(),
                        "cloud": self.cloud, "step": 1}
                try:
                    status = {**base, "ollama": "ready", "models": local_models(),
                              "mode": "local inference" if llm.is_local() else "cloud inference",
                              "features": ['discovery', 'ollama-directed-research', 'architecture-dossier', 'prompt-deck']}
                except AppError as exc:
                    status = {**base, "ollama": "offline", "models": [], "error": str(exc)}
                return Response(200, status)
            if path == "/api/projects":
                return Response(200, self.store.list())
            if path.startswith("/api/projects/"):
                return Response(200, self.store.get(path.split("/")[-1]))
            if path == "/api/hubs":
                hubs = json.loads((ROOT / "hubs.json").read_text(encoding="utf-8"))
                active = {'github', 'huggingface', 'public-apis-repo', 'free-for-dev', '21st-dev', 'mobbin', 'uiverse'}
                for hub in hubs:
                    if hub['id'] in active:
                        hub['status'] = 'active; bounded public connector, directed by the selected model'
                return Response(200, hubs)
            if path == '/api/catalog':
                return Response(200, catalog())
            return Response(404, {"error": "Not found."})
        except AppError as exc:
            return Response(404, {"error": str(exc)})

    def post(self, path, headers, body):
        try:
            if not body or len(body) > 64000:
                return Response(413, {"error": "Invalid request size."})
            body = json.loads(body)
            if not isinstance(body, dict):
                raise ValueError()
            if path == "/api/projects":
                name = body.get("name", "Untitled project")
                if not isinstance(name, str):
                    raise ValueError()
                return Response(201, self.store.create(name))
            if path.startswith("/api/projects/") and path.endswith("/chat"):
                return Response(200, self.store.chat(path.split("/")[3], body.get("message"), body.get("model"),
                                                     body.get('research_online', True)))
            return Response(404, {"error": "Not found."})
        except (ValueError, TypeError):
            return Response(400, {"error": "Invalid JSON request."})
        except AppError as exc:
            return Response(422, {"error": str(exc)})
        except Exception:
            return Response(500, {"error": "Server error. Your existing project is preserved."})


def serve(port=8765, data_dir=None):
    store = Store(Path(data_dir or os.environ.get("PHASE0_DATA_DIR", ROOT / "data")) / "phase0.sqlite3")
    app = App(store, port)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log user content, tokens, or query strings.

        def respond(self, method):
            body = b""
            if method == "POST":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = -1
                if length <= 0 or length > 64000:
                    response = Response(413, {"error": "Invalid request size."})
                    return self.write(response)
                body = self.rfile.read(length)
            self.write(app.handle(method, self.path, dict(self.headers.items()), body))

        def write(self, response):
            self.send_response(response.status)
            for name, value in response.headers:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(response.body)

        def do_GET(self):
            self.respond("GET")

        def do_POST(self):
            self.respond("POST")

    class LocalServer(ThreadingHTTPServer):
        allow_reuse_address = False
        allow_reuse_port = False

        def server_bind(self):
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    server = LocalServer(("127.0.0.1", port), Handler)
    print(f"Phase 0: http://127.0.0.1:{port} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir")
    args = parser.parse_args()
    serve(args.port, args.data_dir)
