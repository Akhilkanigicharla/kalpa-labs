import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
import runner as R


def fake_post(script):
    calls = []
    def post(url, headers, payload):
        calls.append((url, payload))
        item = script.pop(0)
        if isinstance(item, Exception):
            raise item
        return {"choices": [{"message": {"content": item}}]}
    post.calls = calls
    return post


class Runner(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "00-hq/vendor/agency-agents/sales"))
        open(os.path.join(self.root, "00-hq/vendor/agency-agents/sales/deal-closer.md"), "w").write("Close deals kindly.")
        open(os.path.join(self.root, "OFFER.md"), "w").write("BotBhai pilot is free.")
        self.env = {"GROQ_API_KEY": "g", "OPENROUTER_API_KEY": "o"}
        self.task = {"id": "T1", "title": "Write pilot pitch", "owner": "Kavi", "status": "todo", "priority": "P0",
                     "read": ["OFFER.md", "../etc/passwd"], "playbook": "deal-closer"}

    def test_pick_orders_p0_first(self):
        q = [{"id": "a", "status": "todo", "priority": "P2"}, {"id": "b", "status": "review", "priority": "P0"},
             {"id": "c", "status": "todo", "priority": "P0"}]
        self.assertEqual([t["id"] for t in R.pick(q, 3)], ["c", "a"])

    def test_pass_writes_knowledge_and_reads_repo_and_playbook(self):
        post = fake_post(["<think>x</think>Pitch: free 14-day pilot.", "PASS"])
        res = R.work(self.task, self.env, post, self.root)
        self.assertEqual(R.apply(self.task, res, self.root), "review")
        out = open(os.path.join(self.root, self.task["output"])).read()
        self.assertIn("free 14-day pilot", out)
        self.assertNotIn("<think>", out)
        prompt = post.calls[0][1]["messages"]
        self.assertIn("Close deals kindly.", prompt[0]["content"])
        self.assertIn("BotBhai pilot is free.", prompt[1]["content"])
        self.assertIn("(not found)", prompt[1]["content"])  # path escape refused
        self.assertIn("BotBhai pilot is free.", post.calls[1][1]["messages"][1]["content"])  # Vigil sees the repo facts

    def test_fix_goes_back_then_rejected_after_3(self):
        for i in range(3):
            post = fake_post(["draft", "FIX: invented price"])
            st = R.apply(self.task, R.work(self.task, self.env, post, self.root), self.root)
        self.assertEqual(st, "rejected")
        self.assertIn("invented price", self.task["vigil_notes"])

    def test_model_fallback_and_no_keys(self):
        post = fake_post([RuntimeError("429"), RuntimeError("down"), "ok draft", "PASS"])
        res = R.work(self.task, self.env, post, self.root)
        self.assertEqual(res["model"], "nvidia/nemotron-3.5-super-vl:free")
        self.assertIsNone(R.work(self.task, {}, fake_post([]), self.root))
        self.assertEqual(R.apply(self.task, None, self.root), "skipped")
        self.assertEqual(self.task["status"], "todo")

    def test_vigil_unavailable_never_passes(self):
        n = len(R.VIGIL_MODELS)
        post = fake_post(["draft"] + [RuntimeError("down")] * n)
        res = R.work(self.task, self.env, post, self.root)
        self.assertIsNone(res["verdict"])
        self.assertEqual(R.apply(self.task, res, self.root), "todo")
        self.assertEqual(self.task.get("tries", 0), 0)
        self.assertEqual(self.task["last_error"], "vigil unavailable")
        self.assertFalse(os.path.exists(os.path.join(self.root, "00-hq/knowledge/T1.md")))
        R.apply(self.task, {"draft": "d", "model": "m", "verdict": "PASS", "vmodel": "v"}, self.root)
        self.assertEqual(self.task["status"], "review")
        self.assertNotIn("last_error", self.task)

    def test_humanizer_rules_reach_the_worker(self):
        rules = R.style_rules()
        self.assertIn("not x but y", rules)
        self.assertGreater(rules.count(";"), 20)
        post = fake_post(["draft", "PASS"])
        R.work(self.task, self.env, post, self.root)  # temp root has no skill: still works
        self.assertNotIn("humanizer", post.calls[0][1]["messages"][0]["content"])

    def test_gemini_first_and_vigil_checks_with_another_provider(self):
        self.assertEqual(R.ordered(R.MODELS, "gemini")[0][0], "GEMINI_API_KEY")
        self.assertEqual(R.ordered(R.VIGIL_MODELS, R.VIGIL_FOR["gemini"])[0][0], "GROQ_API_KEY")
        self.assertEqual(R.ordered(R.VIGIL_MODELS, R.VIGIL_FOR[""])[0][0], "GEMINI_API_KEY")
        self.assertTrue(all("googleapis.com" in m[1] for m in R.MODELS if m[0] == "GEMINI_API_KEY"))

    def test_prefer_openrouter_reorders(self):
        self.assertEqual(R.ordered(R.MODELS, "openrouter")[0][0], "OPENROUTER_API_KEY")
        self.assertEqual(R.ordered(R.MODELS, ""), R.MODELS)

    def test_real_queues_are_valid(self):
        q, ids = [], []
        for w in R.WORLDS:
            p = os.path.join(R.TASKS, w + ".json")
            if os.path.exists(p):
                part = json.load(open(p))
                self.assertTrue(all(t["world"] == w for t in part), w)
                q += part
        ids = [t["id"] for t in q]
        self.assertGreater(len(ids), 0)
        self.assertEqual(len(ids), len(set(ids)))
        for t in q:
            self.assertIn(t["status"], ("todo", "review", "rejected", "done"))
            self.assertIn(t["priority"], ("P0", "P1", "P2"))

    def test_context_limit_per_task(self):
        big = os.path.join(self.root, "big.md")
        open(big, "w").write("x" * 30000)
        self.assertLess(len(R.read_context(["big.md"], self.root)), R.MAX_CONTEXT + 50)
        self.assertGreater(len(R.read_context(["big.md"], self.root, 25000)), 24000)
        self.assertEqual(R.context_limit({"context_chars": 999999}), R.MAX_CONTEXT_CAP)
        self.assertEqual(R.context_limit({}), R.MAX_CONTEXT)
    def test_lessons_are_stored_and_recalled(self):
        R.apply(self.task, {"draft": "d", "model": "m", "verdict": "FIX:\n- mark the pilot price UNVERIFIED", "vmodel": "v"}, self.root)
        self.task.pop("vigil_notes", None)
        post = fake_post(["draft", "PASS"])
        R.work(self.task, self.env, post, self.root)
        prompt = post.calls[0][1]["messages"][1]["content"]
        self.assertIn("LESSONS FROM PAST TASKS", prompt)
        self.assertIn("pilot price UNVERIFIED", prompt)


if __name__ == "__main__":
    unittest.main()
