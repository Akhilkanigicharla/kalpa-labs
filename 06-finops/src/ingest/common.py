"""Shared helpers for importers: read CSV/JSON/JSONL, pick aliased columns, count rows."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .schema import UsageRecord


@dataclass
class ImportResult:
    source: str
    path: str
    rows_in: int = 0
    records: list[UsageRecord] = field(default_factory=list)
    skipped: list[tuple[int, str]] = field(default_factory=list)  # (row number, reason)
    merged: list[tuple[int, int]] = field(default_factory=list)   # (row, folded into row)

    @property
    def balanced(self) -> bool:
        """'No rows lost': every input row is a record, a skip with a reason, or merged into a record."""
        return self.rows_in == len(self.records) + len(self.skipped) + len(self.merged)


def read_rows(path: str | Path, list_keys: tuple[str, ...] = ("data",)) -> list[dict]:
    """Rows from .csv, .jsonl/.ndjson or .json (a list, or an object holding a list)."""
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig")
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return list(csv.DictReader(text.splitlines()))
    if suffix in (".jsonl", ".ndjson"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    obj = json.loads(text)
    if isinstance(obj, list):
        return obj
    for k in list_keys:
        if isinstance(obj.get(k), list):
            return obj[k]
    raise ValueError(f"{p.name}: no row list found under {list_keys}")


def pick(row: dict, *names, default=None):
    """First non-empty value among aliased column names (case-insensitive)."""
    lower = {str(k).lower(): v for k, v in row.items()}
    for n in names:
        v = lower.get(n.lower())
        if v not in (None, ""):
            return v
    return default


def to_int(v) -> int:
    if v in (None, ""):
        return 0
    try:
        return int(Decimal(str(v).replace(",", "")))
    except (InvalidOperation, ValueError):
        raise ValueError(f"not a number: {v!r}")


def to_dec(v) -> Decimal | None:
    if v in (None, ""):
        return None
    try:
        return Decimal(str(v).replace(",", "").replace("$", ""))
    except InvalidOperation:
        return None


def to_bool(v) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes", "y", "batch")


def to_iso(v) -> str:
    """Unix seconds/ms or an ISO-ish string -> ISO-8601 UTC string."""
    if v in (None, ""):
        raise ValueError("missing timestamp")
    s = str(v).strip()
    if s.replace(".", "", 1).isdigit():
        n = float(s)
        if n > 1e12:
            n /= 1000
        return datetime.fromtimestamp(n, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    s2 = s.replace("Z", "+00:00").replace(" UTC", "+00:00")
    try:
        dt = datetime.fromisoformat(s2)
    except ValueError:
        raise ValueError(f"bad timestamp: {s!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def maybe_json(v):
    if isinstance(v, (dict, list)):
        return v
    if isinstance(v, str) and v.strip()[:1] in ("{", "["):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return None
    return None


def flatten_buckets(rows: list[dict], time_keys=("start_time", "starting_at")) -> list[dict]:
    """Usage APIs return [{start_time, results:[...]}]; flatten to one row per result."""
    out = []
    for r in rows:
        if isinstance(r.get("results"), list):
            t = pick(r, *time_keys)
            for res in r["results"]:
                out.append({"__bucket_time": t, **res})
        else:
            out.append(r)
    return out
