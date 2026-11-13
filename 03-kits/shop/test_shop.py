"""A212 kit shop: content, prices, safety and a 390 px tap sweep (light + dark) on every page.

    python3 -m pytest 03-kits/shop/test_shop.py -q
"""
import functools, http.server, importlib.util, json, pathlib, re, subprocess, sys, threading
import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_s = importlib.util.spec_from_file_location("build_shop", HERE / "build_shop.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)
_t = importlib.util.spec_from_file_location("tap", ROOT / "00-hq" / "site" / "tests" / "test_tap_sweep.py")
TAP = importlib.util.module_from_spec(_t); _t.loader.exec_module(TAP)
BASE = "https://kits.example.org"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out, pages = S.build(tmp_path_factory.mktemp("shop") / "dist", BASE)
    return out, pages


def html(site, p):
    return (site[0] / p).read_text(encoding="utf-8")


def test_every_kit_has_a_page(site):
    ids = {d["id"] for d in S.exams()}
    assert {p.split("/")[0] for p in site[1] if p != "index.html"} == ids
    for i in ids:
        assert f'href="/{i}/"' in html(site, "index.html")


def test_pitch_on_every_kit_page(site):
    for p in site[1]:
        h = html(site, p)
        assert "One payment, no expiry" in h
        if p == "index.html":
            continue
        for word in ("Study planner", "Tracker", "Exam-date alerts", "mini-kit", "We do not sell mock tests"):
            assert word in h, (p, word)
        assert "₹199" in h and "₹499" in h and "₹99 a copy, at least 30" in h  # Akhil's prices, 11 Nov 2026


def test_telugu_on_telangana_kits_only(site):
    for d in S.exams():
        h = html(site, f"{d['id']}/index.html")
        assert (S.TE["once"] in h) == ("te" in d["languages"]), d["id"]


def test_mock_links_are_listed_https_and_open_in_new_tab(site):
    for d in S.exams():
        m = S.CFG["mocks"][d["id"]]
        assert m["url"].startswith("https://")
        assert f'href="{m["url"]}" rel="noopener" target="_blank"' in html(site, f"{d['id']}/index.html")


def test_no_dead_buttons_while_links_are_empty(site):
    for p in site[1]:
        h = html(site, p)
        assert not re.search(r'href="(#|)"', h), p
        if not S.CFG["pay_url"]["kit"]:
            assert "Payment page opens soon" in h
        if not S.CFG["telegram_url"]:
            assert "Telegram channel opens soon" in h


def test_pay_and_telegram_links_appear_once_set(monkeypatch, tmp_path):
    monkeypatch.setitem(S.CFG, "pay_url", {"kit": "https://rzp.example/kit", "bundle": "https://rzp.example/b", "institute": "https://rzp.example/i"})
    monkeypatch.setitem(S.CFG, "telegram_url", "https://t.me/example")
    out, _ = S.build(tmp_path / "d", BASE)
    h = (out / "tgpsc-group2" / "index.html").read_text(encoding="utf-8")
    assert 'href="https://rzp.example/kit"' in h and 'href="https://t.me/example"' in h and "opens soon" not in h


def test_no_promises_and_no_script(site):
    for p in site[1]:
        h = html(site, p).lower()
        text = re.sub(r"<style>.*?</style>|<[^>]+>", " ", h, flags=re.S)
        assert not re.search(r"guarantee|100%|sure success|only today|hurry", text), p
        assert "<script>" not in h and "<script " not in h.replace('<script type="application/ld+json">', ""), p
        assert "default-src 'none'" in h


def test_hostile_text_is_escaped():
    assert S._h('<img src=x onerror=alert(1)>"') == "&lt;img src=x onerror=alert(1)&gt;&quot;"


def test_seo_checks_pass(site):
    r = subprocess.run([sys.executable, str(ROOT / "00-hq/site/tests/test_seo.py"), str(site[0]), BASE], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:]


def test_tap_sweep_390_light_and_dark(site):
    from playwright.sync_api import sync_playwright
    h = functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=str(site[0]))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    bad = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for scheme in ("light", "dark"):
                for path in site[1]:
                    pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, color_scheme=scheme)
                    errs = []
                    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                    pg.goto(url + path.removesuffix("index.html"), wait_until="load")
                    wide = pg.evaluate("document.documentElement.scrollWidth")
                    bad += [f"[{scheme}] {path}: {x}" for x in TAP.sweep(pg) + errs]
                    if wide > 390:
                        bad.append(f"[{scheme}] {path}: page is {wide}px wide")
                    pg.close()
            b.close()
    finally:
        srv.shutdown()
    assert not bad, bad[:8]
