"""Cross-check genai-prices against LiteLLM's price map (data only, MIT).

    python -m price.crosscheck /path/to/model_prices_and_context_window.json

Downloads are done by the weekly Action, never here. Compares USD per million
input / output / cache-read tokens for the models our customers use most and
flags any gap above 0.5% (the INR Price Engine validator in PLAN.md).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

WATCH = [  # (provider, genai-prices model, LiteLLM key)
    ("openai", "gpt-4o", "gpt-4o"), ("openai", "gpt-4o-mini", "gpt-4o-mini"),
    ("openai", "gpt-4.1", "gpt-4.1"), ("openai", "gpt-4.1-mini", "gpt-4.1-mini"),
    ("openai", "gpt-5", "gpt-5"), ("openai", "gpt-5-mini", "gpt-5-mini"),
    ("openai", "o3", "o3"), ("openai", "o4-mini", "o4-mini"),
    ("anthropic", "claude-sonnet-4-5", "claude-sonnet-4-5"),
    ("anthropic", "claude-haiku-4-5", "claude-haiku-4-5"),
    ("anthropic", "claude-opus-4-5", "claude-opus-4-5"), ("anthropic", "claude-opus-4-8", "claude-opus-4-8"),
    ("google", "gemini-2.5-flash", "gemini/gemini-2.5-flash"),
    ("google", "gemini-2.5-pro", "gemini/gemini-2.5-pro"),
    ("google", "gemini-2.5-flash-lite", "gemini/gemini-2.5-flash-lite"),
]
TOL = Decimal("0.005")
M = Decimal(1_000_000)


def ours(provider: str, model: str) -> dict[str, Decimal]:
    from genai_prices import Usage, calc_price
    # probe with 100k-token calls x 10: a single 1M-token call would hit long-context tiers
    def p(**kw):
        return Decimal(str(calc_price(Usage(**kw), model_ref=model, provider_id=provider).total_price)) * 10
    return {"input": p(input_tokens=100_000), "output": p(output_tokens=100_000),
            "cache_read": p(input_tokens=100_000, cache_read_tokens=100_000)}


def theirs(entry: dict) -> dict[str, Decimal | None]:
    def g(k):
        v = entry.get(k)
        return Decimal(str(v)) * M if v is not None else None
    return {"input": g("input_cost_per_token"), "output": g("output_cost_per_token"),
            "cache_read": g("cache_read_input_token_cost")}


def compare(litellm: dict, watch=WATCH) -> list[dict]:
    rows = []
    for prov, model, key in watch:
        row = {"model": f"{prov}/{model}", "status": "ok", "gaps": {}}
        if key not in litellm:
            row["status"] = "missing in litellm"
            rows.append(row)
            continue
        try:
            a = ours(prov, model)
        except Exception as e:
            row["status"] = f"missing in genai-prices ({type(e).__name__})"
            rows.append(row)
            continue
        b = theirs(litellm[key])
        for k in a:
            if b[k] is None:
                continue
            gap = abs(a[k] - b[k]) / b[k] if b[k] else (Decimal(0) if a[k] == 0 else Decimal(1))
            row["gaps"][k] = float(gap)
            if gap > TOL:
                row["status"] = "MISMATCH"
        row["ours"] = {k: str(v) for k, v in a.items()}
        row["litellm"] = {k: (str(v) if v is not None else None) for k, v in b.items()}
        rows.append(row)
    return rows


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    rows = compare(json.loads(Path(argv[0]).read_text()))
    for r in rows:
        print(f"{r['status']:<30} {r['model']:<32} {r.get('ours', '')} | {r.get('litellm', '')}")
    return 1 if any(r["status"] == "MISMATCH" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
