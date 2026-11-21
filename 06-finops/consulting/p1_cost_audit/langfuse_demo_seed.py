#!/usr/bin/env python3
"""Seed a THROWAWAY demo Langfuse (the CI one, on localhost) with made-up LLM calls, so the
P1 audit can run end to end: Langfuse -> langfuse_pull.py -> audit.py. A215.

Uses the official Langfuse Python SDK (MIT, pinned in the workflow). Synthetic data only.
Prints the number of generations sent; nothing else.
"""
from __future__ import annotations

import os
import sys

from langfuse import Langfuse

# (feature, model, calls, input tokens, output tokens, cost USD per call, errors)
PLAN = [
    ("support-bot", "gpt-4o", 30, 2600, 180, 0.0083, 3),
    ("ticket-tagger", "gpt-4o", 20, 900, 12, 0.00237, 0),
    ("summary", "claude-sonnet-4-5", 10, 4000, 400, 0.018, 1),
]


def main() -> int:
    host = os.environ.get("LANGFUSE_HOST", "")
    if not host.startswith(("http://localhost", "http://127.0.0.1")):
        print("refusing: the seeder only writes to a local demo Langfuse", file=sys.stderr)
        return 2
    lf = Langfuse(public_key=os.environ["LANGFUSE_PUBLIC_KEY"], secret_key=os.environ["LANGFUSE_SECRET_KEY"],
                  base_url=host)
    sent = 0
    for feature, model, calls, inp, out, cost, errors in PLAN:
        for i in range(calls):
            g = lf.start_observation(
                name=feature, as_type="generation", model=model,
                level="ERROR" if i < errors else "DEFAULT",
                usage_details={"input": inp, "output": out},
                cost_details={"input": round(cost * 0.8, 6), "output": round(cost * 0.2, 6)},
            )
            g.end()
            sent += 1
    lf.flush()
    lf.shutdown()
    print(sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
