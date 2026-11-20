import json
import export_dates as ed


def test_feed_is_current():
    assert ed.OUT.read_text(encoding="utf-8") == ed.text(), "run python3 03-kits/engine/export_dates.py"


def test_feed_shape():
    rows = json.loads(ed.OUT.read_text(encoding="utf-8"))
    assert rows and all(set(r) == {"exam_id", "exam", "exam_te", "event", "event_te", "status", "date", "source"} for r in rows)
    assert all(r["date"] is None or len(r["date"]) == 10 for r in rows)
