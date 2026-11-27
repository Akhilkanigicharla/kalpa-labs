"""A339 check: the private trade dashboard at 390 px, light + dark, tapped like a real user.

Reuses the Kalpa tap sweep (00-hq/site/tests/test_tap_sweep.py: nothing covered, taps >= 44 px, fields on screen),
then taps the real controls: candle size, exits, a trade row, a month, filters down to the empty state and back,
theme button. Also checks no sideways scroll, no JS errors, the "not real money" notice, and the TradingView
attribution. Screenshots: /tmp/dash-<scheme>.png (full page) and /tmp/dash-<scheme>-trade.png (selected trade).

Run:  python3 07-trading/dashboard/build.py && python3 07-trading/dashboard/test_dashboard.py
"""
import functools, http.server, json, pathlib, sys, threading
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "00-hq" / "site" / "tests"))
import test_tap_sweep as tap  # noqa: E402

DATA = json.loads((HERE / "data.json").read_text())


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(HERE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/trade-dashboard.html"


def check(scheme, pg, url, bad):
    def need(ok, msg):
        if not ok:
            bad.append(f"[{scheme}] {msg}")
    errs = []
    pg.on("pageerror", lambda ex: errs.append(str(ex)[:120]))
    pg.goto(url, wait_until="load", timeout=60000)
    pg.wait_for_selector("#chart canvas", timeout=15000)
    pg.wait_for_timeout(800)
    need(pg.locator("#skel").count() == 0, "skeleton still showing after the chart loaded")
    need(pg.is_hidden("#chartErr"), "chart error box is showing")
    need("not real money" in pg.inner_text(".notice").lower(), "missing the 'not real money' notice")
    need("not investment advice" in pg.inner_text("body").lower(), "missing 'not investment advice'")
    need(pg.locator('a[href="https://www.tradingview.com/"]').count() >= 1, "missing TradingView attribution link")
    need("TradingView, Inc." in pg.inner_text("footer"), "missing TradingView NOTICE text")
    need(pg.evaluate("document.documentElement.scrollWidth") <= 390, "page scrolls sideways")
    s = DATA["stats"]
    kp = pg.inner_text("#kpis")
    need(f"${s['net_usd']:,}" in kp and f"{s['trades']:,}" in kp and f"{s['win_pct']}%" in kp, f"key numbers wrong: {kp[:80]!r}")
    need(pg.locator(".mrow").count() == len(DATA["months"]), "month rows missing")
    need(pg.locator(".trow").count() == 30, "first page of trades should show 30 rows")
    summ = pg.inner_text("#summary")
    need(f"{len(DATA['trades']):,} trades" in summ and f"{s['win_pct']}% wins" in summ and f"${s['net_usd']:,}" in summ,
         f"trade-list summary disagrees with the key numbers: {summ!r}")
    dark = pg.evaluate("matchMedia('(prefers-color-scheme: dark)').matches")
    need(dark == (scheme == "dark"), "colour scheme not applied")

    for f in tap.sweep(pg):                                  # the standard Kalpa tap sweep
        bad.append(f"[{scheme}] {f}")

    pg.click("#tf button[data-tf='3600']"); pg.wait_for_timeout(200)
    need(pg.get_attribute("#tf button[data-tf='3600']", "aria-pressed") == "true", "1h button did not switch")
    pg.click("#exitsBtn")
    need(pg.inner_text("#exitsBtn") == "Exits hidden", "exits toggle did not work")
    pg.click("#exitsBtn")
    pg.click("#more"); pg.wait_for_timeout(100)
    need(pg.locator(".trow").count() == 60, "'Show 30 more' did not add rows")

    pg.locator(".trow").nth(3).click(); pg.wait_for_timeout(600)
    need(pg.is_visible("#sel"), "tapping a trade did not open the selected-trade card")
    need("Entry" in pg.inner_text("#selDl"), "selected-trade card empty")
    pg.screenshot(path=f"/tmp/dash-{scheme}-trade.png")
    pg.click("#clearSel")
    need(pg.is_hidden("#sel"), "Clear did not close the selected trade")

    m = DATA["months"][5]
    pg.locator(".mrow").nth(5).click(); pg.wait_for_timeout(200)
    need(f"{m['trades']:,} trades" in pg.inner_text("#summary"), f"month filter: expected {m['trades']} trades")
    in_month = {DATA["strategies"][t[4]] for t in DATA["trades"]
                if datetime.fromtimestamp(t[2], timezone.utc).strftime("%Y-%m") == m["month"]}
    lonely = next(st for st in DATA["strategies"] if st not in in_month)     # a strategy with no trades that month
    pg.select_option("#fStrat", lonely); pg.wait_for_timeout(200)
    need(pg.locator(".empty").first.is_visible() and "No trades match" in pg.inner_text("#trades"), "empty state missing")
    pg.click("#trades .empty button"); pg.wait_for_timeout(200)
    need(f"{len(DATA['trades']):,} trades" in pg.inner_text("#summary"), "'Clear filters' did not reset")
    need("Not connected yet" in pg.inner_text("#demoBox"), "demo placeholder missing")

    pg.click("#theme"); pg.wait_for_timeout(100)               # auto -> light
    need(pg.get_attribute("html", "data-theme") == "light", "theme button did not switch to light")
    pg.click("#theme"); pg.click("#theme")                       # dark -> auto again
    need(pg.get_attribute("html", "data-theme") is None, "theme button did not cycle back to auto")
    pg.evaluate("localStorage.clear()")
    pg.goto(url, wait_until="load"); pg.wait_for_selector("#chart canvas"); pg.wait_for_timeout(600)
    pg.screenshot(path=f"/tmp/dash-{scheme}.png", full_page=True)
    bad += [f"[{scheme}] js error: {e}" for e in errs]


def main():
    srv, url = serve()
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme in ("light", "dark"):
            pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, color_scheme=scheme)
            check(scheme, pg, url, bad)
            pg.close()
        b.close()
    srv.shutdown()
    for x in bad:
        print("FAIL", x)
    print("PASS dashboard 390 px light + dark" if not bad else f"{len(bad)} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
