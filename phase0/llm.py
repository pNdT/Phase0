"""Model provider used by Phase 0.

Locally the default stays the native Ollama API. In the cloud (Vercel), Ollama is
not available, so any OpenAI-compatible endpoint (Groq, OpenRouter, OpenAI) can be
selected through environment variables:

    LLM_PROVIDER=groq            # or "openai" for any compatible endpoint
    LLM_BASE_URL=https://api.groq.com/openai/v1
    LLM_API_KEY=...
    LLM_MODELS=openai/gpt-oss-120b,openai/gpt-oss-20b

The rest of the code keeps speaking the Ollama dialect (`/api/tags`, `/api/chat`
with `format` and `options`); `request` translates it for compatible providers so
the discovery, scope and research pipelines stay unchanged.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA = "http://127.0.0.1:11434"
DEFAULT_BASE_URLS = {"groq": "https://api.groq.com/openai/v1", "openai": "https://api.openai.com/v1",
                     "openrouter": "https://openrouter.ai/api/v1"}
LABELS = {"ollama": "Ollama", "groq": "Groq", "openai": "OpenAI-compatible API", "openrouter": "OpenRouter"}


class ProviderError(Exception):
    pass


def provider():
    return (os.environ.get("LLM_PROVIDER") or "ollama").strip().lower()


def is_local():
    return provider() == "ollama"


def label():
    return LABELS.get(provider(), provider())


def base_url():
    configured = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    if provider() in DEFAULT_BASE_URLS:
        return DEFAULT_BASE_URLS[provider()]
    raise ProviderError("LLM_BASE_URL is required for provider " + provider() + ".")


def configured_models():
    return [name.strip() for name in os.environ.get("LLM_MODELS", "").split(",") if name.strip()]


def _post(url, payload, headers, timeout):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _ollama(path, payload, timeout):
    try:
        return _post(OLLAMA + path, payload, {}, timeout)
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise ProviderError("Could not reach local Ollama. Start Ollama and retry. No message was saved.") from exc


def _compatible_chat(payload, timeout):
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        raise ProviderError("LLM_API_KEY is not configured on the server. No message was saved.")
    options = payload.get("options") or {}
    body = {"model": payload["model"], "messages": list(payload["messages"]), "stream": False,
            "temperature": options.get("temperature", 0)}
    if options.get("num_predict"):
        body["max_tokens"] = options["num_predict"]
    schema = payload.get("format")
    if isinstance(schema, dict):
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "phase0_response", "schema": schema, "strict": False}}
    elif schema == "json":
        body["response_format"] = {"type": "json_object"}
    headers = {"Authorization": "Bearer " + key}
    url = base_url() + "/chat/completions"
    try:
        try:
            result = _post(url, body, headers, timeout)
        except HTTPError as exc:
            # Some models accept JSON mode but not schemas; keep the schema as an instruction.
            if exc.code != 400 or not isinstance(schema, dict):
                raise
            body["response_format"] = {"type": "json_object"}
            body["messages"] = [{"role": "system", "content": "Return only one JSON object matching this JSON schema: "
                                 + json.dumps(schema)}] + body["messages"]
            result = _post(url, body, headers, timeout)
        content = result["choices"][0]["message"].get("content") or ""
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise ProviderError("The model provider rejected the API key. No message was saved.") from exc
        if exc.code == 429:
            raise ProviderError("The model provider rate limit was reached. Wait a moment and retry. No message was saved.") from exc
        raise ProviderError(f"The model provider returned HTTP {exc.code}. No message was saved.") from exc
    except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Could not reach the model provider. Retry in a moment. No message was saved.") from exc
    return {"message": {"role": "assistant", "content": content}}


def request(path, payload=None, timeout=10):
    """Ollama-dialect request, answered by the configured provider."""
    if is_local():
        return _ollama(path, payload, timeout)
    if path == "/api/tags":
        return {"models": [{"name": name, "capabilities": ["completion"]} for name in configured_models()]}
    if path == "/api/chat":
        return _compatible_chat(payload, timeout)
    raise ProviderError("Unsupported model request.")


def models():
    result = request("/api/tags")
    if not is_local():
        return [m["name"] for m in result.get("models", [])]
    return [m["name"] for m in result.get("models", [])
            if not m.get("remote_model") and not m.get("remote_host")
            and not m.get("name", "").endswith(":cloud")
            and (not m.get("capabilities") or "completion" in m["capabilities"])]
