# Run: python3 tools/test_cards.py  (offline) — smile cards use the Kalamkari system (A01b)
import pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import cards as C
from PIL import Image

assert C.FONTS.is_dir() and C.FONTS.parts[-3:] == ("00-hq", "design", "fonts"), C.FONTS
src = pathlib.Path(C.__file__).read_text()
for f in ["rozha-one-latin-400-normal.woff", "anek-latin-latin-700-normal.woff", "anek-telugu-telugu-700-normal.woff"]:
    assert (C.FONTS / f).exists() and f in src, f
for old in ["anton", "baloo", "noto-sans-telugu"]:
    assert old not in src.split('"""', 2)[2].lower(), "old font still used: " + old
tokens = (C.ROOT.parent.parent / "00-hq/design/tokens.css").read_text().upper()
for setup, (bg, accent, deep) in C.THEMES.items():
    for rgb in (bg, accent, deep):
        assert "#%02X%02X%02X" % rgb in tokens, (setup, "colour not a Kalamkari token", rgb)

with tempfile.TemporaryDirectory() as d:
    n = 0
    for setup in C.CARDS:
        for p in C.build(setup, "Glow Studio", d):
            im = Image.open(p).convert("RGB"); n += 1
            assert im.size == (1080, 1080) and p.stat().st_size < 300_000, (p.name, im.size, p.stat().st_size)
            # temple border: madder teeth at the very top and bottom edge
            assert im.getpixel((3, 1)) == C.MADDER and im.getpixel((3, 1078)) == C.MADDER, p.name
print(f"  ✓ {n} smile cards: 1080², < 300 KB, Kalamkari fonts + token colours + temple border")
print("cards tests passed")
