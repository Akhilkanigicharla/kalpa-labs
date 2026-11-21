"""Dependency audit for every world folder with a package-lock.json (A311, ENGINEERING-CHECKS row 33).

Runs `npm audit --omit=dev --audit-level=high` per folder, prints a markdown table and
exits 1 if any folder has a high/critical advisory or the audit could not run (fail closed).
Usage: python3 00-hq/tools/dep_audit.py [repo root]
"""
import json, os, subprocess, sys

SKIP = {"node_modules", ".claude", "vendor", ".git", "graft"}


def find_locks(root):
    out = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        if "package-lock.json" in files:
            out.append(os.path.relpath(dirpath, root).replace(os.sep, "/"))
    return sorted(out)


def npm_audit(folder):
    r = subprocess.run(["npm", "audit", "--omit=dev", "--audit-level=high", "--json"],
                       cwd=folder, capture_output=True, text=True, timeout=120)
    return r.stdout


def audit(folders, run):
    rows, bad = [], 0
    for f in folders:
        try:
            v = json.loads(run(f))["metadata"]["vulnerabilities"]
            row = {"folder": f, "moderate": v.get("moderate", 0), "high": v.get("high", 0),
                   "critical": v.get("critical", 0)}
            row["ok"] = row["high"] + row["critical"] == 0
        except Exception as e:  # npm failed or printed non-JSON: count as a failure, never a pass
            row = {"folder": f, "moderate": "?", "high": "?", "critical": "?", "ok": False,
                   "error": type(e).__name__}
        bad += not row["ok"]
        rows.append(row)
    return rows, bad


def markdown(rows):
    lines = ["### Dependency audit (npm, production deps)", "",
             "| Folder | Moderate | High | Critical | Result |", "|---|---|---|---|---|"]
    for r in rows:
        res = "PASS" if r["ok"] else ("FAIL" + (f" ({r['error']})" if "error" in r else ""))
        lines.append(f"| {r['folder']} | {r['moderate']} | {r['high']} | {r['critical']} | {res} |")
    return "\n".join(lines)


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    folders = find_locks(root)
    rows, bad = audit(folders, lambda f: npm_audit(os.path.join(root, f)))
    print(markdown(rows))
    print(f"\n{len(folders)} folders, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
