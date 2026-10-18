"""One command for the free LLM Bill X-ray (F-06).

    python3 06-finops/src/xray/generate.py usage.csv [more files] --company "Acme AI" \
        [--revenue revenue.csv] [--dpdp answers.json] [--out xray.html] [--pdf]
    python3 06-finops/src/xray/generate.py --synthetic --out /tmp/xray.html   # demo on made-up data

Needs LP_HASH_SALT (a per-client secret) for real files, so customer ids are hashed before
anything else happens. Input files are read only; nothing leaves this machine.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ingest import load  # noqa: E402
from xray import dpdp  # noqa: E402
from xray.render import render, to_pdf  # noqa: E402
from xray.report import build, load_revenue  # noqa: E402


def synthetic_records():
    sys.path.insert(0, str(SRC.parent / "design"))
    import sample  # the A12 made-up company, "Chaiwala AI"
    names = {sample.hash_id(n): n for n in sample.CUSTOMERS}
    revenue = {cid: (n, sample.CUSTOMERS[n][1] * 100) for cid, n in names.items()}
    answers = [ok for _, ok in sample.DPDP]
    return sample.records(), revenue, answers, "Chaiwala AI (synthetic)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Make the 2-page LLM Bill X-ray.")
    ap.add_argument("files", nargs="*", type=Path, help="usage exports (OpenAI, Anthropic, LiteLLM, Langfuse, CSV/JSONL)")
    ap.add_argument("--company", default="Your company")
    ap.add_argument("--revenue", type=Path, help="CSV: customer, name, monthly_revenue_inr")
    ap.add_argument("--dpdp", type=Path, help="JSON: 20 answers (true/false/null)")
    ap.add_argument("--out", type=Path, default=Path("xray.html"))
    ap.add_argument("--pdf", action="store_true", help="also print a PDF next to the HTML (needs Playwright)")
    ap.add_argument("--synthetic", action="store_true", help="demo on the made-up sample company")
    a = ap.parse_args(argv)

    if a.synthetic:
        records, revenue, answers, company = synthetic_records()
    else:
        if not a.files:
            ap.error("give at least one usage file, or --synthetic")
        records, lost = [], 0
        for f in a.files:
            res = load(f)
            if not res.balanced:
                lost += 1
            for row, why in res.skipped:
                print(f"  skipped {f.name} row {row}: {why}")
            records += res.records
        if lost:
            print("ERROR: rows were lost while importing; not making a report")
            return 2
        revenue, answers, company = load_revenue(a.revenue), dpdp.load_answers(a.dpdp), a.company
    data = build(records, company=company, revenue=revenue, dpdp_answers=answers, synthetic=a.synthetic)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(render(data), encoding="utf-8")
    print(f"{company}: ₹{data['total_month'] / 100:,.0f} a month projected from {data['period']['days']} days, "
          f"{len(data['savings'])} savings ideas worth ₹{data['savings_month'] / 100:,.0f} a month, "
          f"DPDP {data['dpdp']['score']}/{data['dpdp']['of']}, {data['unpriced']['rows']} unpriced rows")
    print(f"wrote {a.out}")
    if a.pdf:
        pages = to_pdf(a.out, a.out.with_suffix(".pdf"))
        print(f"wrote {a.out.with_suffix('.pdf')} ({pages} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
