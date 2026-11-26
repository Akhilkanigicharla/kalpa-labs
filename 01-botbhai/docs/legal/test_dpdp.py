"""A230 check: every DPDP duty in dpdp-2027.md is mapped to BotBhai, the site form and the
site chat as done / n/a / planned A### (and every planned id exists in ROADMAP.md).
Run: python3 01-botbhai/docs/legal/test_dpdp.py"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CELL = re.compile(r"^(done|n/a|planned (A\d{3}))\b")


def check(doc: str, roadmap: str) -> list[str]:
    errs, rows = [], []
    for line in doc.splitlines():
        if re.match(r"^\| *D\d+ *\|", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    if len(rows) < 12:
        errs.append(f"only {len(rows)} duty rows (need 12+)")
    ids = set(re.findall(r"\*\*(A\d{3})\*\*", roadmap))
    for r in rows:
        if len(r) != 7:
            errs.append(f"{r[0]}: {len(r)} columns (need 7)")
            continue
        if not re.search(r"(13 Nov 2025|13 Nov 2026|13 May 2027)", r[3]):
            errs.append(f"{r[0]}: start date missing")
        for name, cell in zip(("BotBhai", "form", "chat"), r[4:7]):
            m = CELL.match(cell)
            if not m:
                errs.append(f"{r[0]} {name}: '{cell[:30]}' must start done / n/a / planned A###")
            elif m.group(2) and m.group(2) not in ids:
                errs.append(f"{r[0]} {name}: {m.group(2)} not in ROADMAP.md")
    return errs


if __name__ == "__main__":
    # self-test: a broken table must fail
    bad = "| D1 | x | r | soon | maybe | done | planned A999 |"
    assert len(check(bad, "")) >= 3, "self-test failed"
    errs = check((HERE / "dpdp-2027.md").read_text(), (ROOT / "00-hq/ROADMAP.md").read_text())
    for e in errs:
        print("FAIL", e)
    print("PASS dpdp-2027.md" if not errs else f"{len(errs)} problems")
    sys.exit(1 if errs else 0)
