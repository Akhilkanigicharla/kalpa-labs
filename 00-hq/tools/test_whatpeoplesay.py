#!/usr/bin/env python3
"""A197 tests: blocked sources and person queries are refused; findings always cite links."""
import datetime as dt, json, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whatpeoplesay as w

NOW = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)


def fake_get(url, headers=None):
    if "algolia" in url:
        assert "created_at_i%3E" in url  # 30-day window sent
        return {"hits": [{"objectID": "1", "title": "Salon bot <b>story</b>", "created_at": "2026-11-01T00:00:00Z", "points": 5, "author": "someone"}]}
    if "api.github.com" in url:
        return {"items": [{"title": "[Bug] Booking\nfails", "html_url": "https://github.com/o/r/issues/1", "created_at": "2026-11-02T00:00:00Z", "reactions": {"total_count": 2}, "user": {"login": "x"}}]}
    if "reddit.com" in url:
        raise OSError("HTTP 403")
    raise AssertionError("unexpected host " + url)


class Guard(unittest.TestCase):
    def test_blocked_sources_refused(self):
        for s in (["instagram"], ["x"], ["reddit", "tiktok"], ["facebook"]):
            with self.assertRaises(w.Refused):
                w.check_sources(s)
        self.assertEqual(w.check_sources(["reddit", "hackernews", "youtube", "github"]), ["reddit", "hackernews", "youtube", "github"])

    def test_person_and_blocked_queries_refused(self):
        bad = ["Ravi Kumar salon reviews", "@somehandle complaints", "who is the owner of glow salon",
               "instagram salon bookings", "phone number of gym owner", "salon on google maps",
               "justdial gym list", "sri ramesh garu trading", "https://x.com/foo", "Elon Musk ai bill", ""]
        for q in bad:
            with self.assertRaises(w.Refused, msg=q):
                w.check_query(q)

    def test_topic_queries_pass(self):
        for q in ("salon whatsapp booking bot", "tgpsc group exam preparation", "llm api bill too high startup", "sebi retail algo trading rules"):
            self.assertEqual(w.check_query(q), q)

    def test_every_configured_topic_passes(self):
        worlds = json.load(open(w.TOPICS))["worlds"]
        self.assertEqual(sorted(worlds), ["b1", "b2", "b3", "b4", "b5", "b6", "b7"])
        for world in worlds.values():
            for q in world["queries"]:
                w.check_query(q)


class Run(unittest.TestCase):
    def test_findings_cite_links_no_authors_and_one_source_down_is_noted(self):
        world = {"name": "BotBhai", "queries": ["salon whatsapp booking bot", "Ravi Kumar salon"]}
        os.environ.pop("YOUTUBE_API_KEY", None)
        findings, notes = w.research_world("b1", world, NOW, get=fake_get)
        self.assertEqual({f["source"] for f in findings}, {"hackernews", "github"})
        for f in findings:
            self.assertTrue(f["url"].startswith("https://"))
            self.assertNotIn("author", f); self.assertNotIn("user", f)
        self.assertTrue(any("refused query `Ravi Kumar salon`" in n for n in notes))
        self.assertTrue(any(n.startswith("reddit") and "403" in n for n in notes))
        self.assertTrue(any("youtube: skipped" in n for n in notes))
        md = w.render("b1", world, findings, notes, NOW)
        self.assertIn("](https://news.ycombinator.com/item?id=1)", md)
        self.assertIn("Salon bot story", md)
        self.assertNotIn("someone", md)
        self.assertIn("- [(Bug) Booking fails](https://github.com/o/r/issues/1)", md)

    def test_blocked_source_stops_run(self):
        with self.assertRaises(w.Refused):
            w.research_world("b1", {"name": "x", "queries": ["a b"]}, NOW, sources=("instagram",), get=fake_get)


if __name__ == "__main__":
    unittest.main()
