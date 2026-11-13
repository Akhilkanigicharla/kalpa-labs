"""A201 tests: clip data checks + video checks on tiny ffmpeg test videos (no Manim needed)."""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_clips as cc

DATA = json.loads((Path(__file__).parent / "clips.json").read_text(encoding="utf-8"))


def make_video(path, w, h, seconds):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=#F2EEE3:s={w}x{h}:d={seconds}:r=10",
                    "-pix_fmt", "yuv420p", str(path)], check=True, timeout=60)


class Data(unittest.TestCase):
    def test_real_data_passes(self):
        self.assertEqual(cc.check_data(DATA), [])

    def test_wrong_sum_caught(self):
        d = copy.deepcopy(DATA)
        d["clips"][0]["steps"][3]["check"] = ["30000/100", 301]
        self.assertTrue(any("not 301" in b for b in cc.check_data(d)))

    def test_hostile_expr_refused(self):
        d = copy.deepcopy(DATA)
        d["clips"][0]["steps"][3]["check"] = ["__import__('os').system('id')", 0]
        self.assertTrue(any("unsafe" in b for b in cc.check_data(d)))

    def test_missing_telugu_caught(self):
        d = copy.deepcopy(DATA)
        d["clips"][1]["steps"][0]["te"] = "Speed goes up"  # English left in the Telugu line
        self.assertTrue(any("no Telugu" in b for b in cc.check_data(d)))

    def test_calc(self):
        self.assertEqual(cc.calc("(600-500)/500*100"), 20)
        for bad in ("1/0", "2**99999", "x+1", "", "[1]"):
            with self.assertRaises((ValueError, ZeroDivisionError)):
                cc.calc(bad)

    def test_empty_and_emoji_lines(self):
        d = copy.deepcopy(DATA)
        d["clips"][2]["steps"][0]["en"] = "   "
        d["clips"][2]["steps"][1]["te"] = "🙂🙂"
        bad = cc.check_data(d)
        self.assertTrue(any("missing en" in b for b in bad))
        self.assertTrue(any("step 2: te has no Telugu" in b for b in bad))

    def test_three_clips_required(self):
        self.assertTrue(cc.check_data({"clips": DATA["clips"][:2]}))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
class Video(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_good_video(self):
        make_video(self.tmp / "a.mp4", 1080, 1920, 2)
        self.assertEqual(cc.check_video(self.tmp / "a.mp4"), [])

    def test_landscape_caught(self):
        make_video(self.tmp / "a.mp4", 1920, 1080, 2)
        self.assertTrue(any("want 1080x1920" in b for b in cc.check_video(self.tmp / "a.mp4")))

    def test_too_long_caught(self):
        make_video(self.tmp / "a.mp4", 1080, 1920, 3)
        self.assertTrue(any("under 2 s" in b for b in cc.check_video(self.tmp / "a.mp4", max_s=2)))

    def test_missing_and_empty(self):
        (self.tmp / "e.mp4").write_bytes(b"")
        self.assertTrue(cc.check_video(self.tmp / "nope.mp4"))
        self.assertTrue(cc.check_video(self.tmp / "e.mp4"))

    def test_contact_sheet(self):
        vids = []
        for n in range(3):
            make_video(self.tmp / f"{n}.mp4", 1080, 1920, 2)
            vids.append(self.tmp / f"{n}.mp4")
        png = cc.contact_sheet(vids, self.tmp / "sheet.png")
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                              str(png)], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(out, "1080,1152")  # 5 x 216 wide, 3 x 384 tall
        self.assertEqual(list(self.tmp.glob(".cs-*")), [])


if __name__ == "__main__":
    unittest.main()
