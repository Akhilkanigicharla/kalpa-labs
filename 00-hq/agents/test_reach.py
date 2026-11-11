"""Offline tests for reach.py (no network, no real CLI). Run: python3 00-hq/agents/test_reach.py"""
import json, os, subprocess, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
import reach as A
import runner as R


class FakeRun:
    """Stands in for subprocess.run: answers `version`, then the scripted fetch output."""
    def __init__(self, out="", version=A.PINNED, exc=None):
        self.out, self.version, self.exc, self.calls = out, version, exc, []

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        if argv[1:] == ["version"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"ok": True, "result": {"version": self.version}}), "")
        if self.exc:
            raise self.exc
        return subprocess.CompletedProcess(argv, 0, self.out, "")


def ok(text, title="T"):
    return json.dumps({"ok": True, "items": [{"title": title, "text": text}], "error": None})


ENV = {"KL_AGENT_REACH": "/opt/ar/bin/agent-reach", "PATH": "/usr/bin", "GROQ_API_KEY": "secret",
       "GITHUB_TOKEN": "ghs_x", "HTTPS_PROXY": "http://proxy:1"}


class Reach(unittest.TestCase):
    def setUp(self):
        A._BIN.clear()

    def test_channel_detection(self):
        c = A.channel_for
        self.assertEqual(c("https://www.youtube.com/watch?v=jNQXAC9IVRw"), "youtube")
        self.assertEqual(c("https://youtu.be/jNQXAC9IVRw"), "youtube")
        self.assertEqual(c("https://m.youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(c("https://github.com/Panniantong/Agent-Reach"), "github")
        self.assertEqual(c("https://old.reddit.com/r/Python/comments/x/"), "reddit")
        self.assertEqual(c("https://blog.example.com/feed.xml"), "web")
        self.assertEqual(c("https://notyoutube.com/x"), "web")  # suffix tricks are not YouTube

    def test_blocked_and_unsafe_urls(self):
        for u in ["https://x.com/a", "https://twitter.com/a", "https://www.linkedin.com/in/a", "https://instagram.com/a",
                  "https://www.facebook.com/a", "https://www.xiaohongshu.com/x", "https://www.bilibili.com/video/1",
                  "https://www.justdial.com/Hyderabad", "https://www.google.com/maps/place/x", "https://maps.google.com/x",
                  "http://localhost:8080/", "http://127.0.0.1/", "http://169.254.169.254/latest", "http://10.0.0.1/",
                  "file:///etc/passwd", "ftp://a.com/x", "https://user:pw@github.com/a/b", "https://intranet/x",
                  "https://a.internal/x", "https://github.com/a b", None, "x" * 3000]:
            self.assertIsNone(A.channel_for(u), u)

    def test_allow_list_is_only_no_login_backends(self):
        self.assertEqual(set(A.ALLOW), {"youtube", "github", "reddit", "web"})
        self.assertFalse(set(A.ALLOW) & A.BLOCKED_CHANNELS)
        self.assertNotIn("opencli", [b for _, b in A.ALLOW.values()])  # the browser/login backend
        self.assertNotIn("gh", [b for _, b in A.ALLOW.values()])  # gh CLI would use a logged-in token
        self.assertTrue(A.allowed("reddit", "read", "public-web"))
        self.assertFalse(A.allowed("reddit", "read", "opencli"))
        self.assertFalse(A.allowed("twitter", "read", "public-web"))
        self.assertFalse(A.allowed("youtube", "transcribe", "whisper"))

    def test_command_always_names_backend(self):
        argv = A.command("https://www.reddit.com/r/Python/comments/1/", "ar", 30)
        self.assertEqual(argv, ["ar", "reddit", "read", "https://www.reddit.com/r/Python/comments/1/",
                                "--backend", "public-web", "--timeout", "30"])
        y = A.command("https://youtu.be/jNQXAC9IVRw", "ar")
        self.assertEqual(y[1:3], ["youtube", "subtitle"])
        self.assertEqual(y[y.index("--backend") + 1], "yt-dlp")
        self.assertIsNone(A.command("https://x.com/a", "ar"))

    def test_find_urls(self):
        t = "See https://youtu.be/abc, and (https://github.com/a/b). Again https://youtu.be/abc! https://d.com https://e.com"
        self.assertEqual(A.find_urls(t), ["https://youtu.be/abc", "https://github.com/a/b", "https://d.com"])
        self.assertEqual(A.find_urls(""), [])

    def test_truncate(self):
        self.assertEqual(A.truncate("abc", 10), "abc")
        out = A.truncate("x" * 500, 100)
        self.assertEqual(len(out), 100)
        self.assertTrue(out.endswith("[... cut to fit]"))
        self.assertEqual(A.truncate("abc", 0), "")
        self.assertEqual(A.truncate("abcdef", 3), "abc")

    def test_clean_env_drops_secrets(self):
        e = A.clean_env(ENV)
        self.assertEqual(set(e), {"PATH", "HTTPS_PROXY"})

    def test_format_result(self):
        self.assertEqual(A.format_result(ok("hello world"), "u", 100), "T\nhello world")
        self.assertIn("UPSTREAM_BROKEN", A.format_result(json.dumps({"ok": False, "error": {"code": "UPSTREAM_BROKEN"}}), "u", 99))
        self.assertIn("unreadable", A.format_result("not json", "u", 99))
        wall = ok("You've been blocked by network security.\nTo continue, log in to your Reddit account")
        self.assertIn("login wall", A.format_result(wall, "u", 999))
        self.assertLessEqual(len(A.format_result(ok("y" * 9000), "u", 500)), 500)

    def test_fetch_success_uses_clean_env_and_pinned_cli(self):
        run = FakeRun(ok("caption text"))
        out = A.fetch("https://youtu.be/jNQXAC9IVRw", 200, ENV, run)
        self.assertEqual(out, "T\ncaption text")
        argv, kw = run.calls[-1]
        self.assertEqual(argv[0], "/opt/ar/bin/agent-reach")
        self.assertNotIn("GROQ_API_KEY", kw["env"])
        self.assertNotIn("GITHUB_TOKEN", kw["env"])
        self.assertIsInstance(argv, list)

    def test_fetch_fallbacks(self):
        url = "https://youtu.be/jNQXAC9IVRw"
        self.assertIn("not installed", A.fetch(url, 200, {"PATH": "/nonexistent"}, FakeRun()))
        self.assertIn("not installed", A.fetch(url, 200, ENV, FakeRun(version="0.1.0")))  # PyPI look-alike refused
        A._BIN.clear()
        self.assertIn("timed out", A.fetch(url, 200, ENV, FakeRun(exc=subprocess.TimeoutExpired("x", 1))))
        self.assertIn("FileNotFoundError", A.fetch(url, 200, ENV, FakeRun(exc=FileNotFoundError())))
        self.assertIn("not an allowed", A.fetch("https://x.com/a", 200, ENV, FakeRun()))
        self.assertIn("turned off", A.fetch(url, 200, {**ENV, "KL_REACH": "0"}, FakeRun()))

    def test_context_for_budget_and_scope(self):
        run = FakeRun(ok("z" * 9000))
        t = "Study https://youtu.be/jNQXAC9IVRw and https://github.com/a/b and https://blog.example.com/x"
        out = A.context_for(t, 3500, env=ENV, run=run)
        self.assertLessEqual(len(out), 3500)
        self.assertIn("WEB SOURCES", out)
        fetched = [c[0][3] for c in run.calls if c[0][1:] != ["version"]]
        self.assertEqual(fetched, ["https://youtu.be/jNQXAC9IVRw", "https://github.com/a/b"])  # plain web not auto-read
        self.assertEqual(A.context_for("no links here", 3500, env=ENV, run=run), "")
        self.assertEqual(A.context_for("https://x.com/a", 3500, env=ENV, run=run), "")


class RunnerHook(unittest.TestCase):
    def test_worker_gets_web_sources_within_max_context(self):
        root = tempfile.mkdtemp()
        open(os.path.join(root, "BIG.md"), "w").write("r" * 20000)
        seen = []
        orig = A.context_for
        A.context_for = lambda text, budget, **k: (seen.append(budget), "WEB SOURCES:\n" + "w" * (budget - 13))[1]
        try:
            calls = []
            def post(url, headers, payload):
                calls.append(payload)
                return {"choices": [{"message": {"content": "draft" if len(calls) == 1 else "PASS"}}]}
            task = {"id": "T9", "title": "Summarise https://youtu.be/jNQXAC9IVRw", "read": ["BIG.md"]}
            R.work(task, {"GROQ_API_KEY": "g"}, post, root)
        finally:
            A.context_for = orig
        user = calls[0]["messages"][1]["content"]
        self.assertEqual(seen, [R.MAX_CONTEXT // 2])
        self.assertIn("WEB SOURCES", user)
        self.assertLessEqual(user.count("r") + user.count("w"), R.MAX_CONTEXT + 50)  # repo + web share the cap

    def test_no_links_means_no_cli_call(self):
        self.assertEqual(A.context_for("Write a pitch", 3500, run=lambda *a, **k: 1 / 0), "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
