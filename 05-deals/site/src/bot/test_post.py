"""Unit tests for the Deal Poster Bot (A18). Run: python3 -m unittest -v test_post.py"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post  # noqa: E402

HEAD = "id,post_at,text,link,price,price_as_of\n"
GOOD_TEXT = '"#ad · affiliate link / అనుబంధ లింక్\\nబోట్ ఇయర్‌బడ్స్ తగ్గింపు"'
NOW = post.parse_ist("2026-10-19 09:10")


def row(id="d1", post_at="2026-10-19 09:00", text=GOOD_TEXT, link="https://www.amazon.in/dp/X",
        price="1299", as_of="2026-10-19 08:30"):
    return f"{id},{post_at},{text},{link},{price},{as_of}\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.queue = self.dir / "queue.csv"
        self.sent = self.dir / "sent.log"
        self.sent_messages = []
        self.lines = []

    def write(self, *rows):
        self.queue.write_text(HEAD + "".join(rows), encoding="utf-8")

    def go(self, live=True, now=NOW):
        return post.run(self.queue, self.sent, now, live, send=self.sent_messages.append, out=self.lines.append)


class TestPosting(Base):
    def test_good_post_goes_out_with_disclosure_price_time_and_link(self):
        self.write(row())
        r = self.go()
        self.assertEqual(r["posted"], ["d1"])
        msg = self.sent_messages[0]
        lines = msg.splitlines()
        self.assertTrue(lines[0].startswith("#ad"))
        self.assertIn("affiliate link / అనుబంధ లింక్", lines[0])
        self.assertIn("₹1,299 as of 19 Oct, 8:30 am; may change / ధర మారవచ్చు", msg)
        self.assertEqual(lines[-1], "https://www.amazon.in/dp/X")

    def test_dry_run_is_default_and_sends_nothing(self):
        self.write(row())
        r = self.go(live=False)
        self.assertEqual(r["dry_run"], ["d1"])
        self.assertEqual(self.sent_messages, [])
        self.assertFalse(self.sent.exists())

    def test_posted_once_only(self):
        self.write(row())
        self.go()
        r = self.go()
        self.assertEqual(r["posted"], [])
        self.assertEqual(len(self.sent_messages), 1)

    def test_future_post_waits(self):
        self.write(row(post_at="2026-10-19 18:00"))
        self.assertEqual(self.go()["posted"], [])

    def test_slot_missed_by_hours_is_skipped(self):
        self.write(row(post_at="2026-10-19 01:00", as_of="2026-10-19 00:30"))
        r = self.go()
        self.assertEqual(r["skipped_late"], ["d1"])
        self.assertEqual(self.sent_messages, [])

    def test_posts_in_time_order(self):
        self.write(row(id="b", post_at="2026-10-19 09:05"), row(id="a", post_at="2026-10-19 08:45"))
        self.assertEqual(self.go()["posted"], ["a", "b"])

    def test_post_without_price_is_fine(self):
        self.write(row(price="", as_of=""))
        self.assertEqual(self.go()["posted"], ["d1"])
        self.assertNotIn("as of", self.sent_messages[0])


class TestDisclosureGate(Base):
    def refused(self, **kw):
        self.write(row(**kw))
        r = self.go()
        self.assertEqual(r["refused"], ["d1"], self.lines)
        self.assertEqual(self.sent_messages, [])
        return self.lines[-1]

    def test_refuses_post_without_ad(self):
        self.assertIn("#ad", self.refused(text='"బోట్ ఇయర్‌బడ్స్ తగ్గింపు"'))

    def test_refuses_ad_buried_below_line_two(self):
        self.refused(text='"Great deal\\nbuy now\\n#ad · affiliate link / అనుబంధ లింక్"')

    def test_refuses_hashtag_lookalikes(self):
        self.refused(text='"#adidas shoes affiliate link / అనుబంధ లింక్"')

    def test_refuses_ad_without_affiliate_label(self):
        self.refused(text='"#ad\\nబోట్ ఇయర్‌బడ్స్"')

    def test_refuses_price_without_time(self):
        self.refused(as_of="")

    def test_refuses_stale_price(self):
        self.assertIn("24 h", self.refused(as_of="2026-10-18 08:00"))

    def test_refuses_price_typed_in_text(self):
        self.refused(text='"#ad · affiliate link / అనుబంధ లింక్\\nఇప్పుడు ₹999 మాత్రమే"')

    def test_refuses_loan_insurance_mf_words(self):
        for word in ["Personal loan offer", "Term insurance", "Best mutual fund", "బీమా ఆఫర్"]:
            with self.subTest(word=word):
                self.sent_messages.clear()
                self.refused(text=f'"#ad · affiliate link / అనుబంధ లింక్\\n{word}"')

    def test_refuses_broker_link(self):
        self.refused(link="https://zerodha.com/open-account?c=X")

    def test_refuses_non_https_link(self):
        self.refused(link="http://www.amazon.in/dp/X")

    def test_bad_post_does_not_block_good_one(self):
        self.write(row(id="bad", text='"no disclosure"'), row(id="good"))
        r = self.go()
        self.assertEqual(r["refused"], ["bad"])
        self.assertEqual(r["posted"], ["good"])


class TestQueueFile(Base):
    def test_missing_column_is_a_queue_error(self):
        self.queue.write_text("id,post_at,text\nx,2026-10-19 09:00,hi\n", encoding="utf-8")
        with self.assertRaises(post.GateError):
            self.go()

    def test_duplicate_ids_rejected(self):
        self.write(row(), row())
        with self.assertRaises(post.GateError):
            self.go()

    def test_bad_time_rejected(self):
        self.write(row(post_at="19/10 9am"))
        with self.assertRaises(post.GateError):
            self.go()


class TestCli(unittest.TestCase):
    def test_live_without_secrets_falls_back_to_dry_run(self):
        import os
        env = {k: os.environ.pop(k) for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if k in os.environ}
        try:
            d = Path(tempfile.mkdtemp())
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = post.main(["--queue", str(post.HERE / "queue.csv"), "--sent", str(d / "s.log"),
                                  "--now", "2026-10-19 09:00", "--live"])
            self.assertEqual(code, 0)
            self.assertIn("Staying in dry run", buf.getvalue())
            self.assertIn("1 dry-run", buf.getvalue())
            self.assertFalse((d / "s.log").exists())
        finally:
            os.environ.update(env)

    def test_sample_queue_passes_the_gate(self):
        deals = post.load_queue(post.HERE / "queue.csv")
        now = post.parse_ist("2026-10-19 09:00")
        for d in deals:
            post.check(d, post.compose(d), now)


if __name__ == "__main__":
    unittest.main()
