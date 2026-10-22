#!/usr/bin/env python3
"""Run: /home/claude/venv-reel/bin/python 00-hq/tools/reel/test_reel_frames.py
Makes a 6 s test video with 3 scenes of text, then checks frames, scene detection, OCR, sheets, report and the URL guard."""
import json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import reel_frames as R

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ok = 0
def check(cond, msg):
    global ok
    assert cond, msg; ok += 1; print("  ✓", msg)

with tempfile.TemporaryDirectory() as d:
    d = Path(d); vid = d / "reel.mp4"
    parts = []
    for i, (col, word) in enumerate([("0x1D3A25", "KALPA"), ("0x6B4226", "TREE"), ("0xC38E12", "FRUIT")]):
        parts += ["-f", "lavfi", "-i", f"color=c={col}:s=360x640:d=2:r=25,drawtext=fontfile={FONT}:text={word}:fontcolor=white:fontsize=72:x=(w-tw)/2:y=(h-th)/2"]
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *parts, "-f", "lavfi", "-i", "sine=f=440:d=6",
                    "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3", "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(vid)], check=True)

    rep = R.build(vid, d / "out", every=1.0, audio=False)
    check(5.5 < rep["duration"] < 6.5 and rep["width"] == 360, f"probe reads 6 s, 360 px ({rep['duration']:.1f}s)")
    check(rep["scene_changes"] >= 2, f"finds the 2 scene cuts ({rep['scene_changes']})")
    check(5 <= rep["frames"] <= 7, f"one frame per second, cuts merged ({rep['frames']} frames)")
    text = " ".join(f["text"] for f in rep["timeline"]).upper()
    check(all(w in text for w in ("KALPA", "TREE", "FRUIT")), "reads the on-screen words of all 3 scenes")
    check(sum(1 for f in rep["timeline"] if f["text"]) == 3, "repeated on-screen text is shown once per scene")
    check(rep["sheets"] == ["sheet_01.jpg"] and (d / "out/sheet_01.jpg").exists(), "makes one contact sheet")
    md = (d / "out/report.md").read_text()
    check("## Timeline" in md and "FRUIT" in md.upper(), "report.md has the timeline")
    check(json.loads((d / "out/report.json").read_text())["frames"] == rep["frames"], "report.json matches")

    capped = R.build(vid, d / "cap", every=0.5, max_frames=4, audio=False)
    check(capped["frames"] == 4, "--max caps the frame count evenly")

    for bad in ("https://www.instagram.com/reel/x/", "http://fb.watch/abc", str(d / "nope.mp4"), __file__):
        try:
            R.check_input(bad); check(False, f"rejects {bad}")
        except SystemExit:
            check(True, f"rejects {Path(bad).name if not bad.startswith('http') else bad[:28]}")

    try:
        import faster_whisper  # noqa: F401
        if Path("/home/claude/whisper").exists():
            rep2 = R.build(vid, d / "aud", every=2.0, audio=True)
            check(isinstance(rep2["speech"], list) and "(" in rep2["speech_language"], "speech step runs on a tone (no words expected)")
    except ImportError:
        print("  - Whisper not installed: speech step skipped")

print(f"reel frame tests passed ({ok} checks)")
