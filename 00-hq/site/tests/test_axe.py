"""axe accessibility scan (A331, K160): 390 px, light + dark, fails on serious/critical.

Run:  AXE_JS=/path/to/axe.min.js python3 00-hq/site/tests/test_axe.py URL [URL ...]
axe-core (MPL-2.0) is used unmodified as a test tool only, never shipped:
  npm i --prefix /tmp/axe axe-core@4.10.3  ->  AXE_JS=/tmp/axe/node_modules/axe-core/axe.min.js
Optional TAP_CLICKS='sel1;sel2' taps those selectors in order and scans after each tap,
so screens behind a button get checked too.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BAD = ('serious', 'critical')


def scan(pg, label):
    res = pg.evaluate("async () => (await axe.run(document, {resultTypes: ['violations']})).violations"
                      ".map(v => ({id: v.id, impact: v.impact, n: v.nodes.length, t: v.nodes[0].target.join(' ')}))")
    bad = [v for v in res if v['impact'] in BAD]
    for v in res:
        print(f"  {'FAIL' if v in bad else 'note'} {label}: {v['id']} ({v['impact']}, {v['n']} nodes) e.g. {v['t'][:70]}")
    return len(bad)


def main(urls):
    axe = open(os.environ['AXE_JS'], encoding='utf-8').read()
    clicks = [c for c in os.environ.get('TAP_CLICKS', '').split(';') if c]
    fails = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for url in urls:
            for scheme in ('light', 'dark'):
                pg = b.new_page(viewport={'width': 390, 'height': 844}, color_scheme=scheme, bypass_csp=True)
                pg.goto(url, wait_until='networkidle')
                pg.add_script_tag(content=axe)
                fails += scan(pg, f'{url} {scheme}')
                for sel in clicks:
                    loc = pg.locator(sel).first
                    if loc.count() and loc.is_visible():
                        loc.click()
                        pg.wait_for_timeout(300)
                        fails += scan(pg, f'{url} {scheme} after {sel}')
                pg.close()
        b.close()
    print('PASS axe (0 serious/critical)' if not fails else f'FAIL axe: {fails} serious/critical rules')
    return 1 if fails else 0


if __name__ == '__main__':
    if len(sys.argv) < 2 or not os.environ.get('AXE_JS'):
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
