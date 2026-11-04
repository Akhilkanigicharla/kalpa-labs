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

    def test_real_queue_is_valid(self):
        q = json.load(open(R.QUEUE))
        ids = [t["id"] for t in q]
        self.assertEqual(len(ids), len(set(ids)))
        for t in q:
            self.assertIn(t["status"], ("todo", "review", "rejected", "done"))
            self.assertIn(t["priority"], ("P0", "P1", "P2"))


if __name__ == "__main__":
    unittest.main()
