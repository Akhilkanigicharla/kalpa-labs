"""A201 check: clips.json is sound, each MP4 is 1080x1920 and under 60 s, then build a contact sheet.

Usage: python3 check_clips.py <dir with MP4s>   (writes contact-sheet.png there)
"""
import ast
import json
import operator
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_S = 60
TELUGU = range(0x0C00, 0x0C80)
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def calc(expr):
    """Arithmetic only (numbers, + - * /, brackets); anything else raises ValueError. No dynamic code."""
    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](walk(n.left), walk(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -walk(n.operand)
        raise ValueError(f"not plain arithmetic: {expr!r}")
    try:
        return walk(ast.parse(str(expr), mode="eval"))
    except SyntaxError as e:
        raise ValueError(f"not plain arithmetic: {expr!r}") from e


def check_data(data):
    """Return a list of problems in clips.json (empty = ok)."""
    bad = []
    clips = data.get("clips", [])
    if len(clips) != 3:
        bad.append(f"need 3 clips, got {len(clips)}")
    for c in clips:
        cid = c.get("id", "?")
        for k in ("title_en", "title_te", "steps"):
            if not c.get(k):
                bad.append(f"{cid}: missing {k}")
        if not any(ord(ch) in TELUGU for ch in c.get("title_te", "")):
            bad.append(f"{cid}: title_te has no Telugu script")
        for i, s in enumerate(c.get("steps", [])):
            for k in ("en", "te", "math"):
                if not str(s.get(k, "")).strip():
                    bad.append(f"{cid} step {i + 1}: missing {k}")
            if not any(ord(ch) in TELUGU for ch in s.get("te", "")):
                bad.append(f"{cid} step {i + 1}: te has no Telugu script")
            if "check" in s:
                expr, want = s["check"]
                try:
                    got = calc(expr)
                except (ValueError, ZeroDivisionError):
                    bad.append(f"{cid} step {i + 1}: unsafe check expr")
                    continue
                if abs(got - want) > 1e-9:
                    bad.append(f"{cid} step {i + 1}: {expr} = {got}, not {want}")
    return bad


def probe(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(mp4)],
                         capture_output=True, text=True, timeout=60, check=True).stdout
    j = json.loads(out)
    st = j["streams"][0]
    return st["width"], st["height"], float(j["format"]["duration"])


def check_video(mp4, max_s=MAX_S):
    if not Path(mp4).is_file() or Path(mp4).stat().st_size == 0:
        return [f"{mp4}: missing or empty"]
    w, h, d = probe(mp4)
    bad = []
    if (w, h) != (1080, 1920):
        bad.append(f"{Path(mp4).name}: {w}x{h}, want 1080x1920")
    if not 0 < d < max_s:
        bad.append(f"{Path(mp4).name}: {d:.1f} s, want under {max_s} s")
    return bad


def contact_sheet(mp4s, out_png):
    """One row per clip, 5 frames each (10/30/50/70/90 % of the clip), scaled to 216x384."""
    rows = []
    tmp = Path(out_png).parent
    for n, mp4 in enumerate(mp4s):
        d = probe(mp4)[2]
        frames = []
        for k, frac in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
            f = tmp / f".cs-{n}-{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * frac:.2f}", "-i", str(mp4),
                            "-frames:v", "1", "-vf", "scale=216:384", str(f)], check=True, timeout=60)
            frames.append(f)
        row = tmp / f".cs-row-{n}.png"
        args = sum((["-i", str(f)] for f in frames), [])
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex",
                        f"hstack=inputs={len(frames)}", str(row)], check=True, timeout=60)
        rows.append(row)
    args = sum((["-i", str(r)] for r in rows), [])
    vf = ["-filter_complex", f"vstack=inputs={len(rows)}"] if len(rows) > 1 else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, *vf, str(out_png)], check=True, timeout=60)
    for p in tmp.glob(".cs-*.png"):
        p.unlink()
    return out_png


def main(argv):
    data = json.loads((HERE / "clips.json").read_text(encoding="utf-8"))
    bad = check_data(data)
    if len(argv) > 1:
        d = Path(argv[1])
        mp4s = [d / f"{c['id']}.mp4" for c in data["clips"]]
        for m in mp4s:
            bad += check_video(m)
        if not bad:
            contact_sheet(mp4s, d / "contact-sheet.png")
            for m in mp4s:
                print(f"{m.name}: {probe(m)[2]:.1f} s")
    if bad:
        print("FAIL\n- " + "\n- ".join(bad))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
