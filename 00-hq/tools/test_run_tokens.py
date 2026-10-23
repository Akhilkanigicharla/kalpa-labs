import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from run_tokens import totals
d = tempfile.mkdtemp(); p = os.path.join(d, "s.jsonl")
rows = [{"message": {"id": "a", "usage": {"input_tokens": 2, "output_tokens": 10, "cache_read_input_tokens": 100}}},
        {"message": {"id": "a", "usage": {"input_tokens": 2, "output_tokens": 10, "cache_read_input_tokens": 100}}},
        {"message": {"id": "b", "usage": {"input_tokens": 1, "output_tokens": 5, "cache_creation_input_tokens": 50}}},
        {"type": "user", "message": {"content": "hi"}}]
open(p, "w").write("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")
t = totals([p])
assert t["turns"] == 2 and t["output_tokens"] == 15 and t["input_tokens"] == 3, t
assert t["cache_read_input_tokens"] == 100 and t["cache_creation_input_tokens"] == 50, t
print("run_tokens tests passed")
