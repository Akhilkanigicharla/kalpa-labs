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


class Build(unittest.TestCase):
    now = datetime(2026, 11, 3, 21, 0, tzinfo=D.IST)

    def test_alerts_come_first(self):
        text, alerts = D.build(self.now, [None, "chat: provider says “trial has ended”"], ["Actions failing: quality"], ["fix x"], ["A143"])
        self.assertEqual(len(alerts), 2)
        self.assertLess(text.index("⚠️ ALERTS"), text.index("Code changes"))
        self.assertIn("A143", text)

    def test_all_clear(self):
        text, alerts = D.build(self.now, [None, None], [], [], [])
        self.assertEqual(alerts, [])
        self.assertIn("No alerts", text)
        self.assertLessEqual(len(text), 3900)


if __name__ == "__main__":
    unittest.main()
