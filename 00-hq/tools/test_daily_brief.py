import os, sys, unittest
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
import daily_brief as D

TRIAL = '<p>Your trial has ended. <a href="https://app.n8n.cloud/account/change-plan">Upgrade now</a></p>'


class Classify(unittest.TestCase):
    def test_trial_ended_is_an_alert(self):
        self.assertIn("trial has ended", D.classify("n8n", 200, TRIAL))
        self.assertIn("trial has ended", D.classify("n8n", 404, TRIAL))

    def test_down_key_quota(self):
        self.assertIn("not reachable", D.classify("Website", 0, "timed out"))
        self.assertIn("key or login", D.classify("chat", 401, "unauthorized"))
        self.assertIn("429", D.classify("chat", 429, "slow down"))
        self.assertIn("HTTP 502", D.classify("site", 502, "bad gateway"))

    def test_wrong_page_and_healthy(self):
        self.assertIn("looks wrong", D.classify("Website", 200, "<h1>Site not found</h1>", want="Kalpa"))
        self.assertIsNone(D.classify("Website", 200, "<title>Kalpa Labs</title>", want="Kalpa"))


class Recipient(unittest.TestCase):
    def test_only_private_chats(self):
        self.assertTrue(D.private_chat("1905524851"))
        for bad in ("-1001234567890", "-42", "", "@kalpadeals", None):
            self.assertFalse(D.private_chat(bad))


class Build(unittest.TestCase):
    now = datetime(2026, 11, 3, 21, 0, tzinfo=D.IST)

    def test_alerts_come_first(self):
        text, alerts = D.build(self.now, [None, "chat: provider says “trial has ended”"], ["Actions failing: quality"], ["fix x"], ["A143"])
        self.assertEqual(len(alerts), 2)
        self.assertLess(text.index("⚠️ ALERTS"), text.index("Code changes"))
        self.assertIn("A143", text)

    def test_progress_by_world_and_noise_filter(self):
        road = ("- [x] **A1** b3 · Exam kits batch 1 (done 2026-11-06, abc)\n"
                "- [x] **A2** b3 · Old kit (done 2026-10-01, abc)\n"
                "- [x] **A3** HQ · Agent memory (done 2026-11-07, def)\n"
                "- [ ] **A4** b1 · Depth: BotBhai end to end\n- [~] **A5** b1 · Voice\n")
        lines = D.progress(road, {"review": 35, "rejected": 2}, D.datetime(2026, 11, 7).date())
        text = "\n".join(lines)
        self.assertIn("b3 Exam kits", text); self.assertIn("1 done", text)
        self.assertNotIn("Old kit", text)
        self.assertIn("HQ", text); self.assertIn("35", text)
        self.assertIn("b1", text); self.assertIn("1 in progress", text)
        self.assertEqual(D.real_commits(["agents(b3): queue run x", "claim A1", "log: x", "A177: fix tests"]), ["A177: fix tests"])

    def test_all_clear(self):
        text, alerts = D.build(self.now, [None, None], [], [], [])
        self.assertEqual(alerts, [])
        self.assertIn("No alerts", text)
        self.assertLessEqual(len(text), 3900)


if __name__ == "__main__":
    unittest.main()
