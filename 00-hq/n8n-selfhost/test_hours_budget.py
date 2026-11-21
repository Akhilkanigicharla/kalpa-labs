import unittest
from hours_budget import awake_hours_per_day, budget, crons, main


class T(unittest.TestCase):
    def test_current_window(self):
        # old cron: 16 and 18 min gaps > 15 min idle, so Render slept between pings
        self.assertEqual(awake_hours_per_day("7,23,41,53 0-18 * * *"), 17.75)
        # new cron: every gap <= 14 min, 00:03..18:59 UTC + 15 min tail
        self.assertEqual(awake_hours_per_day("3,17,31,45,59 0-18 * * *"), 19.18)

    def test_every_5_min_all_day_is_24h(self):
        self.assertEqual(awake_hours_per_day("*/5 * * * *".replace("*/5", ",".join(str(m) for m in range(0, 60, 5)))), 24.0)

    def test_single_ping_is_15_min(self):
        self.assertEqual(awake_hours_per_day("0 3 * * *"), 0.25)

    def test_24_7_does_not_fit(self):
        self.assertFalse(budget(24.0)[1])

    def test_current_fits(self):
        used, ok = budget(19.0)
        self.assertTrue(ok)
        self.assertEqual(used, 682.0)

    def test_cron_parse_and_main(self):
        self.assertEqual(crons('- cron: "1 2 * * *"\n'), ["1 2 * * *"])
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
