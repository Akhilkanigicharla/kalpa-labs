"""Kalpa PII scan: count PII in LLM log exports without keeping the PII.

Usage (from 06-finops/src, or with it on PYTHONPATH):
    python -m pii.scan <paths...> --out report.json [--fail-on AADHAAR,PAN]
                       [--engine auto|builtin|presidio]

The report holds counts per entity and per file plus HMAC-SHA256 hashes of the
normalised values (for dedupe). It never holds, prints or logs a raw value.
Salt: env LP_HASH_SALT (set it as a CI secret). Exit 0 = ok, 1 = a --fail-on
entity was found, 2 = bad usage or no readable input.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Iterator

from . import __version__
from . import recognizers as builtin

try:  # reuse the FinOps hashing so hashes match ingest's pseudonymous ids
    from ingest.schema import DEV_SALT, MissingSaltError, hash_id, resolve_salt
except ImportError:  # vendored without ingest/: identical algorithm
    import hashlib
    import hmac

    DEV_SALT = "ledger-peaks-dev-salt"  # same as ingest.schema

    class MissingSaltError(RuntimeError):
        pass

    def resolve_salt(salt=None):
        if salt:
            return salt
        if os.environ.get("LP_HASH_SALT"):
            return os.environ["LP_HASH_SALT"]
        if os.environ.get("LP_ALLOW_DEV_SALT") == "1":
            return DEV_SALT
        raise MissingSaltError("LP_HASH_SALT is not set; refusing to hash with the public dev salt")

    def hash_id(value, salt=None):
        if value is None or str(value).strip() == "":
            return None
        key = resolve_salt(salt).encode()
        return "c_" + hmac.new(key, str(value).strip().encode(), hashlib.sha256).hexdigest()[:16]

SCAN_EXT = {".csv", ".tsv", ".jsonl", ".ndjson", ".json", ".txt", ".log", ".md"}


# ------------------------------------------------------------------ reading

def _walk_json(obj) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, bool) or obj is None:
        return
    elif isinstance(obj, (int, float)):
        yield str(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_json(k)
            yield from _walk_json(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_json(v)


def iter_texts(path: Path, stats: dict) -> Iterator[str]:
    """Yield text chunks. JSON is parsed so escapes like \\n don't glue to values."""
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        if suffix == ".json":
            raw = fh.read()
            stats["records"] += 1
            try:
                yield from _walk_json(json.loads(raw))
            except ValueError:
                stats["parse_errors"] += 1
                yield raw
            return
        for line in fh:
            stats["records"] += 1
            if suffix in (".jsonl", ".ndjson") and line.strip():
                try:
                    yield from _walk_json(json.loads(line))
                    continue
                except ValueError:
                    stats["parse_errors"] += 1
            yield line


def expand(paths: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            out += sorted(f for f in pp.rglob("*") if f.is_file() and f.suffix.lower() in SCAN_EXT)
        else:
            out.append(pp)
    return out


# ----------------------------------------------------------------- engines

def resolve_engine(name: str) -> str:
    from . import presidio_engine
    if name == "builtin":
        return "builtin"
    if name == "presidio":
        if not presidio_engine.available():
            raise SystemExit("error: --engine presidio but presidio-analyzer is not installed")
        return "presidio"
    return "presidio" if presidio_engine.available() else "builtin"


def find_all(text: str, engine: str, agree: dict | None = None):
    found = list(builtin.find(text))
    if engine != "presidio":
        return found
    from . import presidio_engine
    pres = list(presidio_engine.find(text))
    overlaps = lambda a, b: a.start < b.end and b.start < a.end
    extra = [p for p in pres if not any(overlaps(p, f) for f in found)]
    if agree is not None:
        for p in extra:
            agree["presidio_only"][p.entity] += 1
        for f in found:
            if not any(overlaps(f, p) for p in pres):
                agree["builtin_only"][f.entity] += 1
    return found + extra


# -------------------------------------------------------------------- scan

def scan(paths: Iterable[str], engine: str = "auto", salt: str | None = None) -> dict:
    engine = resolve_engine(engine)
    salt_source = "arg" if salt else ("env" if os.environ.get("LP_HASH_SALT") else "dev-default")
    resolve_salt(salt)  # fail before reading any file when no real salt is set
    totals: Counter = Counter()
    per_file: dict[str, dict] = {}
    hashes: dict[str, set] = defaultdict(set)
    files = []
    agree = {"presidio_only": Counter(), "builtin_only": Counter()} if engine == "presidio" else None
    for path in expand(paths):
        stats = {"path": str(path), "records": 0, "parse_errors": 0}
        counts: Counter = Counter()
        try:
            for text in iter_texts(path, stats):
                for f in find_all(text, engine, agree):
                    counts[f.entity] += 1
                    hashes[f.entity].add(hash_id(f.norm, salt))
        except (OSError, UnicodeError) as e:  # type name only: messages can echo content
            stats["error"] = type(e).__name__
        files.append(stats)
        per_file[str(path)] = dict(sorted(counts.items()))
        totals.update(counts)
    report = {
        "tool": "kalpa-pii-scan",
        "version": __version__,
        "engine": engine,
        "presidio_version": None,
        "salt_source": salt_source,
        "files": files,
        "totals": dict(sorted(totals.items())),
        "unique": {k: len(v) for k, v in sorted(hashes.items())},
        "per_file": per_file,
        "hashes": {k: sorted(v) for k, v in sorted(hashes.items())},
    }
    if engine == "presidio":
        from . import presidio_engine
        report["presidio_version"] = presidio_engine.version()
        report["engine_agreement"] = {k: dict(sorted(v.items())) for k, v in agree.items()}
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pii.scan", description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", help="files or folders (csv, jsonl, json, txt, log)")
    ap.add_argument("--out", default="report.json", help="report path, or - for stdout")
    ap.add_argument("--fail-on", default="", help="comma list of entities, e.g. AADHAAR,PAN")
    ap.add_argument("--engine", choices=["auto", "builtin", "presidio"], default="auto")
    a = ap.parse_args(argv)

    fail_on = [x.strip().upper() for x in a.fail_on.split(",") if x.strip()]
    report = scan(a.paths, engine=a.engine)
    hit = sorted(e for e in fail_on if report["totals"].get(e, 0) > 0)
    report["fail_on"] = fail_on
    report["failed_entities"] = hit
    if not any("error" not in f for f in report["files"]):
        print("error: no readable input files", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if a.out == "-":
        print(text)
    else:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    summary = ", ".join(f"{k}={v}" for k, v in report["totals"].items()) or "none"
    print(f"pii-scan {report['engine']}: {len(report['files'])} file(s); found: {summary}",
          file=sys.stderr)
    if report["salt_source"] == "dev-default":
        print("warning: LP_HASH_SALT not set; hashes use the public dev salt", file=sys.stderr)
    if hit:
        print("FAIL: found " + ", ".join(hit), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
