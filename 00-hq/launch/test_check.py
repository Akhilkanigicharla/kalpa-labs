#!/usr/bin/env python3
"""Tests for the A57 readiness board. Run: python3 00-hq/launch/test_check.py"""
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402

NOW = datetime(2026, 12, 6, 10, 0, tzinfo=check.IST)

ROADMAP_GREEN = """# Roadmap
- [x] **A61** HQ · smoke tests
- [x] **A65** HQ · AUDIT fix
- [x] **C06** HQ · ledger
"""
ROADMAP_RED = ROADMAP_GREEN.replace("[x] **A65**", "[ ] **A65**").replace("[x] **C06**", "[~] **C06**")

AUDIT = """# Audit

| Item | Check | Verdict | Evidence |
|---|---|---|---|
| A41 | files | VERIFIED | ok |

| # | Claim | File:line | Verdict | Evidence | Fix |
|---|---|---|---|---|---|
| 1 | old prices | PLAN.md:9 | **WRONG (stale)** | new prices | **A65** |
| 2 | day count | SOFT-LAUNCH.md:9 | STALE | 28 days | A65 |
| 3 | WRONG in claim text only | x | VERIFIED | fine | none |
"""

CONFIG = {"rows": [
    {"id": "O1", "kind": "offer", "label": "Offer one", "checks": [
        {"kind": "roadmap", "items": ["A61"]},
        {"kind": "env", "names": ["KALPA_TEST_KEY"]},
        {"kind": "file", "path": "privacy.md", "contains": ["Groq", "NVIDIA"]},
        {"kind": "cmd", "run": ["python3", "-c", "import sys; sys.exit(0)"]}]},
    {"id": "R1", "kind": "rule", "label": "CI", "checks": [
        {"kind": "ci", "repo": "o/r", "workflow": "quality.yml", "branch": "main"}]},
    {"id": "R2", "kind": "rule", "label": "Smoke", "checks": [
        {"kind": "smoke", "path": "smoke.json", "targets": ["site", "chat"], "max_age_hours": 12}]},
    {"id": "R3", "kind": "rule", "label": "Audit", "checks": [
        {"kind": "audit", "dir": "audit", "max_age_days": 14}]},
    {"id": "R5", "kind": "rule", "label": "Ledger", "checks": [
        {"kind": "roadmap", "items": ["C06"]},
        {"kind": "fresh", "path": "reconciled.json", "max_age_days": 8}]},
]}

SECRET = "s3cr3t-value-never-print"


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text if isinstance(text, str) else json.dumps(text))


def green_http(url, token):
    assert token == SECRET and "o/r/actions/workflows/quality.yml/runs" in url and "branch=main" in url
    return {"workflow_runs": [{"conclusion": "success", "head_sha": "abc1234def"}]}


def make_root(green):
    root = tempfile.mkdtemp(prefix="readiness-")
    write(root, "00-hq/ROADMAP.md", ROADMAP_GREEN if green else ROADMAP_RED)
    write(root, "audit/README.md", "not a report")
    write(root, "audit/2026-11-30-0900.md", AUDIT)
    write(root, "privacy.md", "Processors: Groq, NVIDIA, Meta" if green else "Processors: Groq, Meta")
    if green:
        write(root, "smoke.json", {"at": "2026-12-06T08:00:00+05:30", "results": [
            {"name": "site", "ok": True}, {"name": "chat", "ok": True}]})
        write(root, "reconciled.json", {"at": "2026-12-01"})
    return root


def board(root, env, http=None):
    return check.run_board(CONFIG, check.Ctx(root, env, NOW, http))


def reasons(b, row_id):
    row = next(r for r in b["rows"] if r["id"] == row_id)
    return [c["reason"] for c in row["checks"] if not c["ok"]]


class GreenFixture(unittest.TestCase):
    def test_all_green(self):
        b = board(make_root(True), {"KALPA_TEST_KEY": SECRET, "GITHUB_TOKEN": SECRET}, green_http)
        self.assertTrue(b["ok"], [(r["id"], r["checks"]) for r in b["rows"] if not r["ok"]])
        self.assertEqual((b["green"], b["total"]), (5, 5))
        self.assertIn("0 WRONG open in 2026-11-30-0900.md", reasons_all(b, "R3"))
        self.assertIn("quality.yml on abc1234: success", reasons_all(b, "R1"))
        self.assertNotIn(SECRET, json.dumps(b))
        text = check.render(b)
        self.assertIn("5/5 green", text)
        self.assertIn("READY", text)
        self.assertNotIn(SECRET, text)


def reasons_all(b, row_id):
    return [c["reason"] for r in b["rows"] if r["id"] == row_id for c in r["checks"]]


class RedFixture(unittest.TestCase):
    def setUp(self):
        self.b = board(make_root(False), {})

    def test_nothing_green(self):
        self.assertFalse(self.b["ok"])
        self.assertEqual(self.b["green"], 0)

    def test_reasons(self):
        self.assertEqual(reasons(self.b, "R1"), ["unknown: GITHUB_TOKEN not set"])
        self.assertEqual(reasons(self.b, "R2"), ["no smoke results yet"])
        self.assertEqual(reasons(self.b, "R3"), ["1 WRONG open in 2026-11-30-0900.md: #1 (A65)"])
        self.assertEqual(reasons(self.b, "R5"), ["not done: C06", "missing reconciled.json"])
        o1 = reasons(self.b, "O1")
        self.assertIn("env not set: KALPA_TEST_KEY", o1)
        self.assertIn("privacy.md lacks: NVIDIA", o1)

    def test_render_marks_red(self):
        text = check.render(self.b)
        self.assertIn("0/5 green", text)
        self.assertIn("✗ R2  Smoke", text)
        self.assertIn("✗ smoke: no smoke results yet", text)
        self.assertIn("NOT READY: 5 red", text)


class Edges(unittest.TestCase):
    def ctx(self, root, env=None, http=None):
        return check.Ctx(root, env or {}, NOW, http)

    def test_ci_failure_and_api_error_are_red(self):
        root = make_root(True)
        fail = lambda u, t: {"workflow_runs": [{"conclusion": "failure", "head_sha": "beef000"}]}
        self.assertEqual(check.check_ci(CONFIG["rows"][1]["checks"][0], self.ctx(root, {"GITHUB_TOKEN": "t"}, fail)),
                         (False, "quality.yml on beef000: failure"))

        def boom(u, t):
            raise urllib.error.URLError("offline")
        ok, why = check.check_ci(CONFIG["rows"][1]["checks"][0], self.ctx(root, {"GITHUB_TOKEN": "t"}, boom))
        self.assertFalse(ok)
        self.assertTrue(why.startswith("unknown: GitHub API error"))

    def test_smoke_old_failed_or_missing_target(self):
        root = make_root(True)
        spec = {"path": "smoke.json", "targets": ["site", "chat"], "max_age_hours": 12}
        write(root, "smoke.json", {"at": "2026-12-05T08:00:00+05:30", "results": []})
        self.assertEqual(check.check_smoke(spec, self.ctx(root)), (False, "smoke results 26 h old (max 12 h)"))
        write(root, "smoke.json", {"at": "2026-12-06T09:00:00+05:30", "results": [
            {"name": "site", "ok": False, "detail": "HTTP 503"}]})
        self.assertEqual(check.check_smoke(spec, self.ctx(root)), (False, "site: HTTP 503; chat: no result"))
        write(root, "smoke.json", "{not json")
        self.assertFalse(check.check_smoke(spec, self.ctx(root))[0])

    def test_audit_missing_or_old(self):
        root = make_root(True)
        self.assertEqual(check.check_audit({"dir": "nope"}, self.ctx(root)), (False, "no audit report yet"))
        ok, why = check.check_audit({"dir": "audit", "max_age_days": 3}, self.ctx(root))
        self.assertFalse(ok)
        self.assertIn("old (max 3 days)", why)

    def test_audit_wrong_without_fix_item_is_open(self):
        root = make_root(True)
        write(root, "audit/2026-12-01-1000.md", AUDIT.replace("**A65** |", "none |"))
        self.assertEqual(check.check_audit({"dir": "audit"}, self.ctx(root)),
                         (False, "1 WRONG open in 2026-12-01-1000.md: #1 (no fix item)"))

    def test_roadmap_unknown_item(self):
        root = make_root(True)
        self.assertEqual(check.check_roadmap({"items": ["A61", "Z9"]}, self.ctx(root)),
                         (False, "not done: Z9 (not in roadmap)"))

    def test_binary_file_existence_only(self):
        root = tempfile.mkdtemp()
        with open(os.path.join(root, "a.pdf"), "wb") as f:
            f.write(b"%PDF\xd3\xc7\x82")
        self.assertEqual(check.check_file({"path": "a.pdf"}, self.ctx(root)), (True, "a.pdf present"))
        self.assertEqual(check.check_file({"path": "b.pdf"}, self.ctx(root)), (False, "missing b.pdf"))

    def test_cmd_failure(self):
        ok, why = check.check_cmd({"run": ["python3", "-c", "print('boom'); raise SystemExit(3)"]},
                                  self.ctx(tempfile.mkdtemp()))
        self.assertFalse(ok)
        self.assertIn("exit 3 (boom)", why)

    def test_env_reports_names_never_values(self):
        ok, why = check.check_env({"names": ["A_SET", "B_MISSING"]}, self.ctx(".", {"A_SET": SECRET}))
        self.assertEqual((ok, why), (False, "env not set: B_MISSING"))

    def test_validate_rejects_bad_config(self):
        for bad in ({}, {"rows": [{"id": "X", "label": "x", "kind": "offer", "checks": [{"kind": "nope"}]}]},
                    {"rows": [{"id": "X", "label": "x", "kind": "boss", "checks": [{"kind": "env", "names": []}]}]}):
            with self.assertRaises(ValueError):
                check.validate(bad)


class RealConfig(unittest.TestCase):
    def test_readiness_json_has_5_offers_and_6_rules(self):
        with open(os.path.join(check.HERE, "readiness.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        check.validate(cfg)
        kinds = [r["kind"] for r in cfg["rows"]]
        self.assertEqual((kinds.count("offer"), kinds.count("rule")), (5, 6))

    def test_cli_json_and_exit_code(self):
        env_backup = os.environ.pop("GITHUB_TOKEN", None)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = check.main(["--json"])
            data = json.loads(buf.getvalue())
            self.assertEqual(code, 0 if data["ok"] else 1)
            self.assertEqual(data["total"], 11)
            r1 = next(r for r in data["rows"] if r["id"] == "R1")
            self.assertEqual(r1["checks"][0]["reason"], "unknown: GITHUB_TOKEN not set")
        finally:
            if env_backup is not None:
                os.environ["GITHUB_TOKEN"] = env_backup


if __name__ == "__main__":
    unittest.main(verbosity=1)
