"""Check an intake.json against intake.schema.json. Stdlib only: supports the schema keywords used there
(type, required, properties, items, enum, const, minimum, minLength, minItems, pattern).

    python3 validate_intake.py intake.json      # exit 0 = valid, 1 = problems listed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent / "intake.schema.json"
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


def _type_ok(v, t) -> bool:
    if t in ("integer", "number") and isinstance(v, bool):
        return False
    return isinstance(v, TYPES[t])


def check(value, schema: dict, path: str = "$") -> list[str]:
    errs = []
    t = schema.get("type")
    if t and not _type_ok(value, t):
        return [f"{path}: should be {t}"]
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: must be {json.dumps(schema['const'])}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errs.append(f"{path}: too short")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: wrong format")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema \
            and value < schema["minimum"]:
        errs.append(f"{path}: below {schema['minimum']}")
    if isinstance(value, dict):
        errs += [f"{path}.{k}: missing" for k in schema.get("required", []) if k not in value]
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                errs += check(value[k], sub, f"{path}.{k}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for i, item in enumerate(value):
                errs += check(item, schema["items"], f"{path}[{i}]")
    return errs


def validate(data) -> list[str]:
    return check(data, json.loads(SCHEMA.read_text(encoding="utf-8")))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    try:
        data = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"error: {e}")
        return 2
    errs = validate(data)
    print("\n".join(errs) if errs else "intake is valid")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
