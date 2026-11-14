"""A214: Telugu verdict lines, commission ranking, 5 sample deals dry-run."""
import os
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import channel  # noqa: E402
import post  # noqa: E402
import verdict as v  # noqa: E402

T = date(2026, 10, 25)
HIST = [{"date": "2026-09-20", "price": 1500}, {"date": "2026-10-05", "price": 1400},
        {"date": "2026-10-18", "price": 1800}]


def deal(**kw):
    d = {"id": "d", "price": "1299"}
    d.update(kw)
    return d


class History(unittest.TestCase):
    def line(self, price, hist=HIST, src="own-log"):
        return v.history_line("d", price, hist, src, T)

    def test_lowest_good_median_ok_above_wait(self):
        self.assertIn("అతి తక్కువ", self.line(1299))
        self.assertIn("పర్వాలేదు", self.line(1450))
        self.assertIn("ఆగండి", self.line(1700))

    def test_needs_three_recent_points_and_lawful_source(self):
        old = HIST[:2] + [{"date": "2026-01-01", "price": 900}, {"date": "2026-10-25", "price": 1}]
        for bad in [lambda: self.line(1299, old), lambda: self.line(1299, src="scraped"),
                    lambda: self.line(1299, src="http://x.in"), lambda: self.line(1299, "x"),
                    lambda: self.line(1299, [{"date": "bad", "price": 1}] * 3),
                    lambda: self.line(1299, [{"date": "2026-10-01", "price": -5}] * 3)]:
            self.assertRaises(post.GateError, bad)


class Emi(unittest.TestCase):
    def test_matches_site_calculator_formula(self):
        # fin.ts emi(100000, 12, 1) -> 8885 a month
        self.assertEqual(v.emi_cost(100000, 12, 12, 0, 0)["monthly"], 8885)

    def test_true_cost_adds_interest_fee_and_gst(self):
        c = v.emi_cost(12000, 6, 15, 199, 18)
        interest = c["monthly"] * 6 - 12000
        self.assertGreater(c["extra"], interest + 199)
        line = v.emi_line("d", 12000, {"months": 6, "rate_pa": 15, "fee": 199})
        self.assertIn("ఎక్కువ", line)
        self.assertNotRegex(line, channel.NO_COST)

    def test_zero_rate_never_says_no_cost(self):
        line = v.emi_line("d", 6000, {"months": 6, "rate_pa": 0, "fee": 0, "gst_pct": 0})
        self.assertIn("సమానం", line)
        self.assertNotRegex(line, channel.NO_COST)

    def test_bad_inputs_refused(self):
        for e in [None, {"months": 1, "rate_pa": 10}, {"months": 6, "rate_pa": -1}, {"months": 6, "rate_pa": "x"},
                  {"months": True, "rate_pa": 10}, {"months": 6, "rate_pa": 10, "fee": -1}]:
            self.assertRaises(post.GateError, v.emi_line, "d", 1000, e)

    def test_calculator_link_only_when_https_set(self):
        os.environ["DEALS_CALC_URL"] = "https://calc.kalpa.in/"
        try:
            self.assertIn("https://calc.kalpa.in/te/emi/", "\n".join(v.lines(deal(emi={"months": 3, "rate_pa": 14}), T)))
            os.environ["DEALS_CALC_URL"] = "javascript:alert(1)"
            self.assertNotIn("javascript", "\n".join(v.lines(deal(emi={"months": 3, "rate_pa": 14}), T)))
        finally:
            del os.environ["DEALS_CALC_URL"]


class Card(unittest.TestCase):
    def test_percent_capped_flat_and_min_order(self):
        self.assertIn("₹100 తగ్గింపు → మీరు కట్టేది ₹1,199", v.card_line("d", 1299, {"bank": "SBI", "pct": 10, "cap": 100}))
        self.assertIn("₹50 తగ్గింపు", v.card_line("d", 349, {"bank": "Axis", "flat": 50}))
        self.assertIn("వర్తించదు", v.card_line("d", 349, {"bank": "HDFC", "flat": 50, "min_order": 500}))
        self.assertIn("₹0", v.card_line("d", 30, {"bank": "X", "flat": 50}))  # never below zero

    def test_bad_offer_refused(self):
        for o in [{}, {"bank": " "}, {"bank": "SBI", "pct": 90, "cap": 10}, {"bank": "SBI", "pct": 10}]:
            self.assertRaises(post.GateError, v.card_line, "d", 1000, o)


class Gate(unittest.TestCase):
    def test_product_without_verdict_never_posts(self):
        self.assertRaises(post.GateError, v.lines, deal(), T)
        self.assertRaises(post.GateError, v.lines, deal(price="abc", emi={"months": 3, "rate_pa": 1}), T)

    def test_long_emoji_title_still_builds(self):
        d = {"id": "x", "kind": "product", "title_te": "🔥" * 3 + "చాలా పొడవైన పేరు " * 20, "store": "Amazon",
             "link": "https://www.amazon.in/dp/X", "price": "1299", "price_as_of": "2026-10-25 08:30",
             "card_offer": {"bank": "<b>SBI</b>", "pct": 10, "cap": 100}}
        self.assertIn(v.HEAD, channel.build(d, datetime(2026, 10, 25, 9, 0, tzinfo=post.IST)))


class Ranking(unittest.TestCase):
    def test_rates_from_amazon_page_and_unknown_is_zero(self):
        r = v.load_rates()
        self.assertEqual(r["checked"], "2026-11-14")
        self.assertEqual(v.rate_for({"store": "Amazon", "category": "Beauty"}, r), 8)
        self.assertEqual(v.rate_for({"store": "Amazon", "category": "mobile phones"}, r), 1)
        self.assertEqual(v.rate_for({"store": "Amazon", "category": "weird"}, r), 5)
        self.assertEqual(v.rate_for({"store": "Flipkart", "category": "beauty"}, r), 0)

    def test_higher_commission_first_at_equal_priority(self):
        a = {"id": "phone", "store": "Amazon", "category": "mobile phones", "date": "2026-10-25"}
        b = {"id": "shirt", "store": "Amazon", "category": "apparel", "date": "2026-10-25"}
        self.assertEqual([d["id"] for d in channel._ranked([a, b], T)], ["shirt", "phone"])
        a["priority"] = 1
        self.assertEqual([d["id"] for d in channel._ranked([a, b], T)], ["phone", "shirt"])


class SampleDryRun(unittest.TestCase):
    def test_five_sample_deals_show_the_verdict_line(self):
        deals = [d for d in channel.load_json(channel.HERE / "deals.json")["deals"] if d["kind"] == "product"]
        self.assertGreaterEqual(len(deals), 5)
        for d in deals[:5]:
            now = datetime.fromisoformat(d["price_as_of"]).replace(tzinfo=post.IST)
            msg = channel.build(d, now)
            self.assertTrue(msg.startswith("#ad"), d["id"])
            self.assertIn(v.HEAD, msg, d["id"])
            self.assertTrue(msg.splitlines()[-1].startswith("https://"), d["id"])


if __name__ == "__main__":
    unittest.main()
