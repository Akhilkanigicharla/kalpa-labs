#!/usr/bin/env python3
"""Tests for smoke.py: python3 00-hq/launch/test_smoke.py  (local servers only, no internet)."""
import functools, http.server, json, os, sys, tempfile, threading, unittest
from datetime import datetime, timezone
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke, check  # noqa: E402

GOOD_HDR = {"Strict-Transport-Security": "max-age=31536000", "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin", "Permissions-Policy": "camera=()"}
SITE = os.path.join(os.path.dirname(HERE), "site")


def server(good):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass

        def end_headers(self):
            if good:
                for k, v in GOOD_HDR.items():
                    self.send_header(k, v)
            super().end_headers()

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(n)
            code, body = (200, {"output": "Hi from Kalpa Bhai"}) if good else (503, {"error": "models unavailable"})
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def fake_tap(code):
    return lambda *a, **k: SimpleNamespace(returncode=code, stdout="PASS tap sweep\n" if code == 0 else "2 problem(s)\n")


class Smoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good, cls.gurl = server(True)
        cls.bad, cls.burl = server(False)

    @classmethod
    def tearDownClass(cls):
        cls.good.shutdown(); cls.bad.shutdown()

    def target(self, url):
        return {"url": url, "chat_url": url + "api/chat", "checks": ["page", "headers", "chat", "tap"]}

    def test_good_site_passes(self):
        r = smoke.run_target("hq-site", self.target(self.gurl), run_fn=fake_tap(0))
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(list(r["steps"]), ["page", "headers", "chat", "tap"])

    def test_broken_site_fails_each_check(self):
        r = smoke.run_target("hq-site", self.target(self.burl), run_fn=fake_tap(1))
        self.assertFalse(r["ok"])
        for word in ("missing HSTS", "chat status 503", "tap: 2 problem(s)"):
            self.assertIn(word, r["detail"])

    def test_dead_url_fails_without_crash(self):
        dead = "http://127.0.0.1:9/"   # discard port: connection refused
        r = smoke.run_target("hq-site", self.target(dead), run_fn=fake_tap(0))
        self.assertFalse(r["ok"])
        self.assertEqual(list(r["steps"]), ["page"])   # stops after the page check

    def test_missing_page_404(self):
        t = dict(self.target(self.gurl + "no-such-page-xyz"), checks=["page"])
        self.assertIn("status 404", smoke.run_target("x", t)["detail"])

    def test_results_file_feeds_check_py(self):
        with tempfile.TemporaryDirectory() as d:
            tf, out = os.path.join(d, "t.json"), os.path.join(d, "smoke-results.json")
            json.dump({"_note": "x", "hq-site": self.target(self.gurl), "botbhai-site": {"url": ""}}, open(tf, "w"))
            self.assertEqual(smoke.main(["--targets", tf, "--out", out], run_fn=fake_tap(0)), 0)
            ctx = SimpleNamespace(now=datetime.now(timezone.utc), path=lambda p: p)
            ok, msg = check.check_smoke({"path": out, "targets": ["hq-site"]}, ctx)
            self.assertTrue(ok, msg)
            ok, msg = check.check_smoke({"path": out, "targets": ["botbhai-site"]}, ctx)
            self.assertFalse(ok)            # not-live targets are not run and stay red
            self.assertIn("no result", msg)

    def test_partial_run_keeps_old_time(self):
        old = {"at": "2026-01-01T00:00:00Z", "results": [{"name": "kits-site", "ok": True, "at": "2026-01-01T00:00:00Z"}]}
        new = [{"name": "hq-site", "ok": True, "at": "2026-11-21T00:00:00Z"}]
        m = smoke.merge(old, new)
        self.assertEqual(m["at"], "2026-01-01T00:00:00Z")   # stale kept result keeps the file stale
        self.assertEqual([r["name"] for r in m["results"]], ["hq-site", "kits-site"])

    def test_unknown_target_is_clear_error(self):
        with self.assertRaises(SystemExit) as e:
            smoke.main(["--only", "nope"])
        self.assertIn("unknown target", str(e.exception.code))

    def test_hostile_chat_body(self):
        f = lambda url, data=None, timeout=20: (200, {}, "<html>not json")
        ok, detail = smoke.check_chat({"chat_url": "x"}, {"fetch": f})
        self.assertFalse(ok)
        self.assertIn("empty answer", detail)


if __name__ == "__main__":
    unittest.main(verbosity=1)
