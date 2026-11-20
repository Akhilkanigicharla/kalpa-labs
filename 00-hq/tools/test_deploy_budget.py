"""Tests for A222 deploy_budget.py (run: python3 00-hq/tools/test_deploy_budget.py)."""
import datetime as dt, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deploy_budget as b

D = dt.date


def rows(*items):
    return [{"date": d, "site": s, "credits": c} for d, s, c in items]


class T(unittest.TestCase):
    def test_ok_fresh_cycle(self):
        r = b.check(rows((D(2026, 10, 30), "kalpa-labs", 225)), "kalpa-labs", D(2026, 11, 21))
        self.assertEqual((r["verdict"], r["used"], r["deploys_left"]), ("OK", 0, 16))

    def test_wait_second_deploy_same_day(self):
        r = b.check(rows((D(2026, 11, 21), "kalpa-labs", 15)), "kalpa-labs", D(2026, 11, 21))
        self.assertEqual(r["verdict"], "WAIT")
        r = b.check(rows((D(2026, 11, 21), "botbhai", 15)), "kalpa-labs", D(2026, 11, 21))
        self.assertEqual(r["verdict"], "OK")  # other site's deploy counts credits, not the daily rule

    def test_stop_at_cap(self):
        many = rows(*[(D(2026, 11, d), "kalpa-labs", 15) for d in range(1, 16)])  # 225
        r = b.check(many, "x", D(2026, 11, 20))
        self.assertEqual((r["verdict"], r["code"]), ("OK", 0))  # 240 exactly is allowed
        r = b.check(many + rows((D(2026, 11, 19), "y", 15)), "x", D(2026, 11, 20))
        self.assertEqual((r["verdict"], r["code"], r["deploys_left"]), ("STOP", 3, 0))

    def test_cycle_day(self):
        self.assertEqual(b.cycle_start(D(2026, 11, 3), 12), D(2026, 10, 12))
        self.assertEqual(b.cycle_start(D(2026, 3, 1), 31), D(2026, 2, 28))  # clamped to 28
        r = b.check(rows((D(2026, 11, 12), "s", 90)), "s", D(2026, 11, 21), cycle_day=13)
        self.assertEqual(r["used"], 0)

    def test_csv_hostile_rows_and_missing_file(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "d.csv")
            self.assertEqual(b.read_rows(p), [])
            with open(p, "w", encoding="utf-8") as f:
                f.write("date_ist,site,deploy_id,why,approx_credits\n"
                        "2026-11-12 23:35,ext 🚀,run 1,\"comma, quote\",0\n"
                        "not-a-date,s,x,y,15\n2026-11-13,s,x,y,abc\n2026-11-14,s,x,y,-5\n"
                        "2026-11-15,s,x,y,99999\n2026-11-16,s,x,y,\n2026-11-17,s,x,y,15\n")
            got = b.read_rows(p)
            self.assertEqual([(r["date"].day, r["credits"]) for r in got], [(12, 0), (16, 0), (17, 15)])
            self.assertEqual(b.main(["--csv", p, "--site", "s", "--today", "2026-11-18", "--json"]), 0)

    def test_real_log_parses(self):
        self.assertTrue(len(b.read_rows(b.DEFAULT_CSV)) >= 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
