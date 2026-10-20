"""Tests for the scheduled deals channel poster (A58). Run: python3 -m unittest -v test_channel.py"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import channel  # noqa: E402
import post  # noqa: E402

DAY = "2026-10-25"  # a Sunday, so the weekly tip slot exists
MONDAY = "2026-10-26"


def product(i, **kw):
    d = {"id": f"p{i}", "kind": "product", "title_te": f"ఇయర్‌బడ్స్ మోడల్ {i}", "store": "Amazon",
         "link": f"https://www.amazon.in/dp/X{i}", "price": "1299", "price_as_of": f"{DAY} 08:30",
         "discount_pct": 40}
    d.update(kw)
    return d


def card(**kw):
    d = {"id": "c1", "kind": "credit_card", "title_te": "షాపింగ్ క్యాష్‌బ్యాక్ కార్డ్",
         "link": "https://earnkaro.com/card/X", "joining_fee": 500, "annual_fee": 500,
         "eligibility": "వయసు 21–60, నెల జీతం ₹25,000+", "terms_url": "https://www.example.com/terms",
         "lifetime_free": False}
    d.update(kw)
    return d


TIPS = [{"id": "t1", "te": "అత్యవసర నిధి ఉంచండి.", "en": "Keep an emergency fund."},
        {"id": "t2", "te": "OTP ఎవరికీ చెప్పకండి.", "en": "Never share an OTP."}]


class Base(unittest.TestCase):
    def setUp(self):
        self.sent, self.lines, self.checked = [], [], []
        self.dead = set()
        self.state = channel.new_state()

    def link(self, url):
        self.checked.append(url)
        return "dead" if url in self.dead else "ok"

    def go(self, deals, now, tips=TIPS, live=True):
        return channel.run(deals, tips, self.state, post.parse_ist(now),
                           send=self.sent.append if live else None, check_link=self.link, out=self.lines.append)

    def day(self, deals, d=DAY, tips=TIPS):
        return channel.simulate_day(deals, tips, self.state, date.fromisoformat(d),
                                    check_link=self.link, out=self.lines.append)


class TestPlanning(Base):
    def test_full_day_posts_five_deals_in_ist_slots(self):
        r = self.day([product(i) for i in range(1, 8)])
        self.assertEqual([p["slot"] for p in r["deals"]], [f"{DAY} {s}" for s in channel.SLOTS])
        self.assertEqual(len(r["deals"]), 5)

    def test_three_deals_is_enough_and_fewer_warns(self):
        r = self.day([product(1), product(2)])
        self.assertEqual(len(r["deals"]), 2)
        self.assertTrue(any("only 2" in l for l in self.lines), self.lines)

    def test_at_most_one_credit_card_a_day(self):
        r = self.day([card(id="c1"), card(id="c2", link="https://earnkaro.com/card/Y"), product(1)])
        self.assertEqual(sorted(p["id"] for p in r["deals"]), ["c1", "p1"])

    def test_dated_deal_only_on_its_day_and_expired_deal_never(self):
        deals = [product(1, date=MONDAY), product(2, valid_until="2026-10-24"), product(3)]
        r = self.day(deals)
        self.assertEqual([p["id"] for p in r["deals"]], ["p3"])

    def test_higher_priority_first(self):
        r = self.day([product(1), product(2, priority=5)])
        self.assertEqual([p["id"] for p in r["deals"]], ["p2", "p1"])

    def test_stale_price_waits_for_no_slot(self):
        r = self.day([product(1, price_as_of="2026-10-24 08:00")])
        self.assertEqual(r["deals"], [])

    def test_weekly_tip_only_on_sunday(self):
        self.assertEqual(len(self.day([product(1)])["tips"]), 1)
        self.assertEqual(self.day([product(2, price_as_of=f"{MONDAY} 08:00")], d=MONDAY)["tips"], [])

    def test_tip_rotates_by_week_and_is_not_repeated(self):
        first = self.day([], d=DAY)["tips"][0]["id"]
        second = self.day([], d="2026-11-01")["tips"][0]["id"]
        self.assertNotEqual(first, second)


class TestMessages(Base):
    def test_product_post_has_ad_first_telugu_price_time_and_utm_link(self):
        self.go([product(1)], f"{DAY} 09:05")
        msg = self.sent[0]
        lines = msg.splitlines()
        self.assertEqual(lines[0], post.DISCLOSURE)
        self.assertIn("ఇయర్‌బడ్స్ మోడల్ 1", msg)
        self.assertIn("40% తగ్గింపు", msg)
        self.assertIn("₹1,299 as of 25 Oct, 8:30 am; may change", msg)
        self.assertTrue(lines[-1].startswith("https://www.amazon.in/dp/X1?utm_source=telegram"), lines[-1])
        self.assertIn("utm_campaign=deals-20261025", lines[-1])
        self.assertIn("utm_content=p1", lines[-1])

    def test_card_post_carries_fees_eligibility_terms_and_rbi_disclaimer(self):
        self.go([card()], f"{DAY} 09:05")
        msg = self.sent[0]
        self.assertTrue(msg.startswith(post.DISCLOSURE))
        for part in ["Joining fee: ₹500", "Annual fee: ₹500", "Eligibility", "https://www.example.com/terms",
                     channel.CARD_DISCLAIMER]:
            self.assertIn(part, msg)

    def test_tip_is_labelled_and_not_advice(self):
        self.go([], f"{DAY} 10:35")
        self.assertIn(channel.TIP_HEAD, self.sent[0])
        self.assertIn(channel.TIP_FOOT, self.sent[0])
        self.assertNotIn("#ad", self.sent[0])


class TestUtm(unittest.TestCase):
    def test_keeps_existing_query_and_fragment(self):
        u = channel.add_utm("https://www.amazon.in/dp/X?tag=kalpa-21#top", "d1", date(2026, 10, 25))
        self.assertTrue(u.startswith("https://www.amazon.in/dp/X?tag=kalpa-21&utm_source=telegram"), u)
        self.assertTrue(u.endswith("#top"))

    def test_does_not_override_existing_utm(self):
        u = channel.add_utm("https://a.in/x?utm_source=mine", "d1", date(2026, 10, 25))
        self.assertEqual(u.count("utm_source"), 1)
        self.assertIn("utm_source=mine", u)

    def test_short_links_are_left_alone(self):
        self.assertEqual(channel.add_utm("https://ekaro.in/abc", "d1", date(2026, 10, 25)), "https://ekaro.in/abc")

    def test_normalise_strips_utm_and_case(self):
        self.assertEqual(channel.normalise("https://WWW.Amazon.in/dp/X/?utm_source=t&tag=a"),
                         "https://www.amazon.in/dp/X?tag=a")


class TestGuards(Base):
    def test_duplicate_id_or_url_from_another_day_is_skipped(self):
        self.go([product(1)], f"{DAY} 09:05")
        again = [product(1, price_as_of=f"{MONDAY} 08:30"),
                 product(9, link="https://www.amazon.in/dp/X1?utm_source=x", price_as_of=f"{MONDAY} 08:30")]
        self.go(again, f"{MONDAY} 09:05")
        self.assertEqual(len(self.sent), 1)

    def test_same_slot_is_not_posted_twice(self):
        self.go([product(1), product(2)], f"{DAY} 09:05")
        self.go([product(1), product(2)], f"{DAY} 09:40")
        self.assertEqual(len(self.sent), 1)

    def test_dead_link_is_skipped_and_next_deal_takes_the_slot(self):
        self.dead.add("https://www.amazon.in/dp/X1")
        self.go([product(1), product(2)], f"{DAY} 09:05")
        self.assertEqual(len(self.sent), 1)
        self.assertIn("X2", self.sent[0])
        self.assertIn("p1", [d["id"] for d in self.state["dead"]])

    def test_unknown_link_status_still_posts(self):
        self.go([product(1)], f"{DAY} 09:05")
        self.assertEqual(self.checked, ["https://www.amazon.in/dp/X1"])
        self.link = lambda url: "unknown"
        self.go([product(2)], f"{DAY} 12:35")
        self.assertEqual(len(self.sent), 2)

    def test_missed_slot_beyond_grace_is_not_posted_late(self):
        self.go([product(1)], f"{DAY} 11:30", tips=[])
        self.assertEqual(self.sent, [])

    def test_catches_up_two_due_slots_in_one_run(self):
        self.go([product(i) for i in range(1, 4)], f"{DAY} 12:40")
        self.assertEqual(len(self.sent), 1)  # 09:00 is more than 2 h old, only 12:30 goes
        self.go([product(i) for i in range(1, 4)], f"{DAY} 18:00")
        self.assertEqual(len(self.sent), 2)

    def test_sample_deals_never_post_live(self):
        self.go([product(1, sample=True)], f"{DAY} 09:05")
        self.assertEqual(self.sent, [])

    def test_dry_run_sends_nothing_and_checks_no_links(self):
        r = self.go([product(1)], f"{DAY} 09:05", live=False)
        self.assertEqual(self.sent, [])
        self.assertEqual(self.checked, [])
        self.assertEqual(r["dry_run"], ["p1"])


class TestCompliance(Base):
    def refused(self, deal):
        r = self.day([deal])
        self.assertEqual(r["deals"], [], self.lines)
        self.assertTrue(any("REFUSED" in l for l in self.lines), self.lines)

    def test_card_must_go_through_earnkaro_or_bankkaro(self):
        self.refused(card(link="https://www.hdfcbank.com/apply"))

    def test_card_needs_fees_eligibility_and_https_terms(self):
        for k in ["joining_fee", "annual_fee", "eligibility", "terms_url"]:
            with self.subTest(k=k):
                self.lines.clear()
                d = card()
                d.pop(k)
                self.refused(d)
        self.lines.clear()
        self.refused(card(terms_url="http://www.example.com/terms"))

    def test_free_only_if_lifetime_free(self):
        self.refused(card(title_te="ఫ్రీ కార్డ్"))
        self.lines.clear()
        self.refused(card(note_te="No annual fee, totally free"))
        self.lines.clear()
        self.refused(card(lifetime_free=True))  # fees are not 0
        self.lines.clear()
        r = self.day([card(lifetime_free=True, joining_fee=0, annual_fee=0, title_te="లైఫ్‌టైమ్ ఫ్రీ కార్డ్")])
        self.assertEqual(len(r["deals"]), 1, self.lines)

    def test_no_cost_emi_wording_refused(self):
        self.refused(product(1, note_te="No-cost EMI available"))
        self.lines.clear()
        self.refused(product(1, note_te="నో కాస్ట్ EMI"))

    def test_loan_and_broker_still_refused(self):
        self.refused(product(1, title_te="Personal loan offer"))
        self.lines.clear()
        self.refused(product(1, link="https://zerodha.com/x"))

    def test_rupee_in_copy_refused(self):
        self.refused(product(1, note_te="ఇప్పుడు ₹999 మాత్రమే"))

    def test_bad_deal_does_not_block_good_ones(self):
        r = self.day([product(1, title_te="loan"), product(2)])
        self.assertEqual([p["id"] for p in r["deals"]], ["p2"])

    def test_tip_with_banned_words_refused(self):
        r = self.day([], tips=[{"id": "x", "te": "guaranteed return!", "en": "x"}])
        self.assertEqual(r["tips"], [])


class TestFiles(unittest.TestCase):
    def test_duplicate_ids_and_unknown_kind_are_file_errors(self):
        for bad in [[product(1), product(1)], [product(1, kind="loan")], [{"id": "x"}]]:
            with self.subTest(bad=bad), self.assertRaises(post.GateError):
                channel.validate_deals(bad)

    def test_sample_files_load_and_fill_a_sunday(self):
        deals = channel.load_json(channel.HERE / "deals.json")["deals"]
        tips = channel.load_json(channel.HERE / "tips.json")["tips"]
        channel.validate_deals(deals)
        r = channel.simulate_day(deals, tips, channel.new_state(), date(2026, 10, 25),
                                 check_link=lambda u: "ok", out=lambda *_: None)
        self.assertGreaterEqual(len(r["deals"]), 3)
        self.assertEqual(len(r["tips"]), 1)
        self.assertTrue(any(p["kind"] == "credit_card" for p in r["deals"]))
        self.assertTrue(all(d.get("sample") for d in deals), "sample file must mark every deal sample")

    def test_cli_day_dry_run_and_live_without_secrets(self):
        env = {k: os.environ.pop(k) for k in channel.SECRET_NAMES + ["DEALS_LIVE"] if k in os.environ}
        try:
            tmp = Path(tempfile.mkdtemp())
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = channel.main(["--day", DAY, "--state", str(tmp / "s.json")])
            self.assertEqual(code, 0, buf.getvalue())
            self.assertIn("#ad", buf.getvalue())
            self.assertIn(channel.TIP_HEAD, buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = channel.main(["--live", "--now", f"{DAY} 09:05", "--state", str(tmp / "s.json")])
            self.assertEqual(code, 0, buf.getvalue())
            self.assertIn("dry run", buf.getvalue().lower())
            self.assertFalse((tmp / "s.json").exists())
        finally:
            os.environ.update(env)

    def test_state_round_trip(self):
        tmp = Path(tempfile.mkdtemp()) / "s.json"
        s = channel.new_state()
        s["posted"].append({"id": "a", "url": "https://x.in/a", "slot": f"{DAY} 09:00", "at": "x"})
        channel.save_state(tmp, s)
        self.assertEqual(channel.load_state(tmp), s)
        self.assertEqual(channel.load_state(tmp.with_name("missing.json")), channel.new_state())
        self.assertEqual(json.loads(tmp.read_text())["posted"][0]["id"], "a")


class TestLinkCheck(unittest.TestCase):
    def test_statuses(self):
        import urllib.error

        def opener(code=None, exc=None):
            calls = []

            def f(req, timeout):
                calls.append(req.get_method())
                if exc:
                    raise exc
                if code >= 400:
                    raise urllib.error.HTTPError(req.full_url, code, "x", {}, None)
                return io.BytesIO(b"")
            f.calls = calls
            return f
        self.assertEqual(channel.link_status("https://a.in", opener=opener(200)), "ok")
        self.assertEqual(channel.link_status("https://a.in", opener=opener(404)), "dead")
        self.assertEqual(channel.link_status("https://a.in", opener=opener(410)), "dead")
        self.assertEqual(channel.link_status("https://a.in", opener=opener(503)), "unknown")
        o = opener(405)
        self.assertEqual(channel.link_status("https://a.in", opener=o), "unknown")
        self.assertEqual(o.calls, ["HEAD", "GET"])
        self.assertEqual(channel.link_status("https://a.in", opener=opener(exc=urllib.error.URLError("dns"))), "dead")
        self.assertEqual(channel.link_status("https://a.in", opener=opener(exc=TimeoutError())), "dead")


if __name__ == "__main__":
    unittest.main()
