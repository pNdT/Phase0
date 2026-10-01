"""Cloud entrypoint (Vercel). See docs/DEPLOY-VERCEL.md.

Required environment variables:
    DATABASE_URL     Postgres connection string (Neon or Supabase pooler)
    PHASE0_PASSWORD  password for the single sign-in screen
    LLM_PROVIDER, LLM_API_KEY, LLM_MODELS (and LLM_BASE_URL when not Groq/OpenAI/OpenRouter)
Optional:
    PHASE0_SECRET    signs session cookies; changing it signs everyone out
"""
import os

from . import llm
from .core import Store
from .server import App

_app = None


def build():
    missing = [name for name in ("DATABASE_URL", "PHASE0_PASSWORD") if not os.environ.get(name)]
    if llm.is_local():
        missing.append("LLM_PROVIDER (Ollama is not available in the cloud)")
    if missing:
        return App(None, cloud=True, setup_error="missing environment variables: " + ", ".join(missing) + ".")
    try:
        store = Store(database_url=os.environ["DATABASE_URL"])
    except Exception:
        return None  # Database unreachable: answer this request with an error and retry on the next one.
    return App(store, cloud=True, password=os.environ["PHASE0_PASSWORD"], secret=os.environ.get("PHASE0_SECRET"))


def app(environ, start_response):
    global _app
    if _app is None:
        _app = build()
    current = _app or App(None, cloud=True, setup_error="could not connect to DATABASE_URL. Check the connection string.")
    headers = {key[5:].replace("_", "-").lower(): value for key, value in environ.items() if key.startswith("HTTP_")}
    if environ.get("CONTENT_TYPE"):
        headers["content-type"] = environ["CONTENT_TYPE"]
    body = b""
    if environ.get("REQUEST_METHOD") == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length) if 0 < length <= 64000 else b""
    path = environ.get("PATH_INFO") or "/"
    response = current.handle(environ.get("REQUEST_METHOD", "GET"), path, headers, body)
    reasons = {200: "OK", 201: "Created", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
               404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large",
               422: "Unprocessable Entity", 500: "Internal Server Error", 503: "Service Unavailable"}
    start_response(f"{response.status} {reasons.get(response.status, 'Status')}", response.headers)
    return [response.body]
