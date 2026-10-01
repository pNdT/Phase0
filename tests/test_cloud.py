import io
import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from phase0 import llm, wsgi
from phase0.core import AppError, Store, blank_profile
from phase0.server import App, SESSION_COOKIE

HOST = "phase0.example.vercel.app"


def output(updates=None, reply="Who will use this?"):
    facts = blank_profile()
    facts.update(updates or {})
    return json.dumps({"reply": reply, "updates": facts})


class ProviderTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"LLM_PROVIDER": "groq", "LLM_API_KEY": "key", "LLM_MODELS": "a/model, b/model"})
        env.start()
        self.addCleanup(env.stop)

    def test_models_come_from_configuration(self):
        self.assertEqual(llm.models(), ["a/model", "b/model"])
        self.assertFalse(llm.is_local())

    def test_ollama_chat_is_translated(self):
        schema = {"type": "object", "properties": {"reply": {"type": "string"}}, "required": ["reply"]}
        with patch("phase0.llm._post", return_value={"choices": [{"message": {"content": '{"reply":"ok"}'}}]}) as post:
            result = llm.request("/api/chat", {"model": "a/model", "stream": False, "format": schema,
                                                "messages": [{"role": "user", "content": "hi"}],
                                                "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 900}}, 30)
        url, body, headers, timeout = post.call_args.args
        self.assertEqual(url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(headers, {"Authorization": "Bearer key"})
        self.assertEqual(body["max_tokens"], 900)
        self.assertEqual(body["response_format"]["json_schema"]["schema"], schema)
        self.assertNotIn("options", body)
        self.assertEqual(result, {"message": {"role": "assistant", "content": '{"reply":"ok"}'}})

    def test_schema_rejection_falls_back_to_json_mode(self):
        error = HTTPError("u", 400, "bad", {}, io.BytesIO(b"{}"))
        ok = {"choices": [{"message": {"content": "{}"}}]}
        with patch("phase0.llm._post", side_effect=[error, ok]) as post:
            llm.request("/api/chat", {"model": "a/model", "format": {"type": "object"},
                                      "messages": [{"role": "user", "content": "hi"}]}, 30)
        retry = post.call_args.args[1]
        self.assertEqual(retry["response_format"], {"type": "json_object"})
        self.assertIn("JSON schema", retry["messages"][0]["content"])

    def test_bad_key_is_reported_without_saving(self):
        error = HTTPError("u", 401, "no", {}, io.BytesIO(b"{}"))
        with patch("phase0.llm._post", side_effect=error), self.assertRaises(llm.ProviderError):
            llm.request("/api/chat", {"model": "a/model", "messages": []}, 30)

    def test_missing_key_is_reported(self):
        with patch.dict(os.environ, {"LLM_API_KEY": ""}), self.assertRaises(llm.ProviderError):
            llm.request("/api/chat", {"model": "a/model", "messages": []}, 30)


class CloudAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / "test.sqlite3")
        self.app = App(self.store, cloud=True, password="correct horse", secret="s")

    def call(self, method, path, body=None, cookie=None, token=None, origin=None):
        headers = {"Host": HOST}
        if cookie:
            headers["Cookie"] = f"{SESSION_COOKIE}={cookie}"
        if token:
            headers["X-Phase0-Token"] = token
        if origin:
            headers["Origin"] = origin
        return self.app.handle(method, path, headers, json.dumps(body).encode() if body is not None else b"")

    def login(self):
        response = self.call("POST", "/api/login", {"password": "correct horse"}, origin="https://" + HOST)
        self.assertEqual(response.status, 200)
        cookie = dict(response.headers)["Set-Cookie"]
        self.assertIn("HttpOnly; Secure; SameSite=Strict", cookie)
        return cookie.split(";")[0].split("=", 1)[1]

    def test_signed_out_visitor_only_sees_login(self):
        page = self.call("GET", "/")
        self.assertEqual(page.status, 200)
        self.assertIn(b"login-form", page.body)
        self.assertEqual(self.call("GET", "/app.js").status, 401)
        self.assertEqual(self.call("GET", "/api/projects").status, 401)
        self.assertEqual(self.call("GET", "/login.js").status, 200)

    @patch("phase0.server.time.sleep")
    def test_wrong_password_is_rejected(self, sleep):
        self.assertEqual(self.call("POST", "/api/login", {"password": "guess"}).status, 401)
        self.assertEqual(self.call("POST", "/api/login", {}).status, 401)
        self.assertEqual(sleep.call_count, 2)

    def test_session_and_csrf_token_unlock_api(self):
        cookie = self.login()
        page = self.call("GET", "/", cookie=cookie)
        token = self.app.csrf(cookie)
        self.assertIn(token.encode(), page.body)
        self.assertIn(b'content="cloud"', page.body)
        self.assertEqual(self.call("GET", "/api/projects", cookie=cookie).status, 403)
        created = self.call("POST", "/api/projects", {"name": "Pulse"}, cookie=cookie, token=token)
        self.assertEqual(created.status, 201)
        listed = self.call("GET", "/api/projects", cookie=cookie, token=token)
        self.assertEqual([p["name"] for p in json.loads(listed.body)], ["Pulse"])

    def test_tampered_or_expired_cookie_is_rejected(self):
        cookie = self.login()
        self.assertEqual(self.call("GET", "/api/projects", cookie=cookie + "x").status, 401)
        expired = "1.abc"
        self.assertEqual(self.call("GET", "/api/projects", cookie=expired + "." + self.app.sign(expired)).status, 401)
        other = App(self.store, cloud=True, password="correct horse", secret="other")
        self.assertIsNone(other.session({"cookie": f"{SESSION_COOKIE}={cookie}"}))

    def test_cross_origin_requests_are_refused(self):
        cookie = self.login()
        response = self.call("POST", "/api/projects", {"name": "x"}, cookie=cookie, token=self.app.csrf(cookie),
                             origin="https://evil.example")
        self.assertEqual(response.status, 403)
        self.assertEqual(self.call("POST", "/api/login", {"password": "correct horse"}, origin="http://" + HOST).status, 403)

    def test_logout_clears_cookie(self):
        cookie = self.login()
        response = self.call("POST", "/api/logout", {}, cookie=cookie, token=self.app.csrf(cookie))
        self.assertIn("Max-Age=0", dict(response.headers)["Set-Cookie"])

    def test_local_mode_keeps_loopback_contract(self):
        local = App(self.store, port=8765)
        self.assertEqual(local.handle("GET", "/", {"Host": HOST}).status, 403)
        self.assertEqual(local.handle("POST", "/api/login", {"Host": "127.0.0.1:8765"}, b'{"password":"x"}').status, 403)
        page = local.handle("GET", "/", {"Host": "127.0.0.1:8765"})
        self.assertIn(local.token.encode(), page.body)
        self.assertIn(b'content="local"', page.body)


class WsgiTests(unittest.TestCase):
    def run_wsgi(self, environ):
        captured = {}
        body = wsgi.app({"REQUEST_METHOD": "GET", "PATH_INFO": "/", "HTTP_HOST": HOST, **environ},
                        lambda status, headers: captured.update(status=status, headers=headers))
        return captured["status"], b"".join(body)

    def test_missing_configuration_fails_closed(self):
        wsgi._app = None
        with patch.dict(os.environ, {"DATABASE_URL": "", "PHASE0_PASSWORD": "", "LLM_PROVIDER": ""}):
            status, body = self.run_wsgi({})
        wsgi._app = None
        self.assertTrue(status.startswith("503"))
        self.assertIn(b"PHASE0_PASSWORD", body)
        self.assertIn(b"LLM_PROVIDER", body)


@unittest.skipUnless(os.environ.get("PHASE0_TEST_DATABASE_URL"), "set PHASE0_TEST_DATABASE_URL to test Postgres")
class PostgresStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(database_url=os.environ["PHASE0_TEST_DATABASE_URL"])
        self.project = self.store.create("Dog matcher " + uuid.uuid4().hex[:6])
        for target in ('phase0.core.scope.input_decision', 'phase0.core.scope.output_allowed', 'phase0.core.planner.should_plan'):
            gate = patch(target, return_value={'phase0.core.scope.input_decision': 'allow',
                                               'phase0.core.scope.output_allowed': True}.get(target, False))
            gate.start()
            self.addCleanup(gate.stop)

    @patch("phase0.core.local_models", return_value=["a/model"])
    @patch("phase0.core.ollama_request")
    def test_chat_persists_turns_and_profile(self, request, models):
        request.return_value = {"message": {"content": output({"platform": {"value": "web", "evidence": "web app"}})}}
        result = self.store.chat(self.project["id"], "A web app for dogs", "a/model")
        self.assertEqual(result["profile"]["platform"]["value"], "web")
        self.assertNotIn("busy_until", result)
        restored = Store(database_url=os.environ["PHASE0_TEST_DATABASE_URL"]).get(self.project["id"])
        self.assertEqual([m["role"] for m in restored["messages"]], ["user", "assistant"])
        self.assertIn(self.project["id"], [p["id"] for p in self.store.list()])

    def test_lease_blocks_a_second_response_until_released(self):
        self.assertTrue(self.store.acquire(self.project["id"]))
        other_instance = Store(database_url=os.environ["PHASE0_TEST_DATABASE_URL"])
        with self.assertRaisesRegex(AppError, "already has a response"):
            other_instance.chat(self.project["id"], "hello", "a/model")
        self.store.release(self.project["id"])
        self.assertTrue(other_instance.acquire(self.project["id"]))
        other_instance.release(self.project["id"])

    def test_missing_project_is_not_reported_as_busy(self):
        with self.assertRaisesRegex(AppError, "Project not found"):
            self.store.acquire(str(uuid.uuid4()))


if __name__ == "__main__":
    unittest.main()
