"""Price pass for API-ingested events (F-11).

The ingest API never trusts a client's cost: rows land with cost_paise = null.
This pass prices them with the same engine as the X-ray (genai-prices + FBIL rate),
so API and file imports give identical rupees. Unknown models stay null (unpriced,
never shown as Rs 0).

Run (GitHub Actions, hourly): SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY as secrets,
    python3 06-finops/src/api/price_pass.py --limit 5000
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingest.schema import UsageRecord  # noqa: E402
from price.engine import price_record  # noqa: E402
from price.fx import FxTable  # noqa: E402

COLS = ("id,ts,provider,model,input_tokens,output_tokens,cache_read_tokens,cache_write_tokens,"
        "reasoning_tokens,requests,batch,served_from_cache")


def price_rows(rows: list[dict], fx: FxTable) -> list[dict]:
    """[{id, ...usage_event cols}] -> [{id, cost_paise}] for rows the engine can price."""
    out = []
    for r in rows:
        rec = UsageRecord(ts=r["ts"], provider=r["provider"], model=r["model"],
                          input_tokens=r["input_tokens"], output_tokens=r["output_tokens"],
                          cache_read_tokens=r["cache_read_tokens"], cache_write_tokens=r["cache_write_tokens"],
                          reasoning_tokens=r["reasoning_tokens"], requests=r["requests"],
                          batch=r["batch"], served_from_cache=r["served_from_cache"], source="api")
        p = price_record(rec, fx)
        if p.paise is not None:
            out.append({"id": r["id"], "cost_paise": p.paise})
    return out


def _call(url: str, key: str, method="GET", body=None):
    req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"apikey": key, "authorization": f"Bearer {key}",
                                          "content-type": "application/json", "prefer": "return=minimal"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data) if data else None


def run(base: str, key: str, limit: int, fx: FxTable, call=_call) -> dict:
    rest = base.rstrip("/") + "/rest/v1/usage_event"
    rows = call(f"{rest}?select={COLS}&source=eq.api&cost_paise=is.null&order=id&limit={limit}", key) or []
    priced = price_rows(rows, fx)
    for p in priced:   # one PATCH per row keeps it simple and safe; volumes here are small
        call(f"{rest}?id=eq.{p['id']}", key, "PATCH", {"cost_paise": p["cost_paise"]})
    return {"fetched": len(rows), "priced": len(priced), "unpriced": len(rows) - len(priced)}


if __name__ == "__main__":
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 5000
    url, svc = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not svc:
        sys.exit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (GitHub secrets)")
    print(json.dumps(run(url, svc, lim, FxTable.load())))
