"""A215: Langfuse -> audit CSV importer. Offline: a fake opener plays the Langfuse API."""
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "p1_cost_audit"))
import audit  # noqa: E402
import langfuse_pull as lp  # noqa: E402


def gen(i, **kw):
    o = {"id": f"o{i}", "traceId": f"t{i}", "type": "GENERATION", "startTime": "2026-11-02T10:00:00.000Z",
         "name": "reply", "traceName": "support-bot", "level": "DEFAULT", "model": "gpt-4o",
         "usageDetails": {"input": 1200, "output": 300, "input_cached_tokens": 200},
         "inputUsage": 1200, "outputUsage": 300, "totalCost": 0.006}
    o.update(kw)
    return o


class FakeAPI:
    """Pages of observations; optional list of HTTP errors to raise first."""
    def __init__(self, pages, errors=()):
        self.pages, self.errors, self.urls, self.auth = pages, list(errors), [], None

    def __call__(self, req, timeout=None):
        assert timeout == lp.TIMEOUT
        self.urls.append(req.full_url)
        self.auth = req.headers.get("Authorization")
        if self.errors:
            code = self.errors.pop(0)
            raise urllib.error.HTTPError(req.full_url, code, "x", {}, io.BytesIO(b""))
        n = sum("cursor=" in u for u in self.urls if not self.errors)
        page = self.pages[min(n, len(self.pages) - 1)]
        return io.BytesIO(json.dumps(page).encode())


def test_pages_until_no_cursor_even_through_empty_page():
    api = FakeAPI([{"data": [gen(1)], "meta": {"cursor": "c1"}},
                   {"data": [], "meta": {"cursor": "c2"}},          # empty page is not the end
                   {"data": [gen(2)], "meta": {"cursor": None}}])
    obs, truncated = lp.fetch("https://cloud.langfuse.com", "pk-lf-1", "sk-lf-1", "2026-11-01", "2026-11-03",
                              opener=api, sleep=lambda s: None)
    assert [o["id"] for o in obs] == ["o1", "o2"] and not truncated
    first = api.urls[0]
    assert "/api/public/v2/observations?" in first and "type=GENERATION" in first and "limit=1000" in first
    assert "io" not in first.split("fields=")[1].split("&")[0].split("%2C")   # never prompt/answer text
    assert api.auth.startswith("Basic ") and "sk-lf-1" not in api.auth        # encoded, not plain


def test_page_cap_reports_truncation():
    api = FakeAPI([{"data": [gen(1)], "meta": {"cursor": "again"}}])
    obs, truncated = lp.fetch("https://x.example", "p", "s", "2026-11-01", "2026-11-02", opener=api,
                              sleep=lambda s: None, max_pages=3)
    assert truncated and len(obs) == 3


def test_retries_429_and_500_with_backoff_then_gives_up_on_400():
    waits = []
    api = FakeAPI([{"data": [gen(1)], "meta": {}}], errors=[429, 503])
    obs, _ = lp.fetch("https://x.example", "p", "s", "2026-11-01", "2026-11-02", opener=api, sleep=waits.append)
    assert len(obs) == 1 and waits == [1, 2]
    with pytest.raises(RuntimeError, match="HTTP 400"):
        lp.fetch("https://x.example", "p", "s", "2026-11-01", "2026-11-02",
                 opener=FakeAPI([{}], errors=[400]), sleep=waits.append)
    with pytest.raises(PermissionError):
        lp.fetch("https://x.example", "p", "s", "2026-11-01", "2026-11-02",
                 opener=FakeAPI([{}], errors=[401]), sleep=waits.append)


@pytest.mark.parametrize("host", ["http://evil.example", "ftp://x", "", "https://u:p@x.example",
                                  "https://x.example/?a=1", "javascript:alert(1)"])
def test_bad_hosts_refused(host):
    with pytest.raises(ValueError):
        lp.check_host(host)


def test_local_http_allowed_for_ci_demo():
    assert lp.check_host("http://localhost:3000/") == "http://localhost:3000"


def test_missing_keys_and_bad_dates_refused():
    with pytest.raises(ValueError, match="LANGFUSE_PUBLIC_KEY"):
        lp.fetch("https://x.example", "", "s", "2026-11-01", "2026-11-02")
    with pytest.raises(ValueError, match="--from"):
        lp.fetch("https://x.example", "p", "s", "1 Nov", "2026-11-02", opener=FakeAPI([{}]))


def test_to_rows_groups_and_handles_worst_case_data():
    obs = [gen(1), gen(2), gen(3, level="ERROR"),
           gen(4, model="claude-3-5-haiku-20241022", traceName=None, name="=HYPERLINK(\"x\")",
               totalCost=None, costDetails={}),
           gen(5, startTime="not a date"), gen(6, model=""),
           gen(7, traceName="ಕನ್ನಡ 🤖 " + "x" * 300, inputUsage=-5, outputUsage="abc", totalCost="NaN")]
    rows, notes = lp.to_rows(obs)
    by = {(r["feature"][:12], r["model"], r["status"]): r for r in rows}
    ok = by[("support-bot", "gpt-4o", "ok")]
    assert ok["requests"] == 2 and ok["input_tokens"] == 2400 and ok["cached_tokens"] == 400
    assert ok["cost"] == "0.012000"
    assert by[("support-bot", "gpt-4o", "error")]["requests"] == 1
    inj = [r for r in rows if r["model"].startswith("claude")][0]
    assert inj["feature"].startswith("'=") and inj["cost"] == "0.000000"        # no spreadsheet formula
    weird = [r for r in rows if r["feature"].startswith("ಕನ್ನಡ")][0]
    assert len(weird["feature"]) <= 80 and weird["input_tokens"] == 0 and weird["cost"] == "0.000000"
    assert any("no valid startTime" in n for n in notes) and any("no model" in n for n in notes)
    assert any("had no cost" in n for n in notes)


def test_end_to_end_into_audit_report(tmp_path, monkeypatch, capsys):
    pages = [{"data": [gen(i) for i in range(40)] + [gen(99, level="ERROR")], "meta": {}}]
    monkeypatch.setattr(lp.urllib.request, "urlopen", FakeAPI(pages))
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test-secret")
    out = tmp_path / "usage.csv"
    assert lp.main(["--from", "2026-11-01", "--to", "2026-11-03", "--out", str(out), "--synthetic"]) == 0
    printed = capsys.readouterr().out
    assert "41 generations" in printed and "sk-lf-test-secret" not in printed
    rows, problems, synthetic = audit.load(out)
    assert synthetic and not problems and sum(r.requests for r in rows) == 41
    report = tmp_path / "r.md"
    assert audit.main([str(out), "--client", "Demo Co", "--out", str(report)]) == 0
    assert "Demo Co" in report.read_text(encoding="utf-8")


def test_main_fails_cleanly_without_keys(tmp_path, monkeypatch, capsys):
    for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    assert lp.main(["--from", "2026-11-01", "--to", "2026-11-02", "--out", str(tmp_path / "u.csv")]) == 2
    assert "LANGFUSE_PUBLIC_KEY" in capsys.readouterr().err
