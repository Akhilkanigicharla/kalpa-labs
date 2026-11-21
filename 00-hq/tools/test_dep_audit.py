"""Offline tests for dep_audit.py (A311). Run: python3 00-hq/tools/test_dep_audit.py"""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
import dep_audit as d


def counts(**kw):
    base = {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0}
    base.update(kw)
    return json.dumps({"metadata": {"vulnerabilities": base}})


class T(unittest.TestCase):
    def test_find_skips_node_modules_claude_vendor(self):
        with tempfile.TemporaryDirectory() as r:
            for p in ["01-a/package-lock.json", "01-a/node_modules/x/package-lock.json",
                      ".claude/skills/s/package-lock.json", "00-hq/vendor/v/package-lock.json",
                      "02-b/app/package-lock.json"]:
                os.makedirs(os.path.join(r, os.path.dirname(p)), exist_ok=True)
                open(os.path.join(r, p), "w").write("{}")
            self.assertEqual(d.find_locks(r), ["01-a", "02-b/app"])

    def test_clean_passes(self):
        rows, bad = d.audit(["a"], lambda f: counts(moderate=2))
        self.assertEqual(bad, 0)
        self.assertEqual(rows[0]["moderate"], 2)

    def test_high_or_critical_fails(self):
        _, bad = d.audit(["a", "b"], lambda f: counts(high=1) if f == "a" else counts(critical=3))
        self.assertEqual(bad, 2)

    def test_garbage_output_fails_closed(self):
        rows, bad = d.audit(["a"], lambda f: "npm ERR! network")
        self.assertEqual(bad, 1)
        self.assertIn("error", rows[0])

    def test_markdown_table(self):
        rows, _ = d.audit(["a"], lambda f: counts(high=1))
        md = d.markdown(rows)
        self.assertIn("| a | 0 | 1 | 0 | FAIL |", md)


if __name__ == "__main__":
    unittest.main()
