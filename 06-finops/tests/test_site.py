"""A192: the built Ledger Peaks site passes the 20 SEO checks and keeps a strict CSP (no inline scripts)."""
import importlib.util, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _build():
    spec = importlib.util.spec_from_file_location("lp_site", ROOT / "06-finops/site/build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build(), mod.SITE


def test_site_passes_seo_checks():
    dist, site = _build()
    r = subprocess.run([sys.executable, str(ROOT / "00-hq/site/tests/test_seo.py"), str(dist), site], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]


def test_no_inline_scripts_and_headers_set():
    dist, _ = _build()
    for page in dist.glob("*.html"):
        assert not re.search(r"<script>(?!\s*$)", page.read_text()), f"inline script left in {page.name}"
        assert "../../" not in page.read_text(), f"repo-relative path left in {page.name}"
        assert " onclick=" not in page.read_text(), f"inline handler left in {page.name}"
    h = (dist / "_headers").read_text()
    for k in ("Strict-Transport-Security", "Content-Security-Policy", "Permissions-Policy", "frame-ancestors 'none'", "X-Content-Type-Options"):
        assert k in h
    assert "Disallow: /api/" in (dist / "robots.txt").read_text()
