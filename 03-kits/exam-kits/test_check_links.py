"""Offline tests for check_links.py (no network). Run: python3 03-kits/exam-kits/test_check_links.py"""
import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import check_links as C

EXAM = {"id": "x", "official_url": "https://ssc.gov.in",
        "resources": {"official": [{"url": "https://ssc.gov.in"}], "mocks": [{"url": "https://m.example/a"}],
                      "channels": [{"url": "https://www.youtube.com/@abc"}]},
        "topic_videos": {"t1": {"url": "https://www.youtube.com/watch?v=abcdefghijk"}, "t2": {"url": "https://www.youtube.com/watch?v=abcdefghijk"}}}


class T(unittest.TestCase):
    def test_links_deduped_and_complete(self):
        ls = C.links(EXAM)
        self.assertEqual(len(ls), 4)  # official twice → once, video twice → once
        self.assertIn(("video", "https://www.youtube.com/watch?v=abcdefghijk"), ls)

    def test_videos_go_through_oembed(self):
        self.assertTrue(C.probe_url("video", "https://www.youtube.com/watch?v=abcdefghijk").startswith("https://www.youtube.com/oembed?"))
        self.assertEqual(C.probe_url("mocks", "https://m.example/a"), "https://m.example/a")

    def test_broken_link_reported(self):
        rep = C.check([EXAM], get=lambda u: 404 if "m.example" in u else 200)
        bad = [r for r in rep["x"] if not r["ok"]]
        self.assertEqual([r["url"] for r in bad], ["https://m.example/a"])


if __name__ == "__main__":
    unittest.main()
