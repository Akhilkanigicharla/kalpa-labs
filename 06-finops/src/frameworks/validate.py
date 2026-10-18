"""A31 (F-13): validate the framework catalogue.

Rules checked (from PLAN.md F-13 and the b6.pack validator):
- every DPDP duty cites at least one Act section or Rule, in a fixed format;
- every duty has a valid applies_from date and some evidence to collect;
- every ISO 42001 ID a duty maps to exists in iso42001-2023.json;
- the ISO file keeps its Probo (MIT) attribution and holds IDs + short titles only;
- every Art. 50 item names a paragraph 50(1)-(7) and a role;
- every file has a disclaimer or note, dated sources, and a last-checked date.

Run: python3 06-finops/src/frameworks/validate.py   (exit 1 on any problem)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
CITE = re.compile(r"^(Act s\.\d{1,2}(\(\d{1,2}\))?(\([a-z]\))?|Act Schedule|Rule \d{1,2}(\(\d{1,2}\))?(\([a-z]\))?)$")
PARA = re.compile(r"^Art\. 50\([1-7]\)$")
ROLES = {"provider", "deployer", "provider+deployer"}
MAX_ISO_NAME = 160  # titles only; anything longer smells like copied standard text


def _date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def load(name: str, folder: Path = HERE) -> dict:
    return json.loads((folder / name).read_text(encoding="utf-8"))


def check_ids(controls: list[dict], errs: list[str], tag: str) -> None:
    ids = [c.get("id") for c in controls]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f"{tag}: duplicate ids {sorted(dup)}")
    for c in controls:
        if not c.get("id") or not c.get("name"):
            errs.append(f"{tag}: control without id or name: {c}")


def check_iso(iso: dict) -> list[str]:
    errs: list[str] = []
    src = iso.get("source", {})
    if src.get("licence") != "MIT" or "Probo" not in src.get("copyright", ""):
        errs.append("iso: Probo MIT attribution missing")
    ctl = iso.get("controls", [])
    if len(ctl) < 30:
        errs.append(f"iso: only {len(ctl)} controls")
    check_ids(ctl, errs, "iso")
    for c in ctl:
        if set(c) - {"id", "name"}:
            errs.append(f"iso {c['id']}: extra fields {sorted(set(c) - {'id', 'name'})} (IDs + titles only)")
        if len(c.get("name", "")) > MAX_ISO_NAME:
            errs.append(f"iso {c['id']}: title too long, looks like copied text")
    return errs


def check_meta(doc: dict, tag: str, errs: list[str]) -> None:
    if not (doc.get("disclaimer") or doc.get("note")):
        errs.append(f"{tag}: no disclaimer")
    elif tag != "iso" and "not legal advice" not in doc["disclaimer"].lower():
        errs.append(f"{tag}: disclaimer must say 'not legal advice'")
    if tag != "iso":
        if not _date(doc.get("dates", {}).get("last_checked", "")):
            errs.append(f"{tag}: dates.last_checked missing")
        srcs = doc.get("sources", [])
        if not srcs:
            errs.append(f"{tag}: no sources")
        for s in srcs:
            if not str(s.get("url", "")).startswith("https://") or not _date(s.get("checked", "")):
                errs.append(f"{tag}: source needs https url and checked date: {s}")


def check_dpdp(dpdp: dict, iso_ids: set[str]) -> list[str]:
    errs: list[str] = []
    check_meta(dpdp, "dpdp", errs)
    ctl = dpdp.get("controls", [])
    check_ids(ctl, errs, "dpdp")
    for c in ctl:
        cid = c.get("id")
        cites = c.get("cite") or []
        if not cites:
            errs.append(f"dpdp {cid}: no section or rule cited")
        for x in cites:
            if not CITE.match(x):
                errs.append(f"dpdp {cid}: bad citation '{x}' (use 'Act s.8(5)' or 'Rule 6(1)(a)')")
        if not _date(c.get("applies_from", "")):
            errs.append(f"dpdp {cid}: applies_from is not a date")
        if not c.get("evidence"):
            errs.append(f"dpdp {cid}: no evidence listed")
        for i in c.get("iso42001", []):
            if i not in iso_ids:
                errs.append(f"dpdp {cid}: ISO 42001 id '{i}' not in iso42001-2023.json")
    return errs


def check_art50(art: dict) -> list[str]:
    errs: list[str] = []
    check_meta(art, "art50", errs)
    ctl = art.get("controls", [])
    check_ids(ctl, errs, "art50")
    for c in ctl:
        if not PARA.match(c.get("para", "")):
            errs.append(f"art50 {c.get('id')}: bad paragraph '{c.get('para')}'")
        if c.get("role") not in ROLES:
            errs.append(f"art50 {c.get('id')}: role must be one of {sorted(ROLES)}")
        if not _date(c.get("applies_from", "")) or not c.get("evidence"):
            errs.append(f"art50 {c.get('id')}: needs applies_from date and evidence")
    return errs


def validate(folder: Path = HERE) -> list[str]:
    iso = load("iso42001-2023.json", folder)
    iso_ids = {c["id"] for c in iso.get("controls", []) if "id" in c}
    return (check_iso(iso) + check_dpdp(load("dpdp-2023.json", folder), iso_ids)
            + check_art50(load("eu-ai-act-art50.json", folder)))


def main() -> int:
    errs = validate()
    for e in errs:
        print("FAIL", e)
    if not errs:
        d = load("dpdp-2023.json")
        print(f"OK dpdp {len(d['controls'])} duties, iso {len(load('iso42001-2023.json')['controls'])} IDs, "
              f"art50 {len(load('eu-ai-act-art50.json')['controls'])} checks")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
