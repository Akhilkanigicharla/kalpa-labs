"""A342 check: UX-PATTERNS.md has the 20 Laws of UX table and a 20-row per-UI law template."""
import re, sys, pathlib
t = pathlib.Path(__file__).with_name("UX-PATTERNS.md").read_text(encoding="utf-8")
laws = ["Aesthetic-usability", "proximity", "Von Restorff", "Zeigarnik", "Tesler", "Prägnanz", "Serial position",
        "Progressive disclosure", "common region", "Goal-gradient", "similarity", "Recognition over recall", "Pareto",
        "Occam", "Parkinson", "uniform connectedness", "active user", "Cognitive load", "Default effect", "Peak-end"]
tpl = t.split("### Per-UI law check", 1)
assert len(tpl) == 2, "template heading missing"
rows = re.findall(r"^\| L(\d+) \| ([^|]+) \| *\|$", tpl[1], re.M)
assert [int(n) for n, _ in rows] == list(range(1, 21)), f"template rows: {len(rows)}"
for law, (_, name) in zip(laws, rows):
    assert law.lower() in name.lower(), f"{law} != {name}"
main = re.findall(r"^\| L\d+ \| [^|]+ \| [^|]+ \| [^|]+ \| \[(lawsofux|NN/g)\]\((https://[^)]+)\) \|$", tpl[0], re.M)
assert len(main) == 20, f"law table rows with source: {len(main)}"
print("PASS: 20 laws table + 20-row template")
