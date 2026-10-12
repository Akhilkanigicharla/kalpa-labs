# Run: python voice/test_prompt.py  (no network, no API keys)
from datetime import datetime
import prompt as P
for s in ["salon", "realestate", "gym", "examkits"]:
    cfg = P.load_setup(s)
    sp = P.system_prompt(cfg, datetime(2026, 10, 12, 10, 0, tzinfo=P.IST))
    assert cfg["business"] in sp and "Monday 12 October 2026" in sp and "Never:" in sp, s
    for c in cfg["catalog"]:
        assert c["price"] in sp, (s, c)
    t = P.tools(cfg)[0]
    assert "date" in t["properties"] and t["properties"]["date"]["description"] == "date in YYYY-MM-DD", s
    print(f"  ✓ {s}: prompt {len(sp)} chars, book fields {list(t['properties'])}")
print("voice prompt tests passed")
