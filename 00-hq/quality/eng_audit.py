#!/usr/bin/env python3
"""Kalpa engineering audit: a stdlib-only static scan of the whole repo.

It checks the items of ENGINEERING-CHECKLIST.md that a scan can honestly detect
(timeouts, secrets, injection sinks, security headers, RLS, CI hygiene, tests,
.env.example, time zones, text encoding) and reports them per world.

    python3 00-hq/quality/eng_audit.py            # writes report.md + report.json here
    python3 00-hq/quality/eng_audit.py --strict   # exit 1 if any CRITICAL is left

Waive a finding on its line with a reason:   x = foo()  # eng-audit: ok <reason>
Waive a file-level finding (e.g. a missing header) anywhere in that file:
    # eng-audit: ok <rule-id> <reason>
"""
from __future__ import annotations

import argparse
import ast
import base64
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "INFO")
WORLDS = {
    "00-hq": "00-hq", ".github": "00-hq", "docs": "00-hq",
    "01-botbhai": "b1 01-botbhai", "02-jobcard": "b2 02-jobcard", "03-kits": "b3 03-kits",
    "04-extensions": "b4 04-extensions", "05-deals": "b5 05-deals", "06-finops": "b6 06-finops",
    "07-trading": "b7 07-trading", "08-microapps": "b8 08-microapps",
}
SKIP_DIRS = {"node_modules", "vendor", "dist", ".git", "generated", "archive", ".pytest_cache",
             "__pycache__", ".claude", ".expo", ".astro", "coverage", "build", ".venv", "venv"}
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
TEXT_EXT = CODE_EXT | {".json", ".yml", ".yaml", ".toml", ".sh", ".html", ".md", ".sql", ".env", ".txt", ".astro", ".css"}
SKIP_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "skills-lock.json"}
MAX_BYTES = 1_000_000
WAIVER = re.compile(r"eng-audit:\s*ok\s+(\S.{2,})", re.I)


@dataclass
class Finding:
    world: str
    severity: str
    rule: str
    file: str
    line: int
    message: str
    fix: str = ""
    waived: str = ""


@dataclass
class Ctx:
    root: Path
    findings: list = field(default_factory=list)

    def add(self, rel, line, severity, rule, message, fix="", lines=None, text=None):
        waived = ""
        if lines and 1 <= line <= len(lines):
            m = WAIVER.search(lines[line - 1])
            if m:
                waived = m.group(1).strip()
        if not waived and text is not None:  # file-level waiver naming the rule
            m = re.search(r"eng-audit:\s*ok\s+" + re.escape(rule) + r"\b\s*(.*)", text, re.I)
            if m:
                waived = (m.group(1).strip() or rule)
        self.findings.append(Finding(world_of(rel), severity, rule, rel, line, message, fix, waived))


# ---------------------------------------------------------------- helpers
def world_of(rel: str) -> str:
    return WORLDS.get(rel.split("/", 1)[0], "00-hq")


def is_test(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    parts = set(rel.split("/")[:-1])
    return bool(re.match(r"(test_.*\.py|.*_test\.py|conftest\.py|.*\.(test|spec|e2e|fuzz)\.[cm]?[jt]sx?|test[-_].*\.(sql|sh)|test\.(sql|sh))$", name)
                or parts & {"tests", "test", "__tests__", "e2e", "qa", "fixtures"})


BROWSER_HINTS = ("/web/", "/apps/", "/public/", "/components/", "/pages/", "/layouts/", "/styles/")


def is_browser_js(rel: str, root: Path | None = None) -> bool:
    name = rel.rsplit("/", 1)[-1]
    if root is not None and "/functions/" not in rel and (root / rel).parent.joinpath("index.html").exists():
        return True  # a static site's own script
    if "/functions/" in rel or "/netlify/" in rel or "/api/" in rel:
        return False
    if name.startswith("sw") or name in {"widget.js"}:
        return True
    if rel.startswith("04-extensions/src/") or rel.startswith("02-jobcard/src/"):
        return True  # Chrome extension and Expo app run on the user's device
    return any(h in "/" + rel for h in BROWSER_HINTS)


def walk(root: Path):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_dir():
                if p.name not in SKIP_DIRS and not p.is_symlink():
                    stack.append(p)
            elif p.is_file():
                yield p


def read(p: Path):
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def mask(s: str) -> str:
    return s[:4] + "…" + f"({len(s)} chars)"


def entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


PLACEHOLDER = re.compile(r"x{4,}|your|example|changeme|dummy|placeholder|fake|sample|redacted|<|\$\{|\{\{|\.\.\.|process\.env|os\.environ|test|mock", re.I)


# ---------------------------------------------------------------- secrets
KNOWN_SECRETS = [
    ("aws-key", "CRITICAL", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", "CRITICAL", re.compile(r"\b(ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{50,}")),
    ("openai-style-key", "CRITICAL", re.compile(r"\bsk-(?:or-v1-|proj-|ant-)?[A-Za-z0-9_\-]{32,}")),
    ("groq-key", "CRITICAL", re.compile(r"\bgsk_[A-Za-z0-9]{40,}")),
    ("google-api-key", "CRITICAL", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("slack-token", "CRITICAL", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", "CRITICAL", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("huggingface-token", "CRITICAL", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b")),
    ("telegram-bot-token", "CRITICAL", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b")),
    ("meta-access-token", "CRITICAL", re.compile(r"\bEAA[A-Za-z0-9]{80,}")),
    ("razorpay-live-key", "HIGH", re.compile(r"\brzp_live_[A-Za-z0-9]{10,}")),
]
JWT = re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.(eyJ[A-Za-z0-9_\-]{10,})\.[A-Za-z0-9_\-]{10,}")
GENERIC = re.compile(r"""(?i)\b[\w-]*(secret|token|api[_-]?key|password|passwd|private[_-]?key)[\w-]*["']?\s*[:=]\s*["']([^"'\s]{16,})["']""")


def check_secrets(ctx: Ctx, rel: str, text: str, lines: list):
    test = is_test(rel)
    for i, ln in enumerate(lines, 1):
        if len(ln) > 2000:
            continue
        for rule, sev, rx in KNOWN_SECRETS:
            for m in rx.finditer(ln):
                if PLACEHOLDER.search(m.group(0)):
                    continue
                ctx.add(rel, i, sev, "SECRET-" + rule, f"Looks like a real {rule}: {mask(m.group(0))}",
                        "Remove it, rotate the key at the provider, keep it in GitHub/Netlify/Supabase secrets.", lines)
        for m in JWT.finditer(ln):
            seg = m.group(1)
            try:
                payload = json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
            except (ValueError, UnicodeDecodeError):
                continue
            role = payload.get("role", "") if isinstance(payload, dict) else ""
            if role == "service_role":
                ctx.add(rel, i, "CRITICAL", "SECRET-supabase-service-role", "Supabase service_role key in the repo (bypasses RLS)",
                        "Rotate the JWT secret in Supabase and keep the key only in server secrets.", lines)
            elif role == "anon":
                ctx.add(rel, i, "INFO", "SECRET-supabase-anon", "Supabase anon key in the repo (public by design; safe only with RLS on every table)", "", lines)
            elif not test:
                ctx.add(rel, i, "HIGH", "SECRET-jwt", "A signed token (JWT) is committed", "Remove it; tokens belong in secrets.", lines)
        if test or rel.endswith(".md"):
            continue
        for m in GENERIC.finditer(ln):
            val = m.group(2)
            if PLACEHOLDER.search(val) or re.search(r"[;#:,( ]", val) or not re.search(r"\d", val) or not re.search(r"[A-Za-z]", val) or entropy(val) < 3.5:
                continue
            if re.fullmatch(r"[a-z0-9_.\-/]+", val) and "_" in val:  # an identifier or path, not a key
                continue
            ctx.add(rel, i, "HIGH", "SECRET-generic", f"Hardcoded {m.group(1).lower()} value {mask(val)}",
                    "Read it from an environment variable / secret instead.", lines)


# ---------------------------------------------------------------- JavaScript / TypeScript
def _call_span(lines, i, start_col, max_lines=40):
    """Text of a call from the '(' at lines[i][start_col:] to its matching ')' (rough, string-unaware)."""
    depth, out = 0, []
    for j in range(i, min(len(lines), i + max_lines)):
        seg = lines[j][start_col:] if j == i else lines[j]
        for k, ch in enumerate(seg):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    out.append(seg[:k + 1])
                    return "\n".join(out)
        out.append(seg)
    return "\n".join(out)


def _statement(lines, i, max_lines=15):
    out = []
    for j in range(i, min(len(lines), i + max_lines)):
        out.append(lines[j])
        if lines[j].rstrip().endswith(";"):
            break
    return "\n".join(out)


SAFE_INTERP = re.compile(r"^\s*(esc|escape|escapeHtml|escHtml|sanitize|DOMPurify\.sanitize|L\.enc|enc|encodeURIComponent|Number|String\(Number|\d)")
BARE = re.compile(r"^\s*[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*|\[[^\]]*\])*\s*$")


def _literal_const(name: str, text: str) -> bool:
    m = re.search(r"\bconst\s+" + re.escape(name) + r"\s*=\s*([`'\"])", text)
    if not m:
        return False
    end = text.find(m.group(1), m.end())
    return end > 0 and "${" not in text[m.end():end]


def _interpolations(s: str):
    out, i = [], 0
    while True:
        i = s.find("${", i)
        if i < 0:
            return out
        depth, j = 1, i + 2
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        out.append(s[i + 2:j - 1])
        i = j


# reel item 04: "Email not found" tells an attacker which accounts exist
_USER_ENUM = re.compile(r"(?i)[`'\"][^`'\"]*\b(email|user|account|phone|number|mobile)\b[^`'\"]{0,20}"
                        r"\b(not found|does ?n[o']t exist|not registered|no such)\b[^`'\"]*[`'\"]")


def check_js(ctx: Ctx, rel: str, text: str, lines: list):
    if rel.endswith(".min.js") or is_test(rel):
        return
    browser = is_browser_js(rel, ctx.root)
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith(("//", "*", "/*")):
            continue
        # network timeouts (server code only: a hung call burns the function's whole time budget)
        if not browser:
            for m in re.finditer(r"(?<![\w.$])fetch\(", ln):
                if re.search(r"(async\s+|function\s+)fetch\($", ln[:m.end()]):
                    continue
                call = _call_span(lines, i - 1, m.end() - 1)
                if "signal" not in call:
                    ctx.add(rel, i, "HIGH", "NET-TIMEOUT-JS", "fetch() without a timeout in server code",
                            "Add `signal: AbortSignal.timeout(10000)` (or less than the host's function limit).", lines)
                if re.match(r"\(\s*[`'\"]http://(?!localhost|127\.0\.0\.1)", call):
                    ctx.add(rel, i, "MEDIUM", "PLAIN-HTTP", "fetch() over plain http://", "Use https://.", lines)
        if re.search(r"(?<![\w.$])eval\(|\bnew Function\(", ln):
            ctx.add(rel, i, "HIGH", "CODE-EVAL", "eval / new Function runs text as code", "Parse data instead (JSON.parse, a lookup table).", lines)
        m = re.search(r"\b(innerHTML|outerHTML)\s*\+?=\s*|insertAdjacentHTML\(|document\.write\(|dangerouslySetInnerHTML=\{\{\s*__html:\s*", ln)
        if m:
            rhs = _statement(lines, i - 1)[m.end():].split(";")[0]
            risky = []
            head = rhs.strip()
            if head and head[0] not in "`'\"":
                ident = re.match(r"[A-Za-z_$][\w$.]*", head)
                if ident and BARE.match(ident.group(0)) and not head[len(ident.group(0)):].strip() \
                        and not _literal_const(ident.group(0).split(".")[0], text):
                    risky.append(ident.group(0))
            for expr in _interpolations(rhs):
                if BARE.match(expr) and not SAFE_INTERP.match(expr) and not _literal_const(expr.strip(), text):
                    risky.append(expr.strip())
            if risky:
                ctx.add(rel, i, "MEDIUM", "XSS-HTML-SINK", f"HTML built from unescaped value(s): {', '.join(sorted(set(risky))[:4])}",
                        "Wrap each value in esc(...) or set textContent instead.", lines)
        if re.search(r"(?i)\b(query|execute|raw|unsafe|exec)\s*\(\s*`[^`]*\b(select|insert|update|delete|drop)\b[^`]*\$\{", ln) \
                or re.search(r"(?i)[\"'`]\s*(select|insert into|update|delete from)\b[^\"'`]*[\"'`]\s*\+\s*\w", ln):
            ctx.add(rel, i, "HIGH", "SQL-STRING", "SQL text built from variables", "Use parameters ($1, ?) or the Supabase client filters.", lines)
        if re.search(r"\b(exec|execSync)\(\s*(`[^`]*\$\{|[^)'\"`]*\+)", ln) or re.search(r"\bshell:\s*true\b", ln):
            ctx.add(rel, i, "HIGH", "CMD-INJECTION", "Shell command built from variables / shell: true", "Use execFile/spawn with an argument array and no shell.", lines)
        if not browser and re.search(r"\bfs\.(readFile|readFileSync|createReadStream|writeFile|writeFileSync|unlink|readdir)\w*\(", ln) \
                and re.search(r"\b(event|req|request)\.|queryStringParameters|searchParams|params\b|body\b", ln):
            ctx.add(rel, i, "HIGH", "PATH-TRAVERSAL", "File path comes from the request", "Allow-list file names; never join raw input into a path.", lines)
        if re.search(r"\brejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED", ln):
            ctx.add(rel, i, "HIGH", "TLS-OFF", "TLS certificate checks switched off", "Remove it; fix the certificate instead.", lines)
        if re.search(r"(?i)[\"']set-cookie[\"']\s*:|\bcookies\.set\(|\bres\.cookie\(|\bserialize\(", ln):
            stmt = _statement(lines, i - 1)
            missing = [f for f in ("HttpOnly", "Secure", "SameSite") if f.lower() not in stmt.lower()]
            if missing:
                ctx.add(rel, i, "HIGH", "COOKIE-FLAGS", f"Cookie set without {', '.join(missing)}", "Add HttpOnly; Secure; SameSite=Lax (or Strict).", lines)
        if re.search(r"\bdocument\.cookie\s*=", ln):
            ctx.add(rel, i, "MEDIUM", "COOKIE-JS", "Cookie written from JavaScript (cannot be HttpOnly)", "Never keep login tokens here.", lines)
        if re.search(r"console\.(log|info|warn|error|debug)\(.*process\.env\.\w*(KEY|SECRET|TOKEN|PASSWORD)", ln):
            ctx.add(rel, i, "HIGH", "LOG-SECRET", "A secret is written to the logs", "Log only that it is set, never its value.", lines)
        if not browser and re.search(r"[\"']Access-Control-Allow-Origin[\"']\s*:\s*[\"']\*[\"']", ln):
            ctx.add(rel, i, "INFO", "CORS-ANY", "Any website may call this endpoint (CORS *)", "Fine for public endpoints only; owner endpoints must not use *.", lines)
        if re.search(r"Math\.random\(", ln) and re.search(r"(?i)\b(token|secret|otp|password|nonce|api_?key)\b", ln):
            ctx.add(rel, i, "MEDIUM", "WEAK-RANDOM", "Math.random used for a security value", "Use crypto.randomUUID() / crypto.getRandomValues().", lines)
        if not browser and re.search(r"[\"']Location[\"']\s*:\s*[^,}]*(query|searchParams|queryStringParameters|req\.|event\.)", ln):
            ctx.add(rel, i, "MEDIUM", "OPEN-REDIRECT", "Redirect target comes from the request", "Allow-list redirect targets (same site only).", lines)
        # login safety (design_with_vinod "20 vibe-coded login mistakes", 13 Nov 2026)
        if re.search(r"(?i)(local|session)Storage\.setItem\(\s*[`'\"][^`'\"]*(token|jwt|session|auth|refresh|secret|key)", ln):
            ctx.add(rel, i, "HIGH", "AUTH-TOKEN-STORAGE", "Login token kept in localStorage/sessionStorage (any XSS can steal it)",
                    "Keep it in an HttpOnly cookie, or let the Supabase client manage the session.", lines)
        if not browser and re.search(r"\bjwt\.decode\(", ln) and not re.search(r"\bjwt\.verify\(", text):
            ctx.add(rel, i, "HIGH", "JWT-NO-VERIFY", "JWT decoded but never verified", "Use jwt.verify(token, key) (or Supabase auth.getUser).", lines)
        if re.search(r"\bjwt\.(sign|verify)\([^,]+,\s*[`'\"][^`'\"]{0,40}[`'\"]", ln):
            ctx.add(rel, i, "CRITICAL", "JWT-LITERAL-SECRET", "JWT signed/verified with a secret written in the code",
                    "Read a long random secret from an env var.", lines)
        if not browser and re.search(r"(?i)\b(body|params|query|payload|data)\s*(\.|\[\s*['\"])\s*(is_?admin|role|is_?staff|is_?owner)\b", ln):
            ctx.add(rel, i, "HIGH", "CLIENT-ROLE-TRUST", "Role/admin flag read from the request",
                    "Take the role from the verified session or the database, never from the browser.", lines)
        if not browser and re.search(r"(?i)(json\(|JSON\.stringify\(|body\s*:).*\b(otp|otp_?code|verification_?code|reset_?token)\b", ln):
            ctx.add(rel, i, "HIGH", "SECRET-IN-RESPONSE", "OTP / reset code returned in an API response",
                    "Send it only by SMS/email; the response says just 'sent'.", lines)
        if re.search(r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*[`'\"](admin|admin123|password|123456|changeme|letmein)[`'\"]", ln):
            ctx.add(rel, i, "CRITICAL", "DEFAULT-CREDS", "Default admin password in code", "Remove it; create admins once by hand with a strong password + 2FA.", lines)
        if not browser and _USER_ENUM.search(ln):
            ctx.add(rel, i, "MEDIUM", "USER-ENUM", "Login/reset reply says whether an account exists",
                    "Give the same reply either way: 'If this number/email is registered, we sent a code.'", lines)


# ---------------------------------------------------------------- Python (AST)
def _dotted(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _dotted(node.value) + "." + node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func) + "()"
    return ""


def _kw(call, name):
    return next((k for k in call.keywords if k.arg == name), None)


def _is_const(node) -> bool:
    return isinstance(node, ast.Constant)


def _built_string(node) -> bool:
    return isinstance(node, ast.JoinedStr) or (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mod, ast.Add))) \
        or (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format")


def check_py(ctx: Ctx, rel: str, text: str, lines: list):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return
    test = is_test(rel)
    server = bool(re.search(r"^\s*(from|import)\s+(fastapi|flask|aiohttp|starlette|http\.server|django)", text, re.M))
    req_names = {"request", "req", "filename", "file_name", "fname", "user_path"}
    req_sessions = {_dotted(t) for n in ast.walk(tree) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                    and _dotted(n.value.func) == "requests.Session" for t in n.targets} - {""}
    # login safety (reel items 04 and 14): account-exists replies, guessable codes
    if not test:
        for i, ln in enumerate(lines, 1):
            if server and _USER_ENUM.search(ln):
                ctx.add(rel, i, "MEDIUM", "USER-ENUM", "Login/reset reply says whether an account exists",
                        "Give the same reply either way: 'If this number/email is registered, we sent a code.'", lines)
            if re.search(r"(?i)\b\w*(otp|token|reset|verif\w*_?code|secret|password|nonce)\w*\s*=.*\brandom\."
                         r"(randint|choice|choices|random|randrange|sample|getrandbits)\(", ln):
                ctx.add(rel, i, "MEDIUM", "WEAK-RANDOM", "random module used for a login code/token (guessable)",
                        "Use secrets.randbelow / secrets.token_urlsafe.", lines)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted(node.func)
        line = node.lineno
        add = lambda sev, rule, msg, fix="": ctx.add(rel, line, sev, rule, msg, fix, lines)  # noqa: E731
        tail = name.rsplit(".", 1)[-1]
        # network timeouts
        if not test:
            if tail == "urlopen" and not _kw(node, "timeout") and len(node.args) < 3:
                add("HIGH", "NET-TIMEOUT-PY", "urlopen() without a timeout", "Pass timeout=<seconds>.")
            elif re.fullmatch(r"(requests|%s)\.(get|post|put|patch|delete|head|request)" % "|".join(map(re.escape, req_sessions)) if req_sessions
                              else r"requests\.(get|post|put|patch|delete|head|request)", name) and not _kw(node, "timeout"):
                add("HIGH", "NET-TIMEOUT-PY", f"{name}() without a timeout (requests waits forever)", "Pass timeout=<seconds>.")
            elif name == "aiohttp.ClientSession" and not _kw(node, "timeout"):
                add("MEDIUM", "NET-TIMEOUT-PY", "aiohttp.ClientSession() uses the 5-minute default timeout", "Pass timeout=aiohttp.ClientTimeout(total=15).")
        # shells and code execution
        sh = _kw(node, "shell")
        if name.startswith("subprocess.") and sh is not None and isinstance(sh.value, ast.Constant) and sh.value.value is True:
            built = bool(node.args) and _built_string(node.args[0])
            add("CRITICAL" if built and not test else "HIGH", "CMD-INJECTION",
                "subprocess with shell=True" + (" and a built command string" if built else ""), "Pass a list of arguments and drop shell=True.")
        if name in ("os.system", "os.popen") and not test:
            add("HIGH" if node.args and not _is_const(node.args[0]) else "MEDIUM", "CMD-INJECTION", f"{name}() runs a shell", "Use subprocess.run([...]) without a shell.")
        if name in ("eval", "exec") and node.args and not _is_const(node.args[0]) and not test:
            add("HIGH", "CODE-EVAL", f"{name}() on a non-constant value", "Parse data instead (json, ast.literal_eval).")
        # SQL
        if tail in ("execute", "executemany", "executescript", "mogrify") and node.args and _built_string(node.args[0]):
            add("HIGH", "SQL-STRING", "SQL built with f-string / % / + / format()", "Use query parameters (%s / ? placeholders).")
        # TLS + unsafe loaders
        v = _kw(node, "verify")
        if v is not None and isinstance(v.value, ast.Constant) and v.value.value is False:
            add("HIGH", "TLS-OFF", "verify=False switches off certificate checks", "Remove it.")
        if name.endswith("_create_unverified_context"):
            add("HIGH", "TLS-OFF", "Unverified SSL context", "Use ssl.create_default_context().")
        if name in ("pickle.load", "pickle.loads", "marshal.loads", "marshal.load") and not test:
            add("HIGH", "UNSAFE-LOAD", f"{name}() can run code from the data", "Use json for data you did not create.")
        if name == "yaml.load" and not _kw(node, "Loader"):
            add("HIGH", "UNSAFE-LOAD", "yaml.load without a safe Loader", "Use yaml.safe_load().")
        # JWT: signature check switched off / secret written in code
        if name == "jwt.decode" and not test:
            opts = _kw(node, "options")
            off = (_kw(node, "verify") is not None and isinstance(_kw(node, "verify").value, ast.Constant)
                   and _kw(node, "verify").value.value is False)
            if opts is not None and isinstance(opts.value, ast.Dict):
                for k, val in zip(opts.value.keys, opts.value.values):
                    if isinstance(k, ast.Constant) and k.value == "verify_signature" and isinstance(val, ast.Constant) and val.value is False:
                        off = True
            if off:
                add("HIGH", "JWT-NO-VERIFY", "jwt.decode with signature check off", "Verify with the real key and algorithms=[...].")
        if name in ("jwt.encode", "jwt.decode") and len(node.args) > 1 and _is_const(node.args[1]) and not test:
            add("CRITICAL", "JWT-LITERAL-SECRET", "JWT key written in the code", "Read a long random key from an env var.")
        # time zones
        if not test and tail in ("now", "utcnow") and name.split(".")[-2:-1] in (["datetime"], ["dt"]) :
            if tail == "utcnow" or (not node.args and not _kw(node, "tz")):
                add("MEDIUM", "NAIVE-DATETIME", f"{name}() has no time zone", "Use datetime.now(timezone.utc) or ZoneInfo('Asia/Kolkata').")
        # text encoding
        if not test:
            mode = None
            if name == "open":
                mode = node.args[1] if len(node.args) > 1 else (_kw(node, "mode").value if _kw(node, "mode") else None)
                check = True
            elif tail == "open" and isinstance(node.func, ast.Attribute) and (
                    (isinstance(node.func.value, ast.BinOp) and isinstance(node.func.value.op, ast.Div))
                    or _dotted(node.func.value) in ("Path()", "pathlib.Path()")):
                mode = node.args[0] if node.args else (_kw(node, "mode").value if _kw(node, "mode") else None)
                check = True
            elif tail in ("read_text", "write_text") and isinstance(node.func, ast.Attribute):
                check = True
            else:
                check = False
            binary = isinstance(mode, ast.Constant) and isinstance(mode.value, str) and "b" in mode.value
            if check and not binary and not _kw(node, "encoding") and not (tail == "write_text" and len(node.args) > 1) \
                    and not (tail == "read_text" and node.args):
                add("MEDIUM", "TEXT-ENCODING", f"{tail}() of a text file without encoding=", "Add encoding=\"utf-8\" (Telugu/Hindi text breaks on Windows otherwise).")
        # path traversal in server code
        if server and not test and (name in ("open", "send_file", "FileResponse") or tail in ("send_file", "FileResponse")) and node.args:
            used = {n.id for n in ast.walk(node.args[0]) if isinstance(n, ast.Name)}
            if used & req_names:
                add("HIGH", "PATH-TRAVERSAL", "File path built from request input", "Allow-list names; resolve() and check the folder.")


# ---------------------------------------------------------------- security headers
HEADER_RULES = [
    ("HDR-CSP", "HIGH", r"content-security-policy", "No Content-Security-Policy (main XSS guard)"),
    ("HDR-HSTS", "MEDIUM", r"strict-transport-security", "No Strict-Transport-Security (HSTS)"),
    ("HDR-FRAME", "MEDIUM", r"x-frame-options|frame-ancestors", "No X-Frame-Options / frame-ancestors (clickjacking)"),
    ("HDR-NOSNIFF", "MEDIUM", r"x-content-type-options", "No X-Content-Type-Options: nosniff"),
    ("HDR-REFERRER", "INFO", r"referrer-policy", "No Referrer-Policy"),
]


def check_headers(ctx: Ctx, files: list):
    sites = []
    for p in files:
        rel = p.relative_to(ctx.root).as_posix()
        if is_test(rel):
            continue
        if p.name == "netlify.toml":
            sites.append((p.parent, p))
        elif p.name.startswith("astro.config."):
            sites.append((p.parent, p.parent / "public" / "_headers"))
    for site_dir, cfg in sites:
        texts = []
        for f in [cfg] + [q for q in files if q.name == "_headers" and site_dir in q.parents]:
            t = read(f) if f.exists() else None
            if t:
                texts.append(t)
        blob = "\n".join(texts).lower()
        rel = cfg.relative_to(ctx.root).as_posix()
        for rule, sev, rx, msg in HEADER_RULES:
            if not re.search(rx, blob):
                ctx.add(rel, 0, sev, rule, f"{msg} for site {site_dir.relative_to(ctx.root).as_posix()}",
                        "Add it under [[headers]] for \"/*\" (Netlify) or in public/_headers (Cloudflare Pages).", text="\n".join(texts))


# ---------------------------------------------------------------- Supabase SQL
def check_sql(ctx: Ctx, files: list):
    by_world = {}
    for p in files:
        rel = p.relative_to(ctx.root).as_posix()
        if p.suffix == ".sql" and not is_test(rel) and "stub" not in p.name:
            t = read(p)
            if t is not None:
                by_world.setdefault(world_of(rel), []).append((rel, re.sub(r"--[^\n]*", "", t), t))
    for world, items in by_world.items():
        rls = set()
        for _, t, _ in items:
            rls |= {m.group(1).split(".")[-1].strip('"').lower()
                    for m in re.finditer(r"(?i)alter\s+table\s+(?:if\s+exists\s+)?(?:only\s+)?([\w.\"]+)\s+enable\s+row\s+level\s+security", t)}
        for rel, t, raw in items:
            lines = raw.splitlines()
            for m in re.finditer(r"(?i)create\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)", t):
                full = m.group(1).strip('"')
                if "." in full and not full.lower().startswith("public."):
                    continue  # private schemas are not exposed by the Supabase API
                name = full.split(".")[-1].strip('"').lower()
                if name not in rls:
                    ln = t[:m.start()].count("\n") + 1
                    ctx.add(rel, ln, "CRITICAL", "RLS-MISSING", f"Table {name} has no 'enable row level security'",
                            "Add `alter table ... enable row level security;` and policies.", lines)
            for m in re.finditer(r"(?is)create\s+(?:or\s+replace\s+)?view\s+([\w.\"]+)(.{0,200}?)\bas\b", t):
                if "security_invoker" not in m.group(2).lower():
                    ln = t[:m.start()].count("\n") + 1
                    ctx.add(rel, ln, "HIGH", "VIEW-DEFINER", f"View {m.group(1)} runs with the owner's rights (no security_invoker)",
                            "Use `with (security_invoker = on)`.", lines)
            for m in re.finditer(r"(?is)create\s+(?:or\s+replace\s+)?function\s+([\w.\"]+)(.*?)(?=create\s+(?:or\s+replace\s+)?function|\Z)", t):
                body = m.group(2)
                if re.search(r"(?i)security\s+definer", body) and not re.search(r"(?i)search_path", body):
                    ln = t[:m.start()].count("\n") + 1
                    ctx.add(rel, ln, "HIGH", "DEFINER-SEARCH-PATH", f"Function {m.group(1)} is SECURITY DEFINER without a fixed search_path",
                            "Add `set search_path = public, pg_temp`.", lines)


# ---------------------------------------------------------------- GitHub workflows
def check_workflows(ctx: Ctx, files: list):
    for p in files:
        rel = p.relative_to(ctx.root).as_posix()
        if not (rel.startswith(".github/workflows/") and p.suffix in (".yml", ".yaml")):
            continue
        text = read(p) or ""
        lines = text.splitlines()
        if not re.search(r"^permissions:", text, re.M):
            ctx.add(rel, 1, "MEDIUM", "CI-PERMISSIONS", "No top-level permissions: (token gets broad defaults)", "Add `permissions: { contents: read }`.", lines, text)
        if re.search(r"^\s*pull_request_target\s*:", text, re.M):
            ctx.add(rel, 1, "HIGH", "CI-PR-TARGET", "pull_request_target runs fork code with secrets", "Use pull_request.", lines)
        in_jobs, job, job_line, has_timeout, uses_reusable = False, None, 0, False, False

        def close_job():
            if job and not has_timeout and not uses_reusable:
                ctx.add(rel, job_line, "MEDIUM", "CI-TIMEOUT", f"Job '{job}' has no timeout-minutes (a hung run burns free minutes for 6 h)",
                        "Add timeout-minutes: 10 (or what the job needs).", lines)

        for i, ln in enumerate(lines, 1):
            if re.match(r"^jobs:\s*$", ln):
                in_jobs = True
                continue
            if in_jobs and re.match(r"^\S", ln):
                close_job(); in_jobs, job = False, None
            if in_jobs:
                m = re.match(r"^  ([\w-]+):\s*$", ln)
                if m:
                    close_job()
                    job, job_line, has_timeout, uses_reusable = m.group(1), i, False, False
                elif re.match(r"^    timeout-minutes:", ln):
                    has_timeout = True
                elif re.match(r"^    uses:", ln):
                    uses_reusable = True
            m = re.search(r"\buses:\s*['\"]?([^\s'\"#]+)", ln)
            if m:
                ref = m.group(1)
                first_party = ref.startswith(("actions/", "github/", "./", "docker://"))
                if not first_party and not re.search(r"@[0-9a-f]{40}$", ref):
                    ctx.add(rel, i, "HIGH", "CI-UNPINNED-ACTION", f"Third-party action {ref} is not pinned to a commit SHA",
                            "Pin to the full 40-character SHA (a tag can be moved by its owner).", lines)
            if re.search(r"\$\{\{\s*github\.event\.(issue|pull_request|comment|review|review_comment|discussion|head_commit|commits)[^}]*\.(title|body|message|name|label|ref)\b", ln):
                ctx.add(rel, i, "HIGH", "CI-SCRIPT-INJECTION", "User-controlled text expanded inside the workflow", "Pass it through env: and quote \"$VAR\".", lines)
            if re.search(r"\becho\b.*\$\{\{\s*secrets\.", ln):
                ctx.add(rel, i, "HIGH", "CI-ECHO-SECRET", "A secret is echoed in a run step", "Never print secrets.", lines)
        close_job()
    if not any(p.relative_to(ctx.root).as_posix() in (".github/dependabot.yml", ".github/dependabot.yaml") for p in files):
        ctx.add(".github", 0, "INFO", "DEPS-BOT", "No .github/dependabot.yml (free weekly dependency-update PRs)",
                "Add Dependabot for npm, pip and github-actions.")


# ---------------------------------------------------------------- tests, CI coverage, env files
ENV_RX = [re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"), re.compile(r"\benv\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
          re.compile(r"os\.environ(?:\.get)?[\[(]\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"), re.compile(r"os\.getenv\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
          re.compile(r"Deno\.env\.get\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"), re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]{2,})")]
ENV_IGNORE = re.compile(r"^(CI|HOME|PATH|PWD|USER|LANG|TZ|PORT|NODE_ENV|GITHUB_\w+|RUNNER_\w+|PYTHON\w*|PG\w+|DEBUG|TERM|TMPDIR|SHELL|NETLIFY|CONTEXT|URL|DEPLOY_\w+)$")


def check_world_level(ctx: Ctx, files: list):
    worlds = sorted(set(WORLDS.values()))
    tests = {w: [] for w in worlds}
    env_read = {w: {} for w in worlds}
    env_docs = {w: "" for w in worlds}
    has_example = {w: False for w in worlds}
    corpus, pytest_dirs, npm_dirs = [], set(), set()
    for p in files:
        rel = p.relative_to(ctx.root).as_posix()
        w = world_of(rel)
        if p.name.startswith(".env.") and p.name != ".env":
            has_example[w] = True
            env_docs[w] += read(p) or ""
        elif p.suffix == ".md":
            env_docs[w] += read(p) or ""
        if p.suffix in CODE_EXT and is_test(rel) and "/fixtures/" not in "/" + rel:
            tests[w].append(rel)
        elif p.suffix in CODE_EXT and not is_test(rel):
            t = read(p) or ""
            for rx in ENV_RX:
                for m in rx.finditer(t):
                    if not ENV_IGNORE.match(m.group(1)):
                        env_read[w].setdefault(m.group(1), rel)
        if rel.startswith(".github/workflows/") or p.suffix == ".sh" or p.name == "package.json":
            t = read(p) or ""
            corpus.append(t)
            if rel.startswith(".github/workflows/"):
                for step in re.split(r"\n\s*- ", t):
                    wd = re.search(r"working-directory:\s*([\w./-]+)", step)
                    if "pytest" in step:
                        pytest_dirs.add(wd.group(1).strip("/") if wd else "")
                        pytest_dirs |= {a.strip("/") for a in re.findall(r"pytest[^\n]*?\s((?:\d\d-|\.)[\w./-]+)", step)}
                    if re.search(r"npm (run )?test|pnpm test|npm run test", step) and wd:
                        npm_dirs.add(wd.group(1).strip("/"))
                for d in re.findall(r"defaults:\s*\n\s*run:\s*\n\s*working-directory:\s*([\w./-]+)", t):
                    npm_dirs.add(d.strip("/"))
    blob = "\n".join(corpus)
    for w in worlds:
        if not tests[w]:
            ctx.add(w.split()[-1], 0, "HIGH", "TESTS-MISSING", f"No automated tests found in {w}", "Add at least one test for the money paths.")
            continue
        uncovered = []
        for rel in tests[w]:
            parent, name = rel.rsplit("/", 1)
            ok = name in blob or parent in blob
            ok = ok or (rel.endswith(".py") and any(d == "" or rel.startswith(d + "/") for d in pytest_dirs))
            ok = ok or any(rel.startswith(d + "/") for d in npm_dirs)
            if not ok:
                uncovered.append(rel)
        if uncovered:
            ctx.add(w.split()[-1], 0, "INFO", "TESTS-NOT-IN-CI",
                    f"{len(uncovered)} of {len(tests[w])} test files may not run in CI, e.g. {', '.join(uncovered[:3])}",
                    "Wire them into .github/workflows/quality.yml or delete dead tests.")
    for w in worlds:
        names = env_read[w]
        if not names:
            continue
        undocumented = sorted(n for n in names if n not in env_docs[w])
        if not has_example[w]:
            ctx.add(w.split()[-1], 0, "MEDIUM", "ENV-EXAMPLE", f"{len(names)} env vars read but no .env.example ({len(undocumented)} not named in any doc): "
                    + ", ".join(undocumented[:8] or sorted(names)[:8]), "Add a .env.example listing every name with a dummy value and where to set it.")
        elif undocumented:
            ctx.add(w.split()[-1], 0, "INFO", "ENV-UNDOCUMENTED", "Env vars not in .env.example: " + ", ".join(undocumented[:8]))


# ---------------------------------------------------------------- run + report
def audit(root: Path) -> list:
    ctx = Ctx(root=root)
    files = [p for p in walk(root)]
    for p in files:
        rel = p.relative_to(root).as_posix()
        if p.name in SKIP_FILES or p.suffix not in TEXT_EXT and not p.name.startswith(".env"):
            continue
        if rel.startswith("00-hq/quality/"):
            continue  # the scanner and its fixtures describe the very patterns it hunts
        text = read(p)
        if text is None:
            continue
        lines = text.splitlines()
        check_secrets(ctx, rel, text, lines)
        if p.suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
            check_js(ctx, rel, text, lines)
        elif p.suffix == ".py":
            check_py(ctx, rel, text, lines)
    check_headers(ctx, files)
    check_sql(ctx, files)
    check_workflows(ctx, files)
    check_world_level(ctx, files)
    order = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(ctx.findings, key=lambda f: (f.world, order[f.severity], f.rule, f.file, f.line))


def counts(findings):
    out = {}
    for f in findings:
        if not f.waived:
            out.setdefault(f.world, {s: 0 for s in SEVERITIES})[f.severity] += 1
    return out


def to_markdown(findings, limit_per_sev=25) -> str:
    c = counts(findings)
    worlds = sorted(set(WORLDS.values()))
    total = {s: sum(c.get(w, {}).get(s, 0) for w in worlds) for s in SEVERITIES}
    out = ["# Kalpa engineering audit", "",
           "Static scan by `00-hq/quality/eng_audit.py` against `ENGINEERING-CHECKLIST.md`. "
           "CRITICAL fails CI; the rest is the fix list. Waive a line with `# eng-audit: ok <reason>`.", "",
           "| World | CRITICAL | HIGH | MEDIUM | INFO |", "|---|---|---|---|---|"]
    for w in worlds:
        r = c.get(w, {s: 0 for s in SEVERITIES})
        out.append(f"| {w} | " + " | ".join(str(r[s]) for s in SEVERITIES) + " |")
    out.append("| **All** | " + " | ".join(f"**{total[s]}**" for s in SEVERITIES) + " |")
    waived = [f for f in findings if f.waived]
    out += ["", f"Waived: {len(waived)}.", ""]
    for w in worlds:
        fs = [f for f in findings if f.world == w and not f.waived]
        if not fs:
            continue
        out += [f"## {w}", ""]
        for s in SEVERITIES:
            group = [f for f in fs if f.severity == s]
            if not group:
                continue
            out.append(f"**{s}** ({len(group)})")
            out.append("")
            for f in group[:limit_per_sev]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                out.append(f"- `{f.rule}` {loc}: {f.message}" + (f". Fix: {f.fix}" if f.fix else ""))
            if len(group) > limit_per_sev:
                out.append(f"- … and {len(group) - limit_per_sev} more (see report.json)")
            out.append("")
    if waived:
        out += ["## Waived", ""] + [f"- `{f.rule}` {f.file}:{f.line}: {f.waived}" for f in waived] + [""]
    return "\n".join(out)


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(here.parent.parent))
    ap.add_argument("--md", default=str(here / "report.md"))
    ap.add_argument("--json", default=str(here / "report.json"))
    ap.add_argument("--strict", action="store_true", help="exit 1 if any un-waived CRITICAL finding")
    a = ap.parse_args(argv)
    findings = audit(Path(a.root).resolve())
    md = to_markdown(findings)
    Path(a.md).write_text(md + "\n", encoding="utf-8")
    Path(a.json).write_text(json.dumps({"counts": counts(findings), "findings": [asdict(f) for f in findings]}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    crit = [f for f in findings if f.severity == "CRITICAL" and not f.waived]
    tot = {s: sum(1 for f in findings if f.severity == s and not f.waived) for s in SEVERITIES}
    print("eng-audit: " + ", ".join(f"{k} {v}" for k, v in tot.items()) + f" -> {a.md}")
    for f in crit:
        print(f"CRITICAL {f.rule} {f.file}:{f.line} {f.message}")
    return 1 if (a.strict and crit) else 0


if __name__ == "__main__":
    sys.exit(main())
