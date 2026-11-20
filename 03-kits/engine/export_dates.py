"""b3 exam-date feed for the engine alert flow (A242 b3): exams/*.yaml key_dates -> dist/exam-dates.json.
Run: python3 03-kits/engine/export_dates.py   (tests/test_dates_feed.py checks the committed file is current)"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kit_engine as ke

OUT = ke.DIST / "exam-dates.json"


def rows():
    out = []
    for f in ke.exam_files():
        d = ke.load(f)
        for k in d.get("key_dates") or []:
            out.append({"exam_id": d["id"], "exam": d.get("short") or d.get("name"), "exam_te": d.get("name_te") or "",
                        "event": k.get("event") or "", "event_te": k.get("event_te") or "", "status": k.get("status") or "",
                        "date": k.get("date"), "source": k.get("source") or ""})
    return out


def text():
    return json.dumps(rows(), indent=1, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUT.write_text(text(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ke.DIST.parent.parent.parent)} ({len(rows())} dates)")
