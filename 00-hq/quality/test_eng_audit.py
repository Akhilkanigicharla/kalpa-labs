"""Tests for eng_audit.py: each check on small fixture repos in a temp folder (no network)."""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eng_audit as E  # noqa: E402

FULL_HEADERS = """[[headers]]
  for = "/*"
  [headers.values]
    Content-Security-Policy = "default-src 'self'; frame-ancestors 'none'"
    Strict-Transport-Security = "max-age=31536000"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
"""


def repo(tmp_path, files):
    for rel, body in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return tmp_path


def run(tmp_path, files):
    return E.audit(repo(tmp_path, files))


def rules(findings, rule=None, waived=False):
    return [f for f in findings if (rule is None or f.rule == rule) and bool(f.waived) == waived]


def jwt(role):
    seg = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")  # noqa: E731
    return f"{seg({'alg': 'HS256'})}.{seg({'iss': 'supabase', 'role': role})}.{'Zk3' * 10}"


# ------------------------------------------------------------- timeouts
def test_js_fetch_without_timeout_in_server_code(tmp_path):
    fs = run(tmp_path, {
        "01-botbhai/core/functions/a.js": 'const r = await fetch(url, {\n  method: "POST",\n  body: x,\n});\n',
        "01-botbhai/core/functions/b.js": 'const r = await fetch(url, {\n  method: "POST",\n  signal: AbortSignal.timeout(8000),\n});\n',
        "01-botbhai/web/app.js": "fetch('data.json').then(r => r.json());\n",
    })
    hits = rules(fs, "NET-TIMEOUT-JS")
    assert [(f.file, f.line, f.severity) for f in hits] == [("01-botbhai/core/functions/a.js", 1, "HIGH")]


def test_python_timeouts(tmp_path):
    fs = run(tmp_path, {"07-trading/src/net.py": (
        "import urllib.request, requests\n"
        "urllib.request.urlopen(req)\n"
        "urllib.request.urlopen(req, timeout=10)\n"
        "requests.get(u)\n"
        "requests.get(u, timeout=5)\n"
        "s = {'a': 1}\nprint(s.get('a'))\n"
        "sess = requests.Session()\nsess.post(u)\n")})
    assert sorted(f.line for f in rules(fs, "NET-TIMEOUT-PY")) == [2, 4, 9]


def test_inline_waiver_needs_a_reason(tmp_path):
    fs = run(tmp_path, {"06-finops/src/x.py": (
        "import urllib.request\n"
        "urllib.request.urlopen(r)  # eng-audit: ok local file:// url only\n"
        "urllib.request.urlopen(r)  # eng-audit: ok\n")})
    assert [f.line for f in rules(fs, "NET-TIMEOUT-PY", waived=True)] == [2]
    assert [f.line for f in rules(fs, "NET-TIMEOUT-PY")] == [3]


# ------------------------------------------------------------- secrets
def test_secret_patterns(tmp_path):
    aws = "AKIA" + "Q3EGRNC7XLZ5TB2M"
    fs = run(tmp_path, {
        "05-deals/a.js": f'const k = "{aws}";\n',
        "05-deals/b.js": f'const anon = "{jwt("anon")}";\nconst svc = "{jwt("service_role")}";\n',
        "05-deals/c.js": 'const apiKey = "your-api-key-goes-here-123";\nconst TOKENS = "--bg:#fff;--fg:#000;--x:#123456";\n',
        "05-deals/d.py": 'API_KEY = "' + "q8Zt4Lm2" + "Vx9Rk7Pw3Hn5" + '"\n',  # split so gitleaks stays quiet
    })
    got = sorted((f.file, f.severity, f.rule) for f in rules(fs) if f.rule.startswith("SECRET"))
    assert got == [("05-deals/a.js", "CRITICAL", "SECRET-aws-key"),
                   ("05-deals/b.js", "CRITICAL", "SECRET-supabase-service-role"),
                   ("05-deals/b.js", "INFO", "SECRET-supabase-anon"),
                   ("05-deals/d.py", "HIGH", "SECRET-generic")]
    assert aws not in json.dumps([f.message for f in fs])  # masked in the report


# ------------------------------------------------------------- injection sinks
def test_html_sinks(tmp_path):
    fs = run(tmp_path, {"02-jobcard/web/app.js": (
        "el.innerHTML = `<b>${name}</b>`;\n"
        "el.innerHTML = `<b>${esc(name)}</b>`;\n"
        "const ICON = `<svg></svg>`;\nel.innerHTML = ICON;\n"
        "el.innerHTML = tab === 'a' ? viewA(v) : viewB(v);\n"
        "el.innerHTML = userText;\n")})
    assert [f.line for f in rules(fs, "XSS-HTML-SINK")] == [1, 6]


def test_eval_sql_and_shell(tmp_path):
    fs = run(tmp_path, {
        "00-hq/tools/a.py": (
            "import subprocess, os\n"
            "subprocess.run(f'ls {d}', shell=True)\n"
            "subprocess.run(['ls', d])\n"
            "cur.execute(f\"select * from t where id = {i}\")\n"
            "cur.execute('select * from t where id = %s', (i,))\n"
            "eval(user)\n"),
        "00-hq/tools/b.js": "db.query(`select * from t where id = ${id}`);\nconst f = new Function(src);\nexecSync(`rm ${p}`);\n",
    })
    assert [(f.file, f.line, f.severity) for f in rules(fs, "CMD-INJECTION")] == [("00-hq/tools/a.py", 2, "CRITICAL"), ("00-hq/tools/b.js", 3, "HIGH")]
    assert sorted((f.file, f.line) for f in rules(fs, "SQL-STRING")) == [("00-hq/tools/a.py", 4), ("00-hq/tools/b.js", 1)]
    assert sorted((f.file, f.line) for f in rules(fs, "CODE-EVAL")) == [("00-hq/tools/a.py", 6), ("00-hq/tools/b.js", 2)]


def test_cookie_flags_and_tests_are_skipped(tmp_path):
    fs = run(tmp_path, {
        "01-botbhai/core/functions/login.js": (
            'return { headers: { "Set-Cookie": `s=${t}; Path=/` } };\n'
            'return { headers: { "Set-Cookie": `s=${t}; Path=/; HttpOnly; Secure; SameSite=Lax` } };\n'),
        "01-botbhai/core/functions/login.test.js": "eval(x); fetch(u);\n",
    })
    assert [f.line for f in rules(fs, "COOKIE-FLAGS")] == [1]
    assert not [f for f in fs if f.file.endswith(".test.js")]


# ------------------------------------------------------------- python hygiene
def test_naive_datetime_and_encoding(tmp_path):
    fs = run(tmp_path, {"07-trading/src/t.py": (
        "from datetime import datetime, timezone\nfrom pathlib import Path\n"
        "a = datetime.now()\n"
        "b = datetime.now(timezone.utc)\n"
        "c = datetime.utcnow()\n"
        "open('x.txt').read()\n"
        "open('x.bin', 'rb').read()\n"
        "open('x.txt', 'w', encoding='utf-8')\n"
        "Path('x').read_text()\n"
        "(Path('d') / 'f.csv').open(newline='')\n")})
    assert [f.line for f in rules(fs, "NAIVE-DATETIME")] == [3, 5]
    assert [f.line for f in rules(fs, "TEXT-ENCODING")] == [6, 9, 10]


# ------------------------------------------------------------- headers, SQL, CI
def test_security_headers(tmp_path):
    fs = run(tmp_path, {
        "01-botbhai/site/netlify.toml": '[build]\n  publish = "web"\n',
        "02-jobcard/netlify.toml": FULL_HEADERS,
        "05-deals/site/astro.config.mjs": "export default {};\n",
        "05-deals/site/public/_headers": "/*\n  X-Content-Type-Options: nosniff\n",
    })
    bot = {f.rule for f in fs if f.file == "01-botbhai/site/netlify.toml"}
    assert bot == {"HDR-CSP", "HDR-HSTS", "HDR-FRAME", "HDR-NOSNIFF", "HDR-REFERRER"}
    assert not [f for f in fs if f.file == "02-jobcard/netlify.toml"]
    deals = {f.rule for f in fs if f.world == "b5 05-deals" and f.rule.startswith("HDR")}
    assert "HDR-CSP" in deals and "HDR-NOSNIFF" not in deals
    assert [f.severity for f in fs if f.rule == "HDR-CSP" and f.world == "b1 01-botbhai"] == ["HIGH"]


def test_file_level_waiver(tmp_path):
    fs = run(tmp_path, {"00-hq/site/netlify.toml": FULL_HEADERS.replace('    Strict-Transport-Security = "max-age=31536000"\n', "")
                        + "# eng-audit: ok HDR-HSTS host sends HSTS itself\n"})
    assert [f.rule for f in rules(fs, waived=True)] == ["HDR-HSTS"]


def test_rls(tmp_path):
    fs = run(tmp_path, {
        "06-finops/db/0001.sql": (
            "create table if not exists public.a (id int);\n"
            "create table b (id int);\n"
            "create table private.c (id int);\n"
            "-- create table d (id int);\n"
            "alter table public.a enable row level security;\n"
            "create or replace function f() returns int language sql security definer as $$ select 1 $$;\n"
            "create or replace function g() returns int language sql security definer set search_path = public as $$ select 1 $$;\n"
            "create view v as select * from a;\n"),
        "06-finops/db/test.sql": "create table t (id int);\n",
    })
    assert [(f.line, f.severity) for f in rules(fs, "RLS-MISSING")] == [(2, "CRITICAL")]
    assert [f.message.split()[1] for f in rules(fs, "DEFINER-SEARCH-PATH")] == ["f"]
    assert len(rules(fs, "VIEW-DEFINER")) == 1


def test_rls_enabled_in_a_later_migration(tmp_path):
    fs = run(tmp_path, {"06-finops/db/0001.sql": "create table public.k (id int);\n",
                        "06-finops/db/0002.sql": "alter table public.k enable row level security;\n"})
    assert not rules(fs, "RLS-MISSING")


def test_workflows(tmp_path):
    fs = run(tmp_path, {".github/workflows/a.yml": (
        "name: a\non: push\njobs:\n"
        "  one:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: someone/tool@v1\n"
        "      - uses: someone/tool@0123456789abcdef0123456789abcdef01234567\n"
        "      - run: echo \"${{ github.event.issue.title }}\"\n"
        "  two:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n      - run: true\n")})
    assert sorted((f.rule, f.line) for f in fs if f.rule.startswith("CI-")) == [
        ("CI-PERMISSIONS", 1), ("CI-SCRIPT-INJECTION", 10), ("CI-TIMEOUT", 4), ("CI-UNPINNED-ACTION", 8)]


# ------------------------------------------------------------- world level + output
def test_world_level_checks_and_skips(tmp_path):
    fs = run(tmp_path, {
        "04-extensions/src/a.js": "const x = process.env.STORE_KEY;\n",
        "03-kits/engine/k.py": "import os\nK = os.environ['KIT_TOKEN']\n",
        "03-kits/engine/tests/test_k.py": "def test_k():\n    assert True\n",
        "03-kits/.env.example": "KIT_TOKEN=dummy\n",
        "03-kits/node_modules/pkg/index.js": "eval(x); fetch(u);\n",
    })
    assert [f.world for f in rules(fs, "TESTS-MISSING") if f.world.startswith("b")] == [
        "b1 01-botbhai", "b2 02-jobcard", "b4 04-extensions", "b5 05-deals", "b6 06-finops", "b7 07-trading"]
    env = rules(fs, "ENV-EXAMPLE")
    assert [f.world for f in env] == ["b4 04-extensions"] and "STORE_KEY" in env[0].message
    assert not [f for f in fs if "node_modules" in f.file]
    assert [f.world for f in rules(fs, "TESTS-NOT-IN-CI")] == ["b3 03-kits"]


def test_report_and_strict_exit(tmp_path):
    root = repo(tmp_path / "r", {"06-finops/db/s.sql": "create table x (id int);\n"})
    md, js = tmp_path / "r.md", tmp_path / "r.json"
    args = ["--root", str(root), "--md", str(md), "--json", str(js)]
    assert E.main(args) == 0
    assert E.main(args + ["--strict"]) == 1
    text = md.read_text(encoding="utf-8")
    assert "| b6 06-finops | 1 |" in text and "RLS-MISSING" in text
    assert json.loads(js.read_text(encoding="utf-8"))["counts"]["b6 06-finops"]["CRITICAL"] == 1
    (root / "06-finops/db/s.sql").write_text("create table x (id int);\nalter table x enable row level security;\n", encoding="utf-8")
    assert E.main(args + ["--strict"]) == 0
