import argparse
import json
import os
import secrets
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .core import AppError, Store, local_models
from .planner import catalog

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "phase0" / "web"


def serve(port=8765, data_dir=None):
    store = Store(Path(data_dir or os.environ.get("PHASE0_DATA_DIR", ROOT / "data")) / "phase0.sqlite3")
    token = secrets.token_urlsafe(32)
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log user content, tokens, or query strings.

        def send(self, status, body, content_type="application/json; charset=utf-8"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def authorized(self, api=False):
            if self.headers.get("Host") not in allowed_hosts:
                self.send(403, {"error": "Invalid host."})
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + h for h in allowed_hosts}:
                self.send(403, {"error": "Cross-origin access is disabled."})
                return False
            if api and not secrets.compare_digest(self.headers.get("X-Phase0-Token", ""), token):
                self.send(403, {"error": "Refresh the application to renew the local session."})
                return False
            return True

        def do_GET(self):
            path = urlsplit(self.path).path
            if not self.authorized(api=path.startswith("/api/")):
                return
            try:
                if path == "/api/status":
                    try:
                        models = local_models()
                        status = {"ollama": "ready", "models": models, "mode": "local inference", "step": 1,
                                  'features':['discovery','ollama-directed-research','architecture-dossier','prompt-deck']}
                    except AppError as exc:
                        status = {"ollama": "offline", "models": [], "error": str(exc), "step": 1}
                    self.send(200, status)
                elif path == "/api/projects":
                    self.send(200, store.list())
                elif path.startswith("/api/projects/"):
                    self.send(200, store.get(path.split("/")[-1]))
                elif path == "/api/hubs":
                    hubs = json.loads((ROOT / "hubs.json").read_text(encoding="utf-8"))
                    active = {'github','huggingface','public-apis-repo','free-for-dev','21st-dev','mobbin','uiverse'}
                    for hub in hubs:
                        if hub['id'] in active:
                            hub['status'] = 'active; bounded public connector, directed by Ollama'
                    self.send(200, hubs)
                elif path == '/api/catalog':
                    self.send(200,catalog())
                elif path in {"/", "/index.html", "/app.js", "/style.css"}:
                    filename = "index.html" if path == "/" else path[1:]
                    content = (WEB / filename).read_text(encoding="utf-8")
                    if filename == "index.html":
                        content = content.replace("__SESSION_TOKEN__", token)
                    mime = {"html": "text/html", "js": "text/javascript", "css": "text/css"}[filename.split(".")[-1]]
                    self.send(200, content, mime + "; charset=utf-8")
                else:
                    self.send(404, {"error": "Not found."})
            except AppError as exc:
                self.send(404, {"error": str(exc)})

        def do_POST(self):
            if not self.authorized(api=True):
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 64000:
                    self.send(413, {"error": "Invalid request size."})
                    return
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError()
                path = urlsplit(self.path).path
                if path == "/api/projects":
                    name = body.get("name", "Untitled project")
                    if not isinstance(name, str):
                        raise ValueError()
                    self.send(201, store.create(name))
                elif path.startswith("/api/projects/") and path.endswith("/chat"):
                    self.send(200, store.chat(path.split("/")[3], body.get("message"), body.get("model"),body.get('research_online',True)))
                else:
                    self.send(404, {"error": "Not found."})
            except (ValueError, TypeError):
                self.send(400, {"error": "Invalid JSON request."})
            except AppError as exc:
                self.send(422, {"error": str(exc)})
            except Exception:
                self.send(500, {"error": "Local server error. Your existing project is preserved."})

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
