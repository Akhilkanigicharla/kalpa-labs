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
        if isinstance(item, tuple):  # (content, finish_reason)
            return {"choices": [{"message": {"content": item[0]}, "finish_reason": item[1]}]}
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

    def test_cut_off_or_unclosed_think_tries_next_model(self):
        post = fake_post([("half a dra", "length"), "<think>still thinking", "full draft", "PASS"])
        res = R.work(self.task, self.env, post, self.root)
        self.assertEqual(res["draft"], "full draft")
        self.assertEqual(len(post.calls), 4)

    def test_gemini_gets_low_reasoning_and_more_room(self):
        env = {"GEMINI_API_KEY": "x"}
        post = fake_post(["draft", "PASS"])
        R.work(self.task, env, post, self.root)
        url, pay = post.calls[0]
        self.assertIn("generativelanguage", url)
        self.assertEqual((pay["max_tokens"], pay.get("reasoning_effort")), (8000, "low"))

    def test_min_items_sends_short_drafts_back(self):
        self.task["min_items"] = 20
        short = "\n".join(f"{i}. row" for i in range(1, 13))
        res = R.work(self.task, self.env, fake_post([short]), self.root)
        self.assertTrue(res["verdict"].startswith("FIX: incomplete, 12 of 20"))
        self.assertEqual(R.apply(self.task, res, self.root), "todo")
        full = "\n".join(f"| {i} | Pattern | done |" for i in range(1, 21))
        res = R.work(self.task, self.env, fake_post([full, "PASS"]), self.root)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(R.count_items("**1.** a\n2) b\n- 3. c\n| 4 | d |\n10. e"), 5)

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

    def test_groq_always_first_then_preferred_provider(self):  # A229: Groq has 1,000/day per model, OpenRouter free only 50/day
        for prefer in ["gemini", "openrouter", "groq", ""]:
            self.assertEqual(R.ordered(R.MODELS, prefer)[0][0], "GROQ_API_KEY")
            self.assertEqual(R.ordered(R.VIGIL_MODELS, R.VIGIL_FOR.get(prefer, ""))[0][0], "GROQ_API_KEY")
            self.assertEqual(sorted(R.ordered(R.MODELS, prefer)), sorted(R.MODELS))  # nothing lost
        after_groq = [m for m in R.ordered(R.MODELS, "gemini") if m[0] != "GROQ_API_KEY"]
        self.assertEqual(after_groq[0][0], "GEMINI_API_KEY")
        self.assertEqual([m for m in R.ordered(R.MODELS, "openrouter") if m[0] != "GROQ_API_KEY"][0][0], "OPENROUTER_API_KEY")
        self.assertTrue(all("googleapis.com" in m[1] for m in R.MODELS if m[0] == "GEMINI_API_KEY"))

    def test_real_queues_are_valid(self):
        q, ids = [], []
        for w in R.WORLDS:
            p = os.path.join(R.TASKS, w + ".json")
            if os.path.exists(p):
                part = json.load(open(p))
                self.assertTrue(all(t["world"] == w for t in part), w)
                q += part
        for t in q:  # numbers must be numbers, or the runner crashes adding to them (K076/K077, 12 Nov)
            for k in ("tries", "context_chars", "min_items"):
                self.assertTrue(k not in t or isinstance(t[k], int), f'{t["id"]}.{k} must be a number')
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


class CloudflareBackupTest(unittest.TestCase):
    def test_cloudflare_url_and_skip(self):
        import runner
        cf = [m for m in runner.MODELS if m[0] == "CLOUDFLARE_API_TOKEN"]
        self.assertTrue(cf)
        seen = []
        def post(url, hdr, pay):
            seen.append(url)
            return {"choices": [{"message": {"content": "ok"}}]}
        self.assertEqual(runner.call(cf, [], {"CLOUDFLARE_API_TOKEN": "t"}, post), (None, None))  # no account id: skipped
        text, model = runner.call(cf, [], {"CLOUDFLARE_API_TOKEN": "t", "CLOUDFLARE_ACCOUNT_ID": "abc"}, post)
        self.assertEqual(text, "ok")
        self.assertEqual(seen[0], "https://api.cloudflare.com/client/v4/accounts/abc/ai/v1/chat/completions")


class DailyCountTest(unittest.TestCase):  # A229: count calls per day, skip a provider at its free daily cap
    def setUp(self):
        self.d = tempfile.mkdtemp()
        R.USAGE.clear()

    def tearDown(self):
        R.USAGE.clear()

    def test_counts_calls_and_skips_at_cap(self):
        models = [("OPENROUTER_API_KEY", "https://openrouter.ai/x", "a:free"), ("GROQ_API_KEY", "https://api.groq.com/x", "g")]
        env = {"OPENROUTER_API_KEY": "k", "GROQ_API_KEY": "k"}
        R.USAGE.update({"date": R.today(), "calls": {"OPENROUTER_API_KEY|b:free": 50}})  # OpenRouter's 50/day shared by all free models
        seen = []
        def post(url, hdr, pay):
            seen.append(pay["model"])
            return {"choices": [{"message": {"content": "ok"}}]}
        self.assertEqual(R.call(models, [], env, post), ("ok", "g"))
        self.assertEqual(seen, ["g"])  # OpenRouter skipped, no wasted request
        self.assertEqual(R.USAGE["calls"]["GROQ_API_KEY|g"], 1)

    def test_daily_429_marks_provider_spent_and_usage_files_merge(self):
        env = {"KL_RETRY_WAIT": "0", "OPENROUTER_API_KEY": "k"}
        models = [("OPENROUTER_API_KEY", "u", "a:free"), ("OPENROUTER_API_KEY", "u", "b:free")]
        n = []
        def post(url, hdr, pay):
            n.append(1)
            raise R.urllib.error.HTTPError(url, 429, "limit", {}, None)
        self.assertEqual(R.call(models, [], env, post), (None, None))
        self.assertEqual(len(n), 2)  # first model: try + one retry; second model skipped as spent
        R.save_usage("b1", self.d)
        json.dump({"date": R.today(), "calls": {"GROQ_API_KEY|g": 7}}, open(os.path.join(self.d, "b2.json"), "w"))
        json.dump({"date": "2000-01-01", "calls": {"GROQ_API_KEY|g": 999}}, open(os.path.join(self.d, "b3.json"), "w"))
        tot = R.day_totals(self.d)
        self.assertEqual(tot["GROQ_API_KEY|g"], 7)  # old days ignored
        self.assertGreaterEqual(tot["OPENROUTER_API_KEY"], 50)
        R.USAGE.clear()
        R.load_usage("b1", self.d)
        self.assertEqual(R.used("GROQ_API_KEY", "g"), (7, 7))  # other worlds' calls count toward shared caps


if __name__ == "__main__":
    unittest.main()
