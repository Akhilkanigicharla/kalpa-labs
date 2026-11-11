"""P2: build the DPDP + EU AI Act Art. 50 transparency checklist from the Ledger Peaks framework catalogue.

    python3 build_checklist.py [--client "Acme"] [--out checklist.md]

Source of truth: 06-finops/src/frameworks/{dpdp-2023,eu-ai-act-art50}.json (Kalpa's own wording, dated
sources inside). Re-run after those files change so the checklist never drifts from them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FW = Path(__file__).resolve().parents[2] / "src" / "frameworks"
LAWYER = "**[LAWYER CHECK]** Check with a lawyer before giving this to a client."


def _load(name: str) -> dict:
    return json.loads((FW / f"{name}.json").read_text(encoding="utf-8"))


def build(client: str = "Client") -> str:
    eu, dp = _load("eu-ai-act-art50"), _load("dpdp-2023")
    L = [f"# DPDP + EU AI Act Art. 50 transparency checklist: {client}", "",
         LAWYER + " Every line below is a legal point. This is Kalpa Labs' plain-English summary, "
         "not the legal text, not legal advice and not a certification.", "",
         "How to use: tick Yes / No / N.A. for each line, write where the evidence is, and give the "
         "client the open items as tasks. Dates change: recheck the sources on the day you deliver.", "",
         "## Part A. EU AI Act Article 50 (transparency)", "",
         f"Applies from {eu['dates']['applies_from']}; last checked {eu['dates']['last_checked']}. "
         "First answer ART50-06: with no EU users, Art. 50 likely does not reach the client.", "",
         "| ID | Para | Who | Check | Evidence to collect | Yes/No/N.A. | Where |",
         "|---|---|---|---|---|---|---|"]
    for c in eu["controls"]:
        note = ""
        if c.get("transition"):
            t = c["transition"]
            note = f" (grace period until {t['until']} for {t['for']}; {t.get('verified', '')})"
        L.append(f"| {c['id']} | {c['para']} | {c['role']} | {c['name']}{note} [LAWYER CHECK] | "
                 f"{'; '.join(c['evidence'])} |  |  |")
    L += ["", "## Part B. India DPDP Act 2023 + Rules 2025 (AI usage)", "",
          f"Rules published {dp['dates']['rules_published']}; most duties from {dp['dates']['most_duties']}; "
          f"last checked {dp['dates']['last_checked']}. {dp['dates']['date_basis']}", "",
          "| ID | Check | Cites | Evidence to collect | Max penalty (Rs crore) | Yes/No/N.A. | Where |",
          "|---|---|---|---|---|---|---|"]
    for c in dp["controls"]:
        L.append(f"| {c['id']} | {c['name']} [LAWYER CHECK] | {', '.join(c['cite'])} | "
                 f"{'; '.join(c['evidence'])} | {c.get('penalty_max_inr_crore', 50)} |  |  |")
    L += ["", f"Penalties: {dp['penalties_note']}", "", "## Sources", ""]
    for s in eu["sources"] + dp["sources"]:
        L.append(f"- {s['what']}: {s['url']} (checked {s['checked']})")
    L += ["", LAWYER, ""]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--client", default="Client")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    md = build(a.client)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
