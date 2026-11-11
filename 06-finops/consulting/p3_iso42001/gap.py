"""P3 ISO/IEC 42001 readiness: answers file -> scored gap report + 90-day roadmap (markdown).

    python3 gap.py template > answers.json        # blank answers file to fill in
    python3 gap.py report answers.json --out gap-report.md

Answers file (JSON, or YAML if PyYAML is installed):
    {"client": "Acme", "scope": "Support chatbot and lead-scoring model",
     "answers": {"4.1": {"score": 2, "note": "...", "owner": "CTO"}, "A.4.2": {"score": "na", "reason": "..."}}}
Scores: 0-3 (see areas.json "scale"). "na" only for Annex A items and only with a reason.
Readiness check only. Not a certification; only an accredited certification body certifies.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOGUE = HERE.parents[1] / "src" / "frameworks" / "iso42001-2023.json"
AREAS = HERE / "areas.json"
PHASES = {1: "Days 1-30: foundations", 2: "Days 31-60: build and run controls", 3: "Days 61-90: check, tell, improve"}
STATUS = {0: "Missing", 1: "Started", 2: "Partly done", 3: "Done"}


def group_of(cid: str) -> str:
    """'6.1.2' -> '6'; 'A.6.2.4' -> 'A.6'."""
    parts = cid.split(".")
    return ".".join(parts[:2]) if parts[0] == "A" else parts[0]


def items() -> list[dict]:
    cat = json.loads(CATALOGUE.read_text(encoding="utf-8"))["controls"]
    areas = json.loads(AREAS.read_text(encoding="utf-8"))
    out = []
    for c in cat:
        g = group_of(c["id"])
        out.append({"id": c["id"], "title": c["name"].split(" - ", 1)[-1], "group": g,
                    "annex": c["id"].startswith("A."), "question": areas["questions"][c["id"]],
                    "phase": areas["groups"][g]["phase"]})
    return out


def load_answers(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if str(path).endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError as e:
            raise ValueError("YAML needs PyYAML; save the answers as .json instead") from e
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("answers", {}), dict):
        raise ValueError("answers file must be an object with an 'answers' object")
    return data


def score(data: dict) -> dict:
    ans = data.get("answers") or {}
    its, problems = items(), []
    known = {i["id"] for i in its}
    problems += [f"unknown id ignored: {k}" for k in ans if k not in known]
    rows = []
    for it in its:
        a = ans.get(it["id"])
        a = a if isinstance(a, dict) else ({"score": a} if a is not None else {})
        s = a.get("score")
        if isinstance(s, str) and s.strip().lower() == "na":
            if not it["annex"]:
                problems.append(f"{it['id']}: clauses 4-10 cannot be 'na'; scored 0")
                s = 0
            elif not str(a.get("reason", "")).strip():
                problems.append(f"{it['id']}: 'na' needs a reason; scored 0")
                s = 0
            else:
                s = "na"
        elif s is None:
            if it["id"] in ans:
                problems.append(f"{it['id']}: no score given; scored 0")
            s = 0
        else:
            try:
                s = int(s)
            except (TypeError, ValueError):
                s = -1
            if s not in STATUS:
                problems.append(f"{it['id']}: score must be 0-3 or 'na'; scored 0")
                s = 0
        rows.append({**it, "score": s, "note": str(a.get("note", "") or a.get("reason", "")),
                     "owner": str(a.get("owner", "")), "answered": it["id"] in ans})
    unanswered = sum(1 for r in rows if not r["answered"])
    if unanswered:
        problems.append(f"{unanswered} item(s) not answered; scored 0")

    def pct(rs):
        rs = [r for r in rs if r["score"] != "na"]
        return round(100 * sum(r["score"] for r in rs) / (3 * len(rs))) if rs else 100

    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    gaps = [r for r in rows if r["score"] != "na" and r["score"] < 3]
    # roadmap order: phase, then mandatory clauses first, then lowest score first
    gaps.sort(key=lambda r: (r["phase"], r["annex"], r["score"]))
    return {"rows": rows, "groups": {g: pct(rs) for g, rs in groups.items()},
            "clauses": pct([r for r in rows if not r["annex"]]), "annex": pct([r for r in rows if r["annex"]]),
            "overall": pct(rows), "gaps": gaps, "problems": problems,
            "na": [r for r in rows if r["score"] == "na"]}


def render(data: dict, res: dict) -> str:
    areas = json.loads(AREAS.read_text(encoding="utf-8"))["groups"]
    client = data.get("client") or "Client"
    L = [f"# ISO/IEC 42001 readiness gap report: {client}", ""]
    if data.get("synthetic"):
        L += ["> **SYNTHETIC DATA.** Made-up answers for a demo, not a real client.", ""]
    L += ["Prepared by Kalpa Labs (AI FinOps + AI Guardrails consulting). **Readiness check only, not a "
          "certification.** Only an accredited certification body can certify. Item wording is Kalpa's own "
          "summary; the requirements are in the standard (buy it from ISO or BIS).", "",
          f"**Scope:** {data.get('scope') or 'not stated (agree it first: clause 4.3)'}", "",
          "## 1. Score", "",
          f"- Overall readiness: **{res['overall']}%**",
          f"- Clauses 4-10 (all mandatory): **{res['clauses']}%**",
          f"- Annex A controls: **{res['annex']}%**",
          f"- Gaps to close: **{len(res['gaps'])}** "
          f"({sum(1 for g in res['gaps'] if g['score'] == 0)} missing, "
          f"{sum(1 for g in res['gaps'] if g['score'] > 0)} partial)", "",
          "Scale: 0 nothing, 1 started, 2 mostly, 3 done with evidence. % = points / max points.", "",
          "## 2. By area", "", "| Area | What it covers | Readiness |", "|---|---|---:|"]
    for g, p in res["groups"].items():
        name = f"Clause {g}" if not g.startswith("A") else f"Annex {g}"
        L.append(f"| {name} {areas[g]['title']} | {areas[g]['about']} | {p}% |")
    L += ["", "## 3. Gap list", "", "| ID | Item | Status | Check question | Note |", "|---|---|---|---|---|"]
    for r in sorted(res["gaps"], key=lambda r: (r["score"], r["annex"])):
        L.append(f"| {r['id']} | {r['title']} | {STATUS[r['score']]} | {r['question']} | {r['note']} |")
    if not res["gaps"]:
        L.append("| - | No gaps found | - | - | - |")
    L += ["", "## 4. 90-day roadmap", "",
          "Order: foundations first, mandatory clauses before Annex A, biggest gaps first in each phase.", ""]
    for ph, label in PHASES.items():
        todo = [r for r in res["gaps"] if r["phase"] == ph]
        L += [f"### {label}", ""]
        if not todo:
            L += ["- Nothing open in this phase.", ""]
            continue
        for r in todo:
            owner = r["owner"] or "owner to name"
            L.append(f"- [ ] **{r['id']} {r['title']}** ({STATUS[r['score']]}, {owner}): {r['question']}")
        L.append("")
    L += ["### After day 90", "",
          "- Run one full internal audit (9.2) and one management review (9.3) on the new system.",
          "- Keep 2-3 months of records, then talk to an accredited certification body if you want a certificate.", ""]
    if res["na"]:
        L += ["## 5. Marked not applicable (for the Statement of Applicability)", ""]
        L += [f"- {r['id']} {r['title']}: {r['note']}" for r in res["na"]] + [""]
    if res["problems"]:
        L += ["## Data notes", ""] + [f"- {p}" for p in res["problems"]] + [""]
    return "\n".join(L)


def template() -> dict:
    return {"client": "", "scope": "", "assessor": "", "date": "",
            "answers": {i["id"]: {"score": None, "note": "", "owner": "", "question": i["question"]}
                        for i in items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P3 ISO/IEC 42001 readiness gap report")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template")
    rp = sub.add_parser("report")
    rp.add_argument("answers")
    rp.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "template":
        print(json.dumps(template(), indent=2))
        return 0
    try:
        data = load_answers(a.answers)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    md = render(data, score(data))
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
