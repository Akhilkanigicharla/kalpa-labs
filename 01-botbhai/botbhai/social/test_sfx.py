"""A196 tests for social/sfx.py. No network, no earshot: a fake renderer and a fake Openverse. Needs ffmpeg + numpy.
Run: python3 social/test_sfx.py"""
import json
import pathlib
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sfx  # noqa: E402


class W:
    def __init__(self, start, end, text):
        self.start, self.end, self.text = start, end, text


def tone(f, dur, attack=0.004, rise=False):
    t = np.arange(int(dur * sfx.SR)) / sfx.SR
    env = np.minimum(t / attack, 1) * np.exp(-t * 6) if not rise else np.sin(np.pi * t / dur) ** 2
    return 0.6 * env * np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 7 * t))


def fake_render(sound_id, out):
    sfx.write_wav(out, np.concatenate([np.zeros(sfx.SR // 50),
                                       tone(1800 if "whoosh" in sound_id else 900, 0.4, rise="whoosh" in sound_id)]))
    return out


SCRIPT = [(0.40, "Book"), (0.70, "in"), (0.90, "2"), (1.10, "taps."), (2.00, "First,"), (2.40, "pick"),
          (3.20, "₹99"), (4.30, "No"), (4.60, "mistakes,"), (5.60, "done!")]


def voice_and_words(path):
    rng = np.random.default_rng(7)
    v = np.zeros(int(7 * sfx.SR))
    words = []
    for s, txt in SCRIPT:
        n = int(0.25 * sfx.SR)
        a = int(s * sfx.SR)
        v[a:a + n] += 0.3 * rng.standard_normal(n) * np.hanning(n)
        words.append(W(s, s + 0.25, txt))
    sfx.write_wav(path, v)
    return words


def test_plan():
    cues = sfx.plan_cues([W(s, s + 0.2, t) for s, t in SCRIPT])
    assert [c["kind"] for c in cues] == ["pop", "whoosh", "chime", "thud", "click"], cues
    assert cues[0]["t"] == 0.9 and cues[2]["word"] == "₹99"
    close = sfx.plan_cues([W(0.0, 0.1, "5"), W(0.3, 0.4, "6"), W(1.0, 1.1, "7")])
    assert [c["t"] for c in close] == [0.0, 1.0], close            # min gap 0.8 s
    many = sfx.plan_cues([W(i, i + 0.1, str(i)) for i in range(30)])
    assert len(many) == sfx.MAX_CUES
    te = sfx.plan_cues([W(0, .1, "మొదట"), W(1, 1.1, "500"), W(2, 2.1, "రూపాయలు"), W(3, 3.1, "जाग"), W(4, 4.1, "गलती")])
    assert [c["kind"] for c in te] == ["whoosh", "pop", "chime", "thud"], te
    assert sfx.plan_cues([W(0, .1, "hello"), W(1, 1.1, "world")]) == []


def test_sync_point():
    pop = np.concatenate([np.zeros(480), tone(900, 0.3)])
    assert abs(sfx.sync_point(pop, "onset") - 480) < 0.002 * sfx.SR
    sw = tone(1800, 0.4, rise=True)
    assert abs(sfx.sync_point(sw, "peak") - 0.2 * sfx.SR) < 0.01 * sfx.SR


def test_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        words = voice_and_words(d / "v.wav")
        rep = sfx.run(d / "v.wav", words, d / "out", render=fake_render)
        assert rep["pass"], json.dumps({k: rep[k] for k in rep if k != "cues"})
        assert len(rep["cues"]) == 5 and rep["max_err_ms"] <= 33.3
        assert rep["max_under_voice_db"] <= sfx.CLEAR_DB
        assert abs(rep["mp4_audio_offset_ms"]) <= 33.3
        for f in ("reel-sfx.mp4", "mix.wav", "sfx-stem.wav", "credits.txt", "report.json"):
            assert (d / "out" / f).stat().st_size > 0, f
        assert "Synthesised sounds:" in (d / "out" / "credits.txt").read_text()


def test_checks_catch_errors():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        words = voice_and_words(d / "v.wav")
        voice = sfx.read_audio(d / "v.wav")
        cues = sfx.plan_cues(words)
        takes, _ = sfx.get_takes([c["kind"] for c in cues], d, {}, fake_render)
        stem, placed = sfx.build_stem(voice, cues, takes)
        assert max(sfx.measure_sync(stem, placed, takes)) <= sfx.FRAME_S
        late = np.concatenate([np.zeros(int(0.06 * sfx.SR)), stem])[: len(stem)]     # 60 ms late: must fail
        assert min(sfx.measure_sync(late, placed, takes)) > sfx.FRAME_S
        assert max(sfx.clarity(voice, stem * 10, placed)) > sfx.CLEAR_DB              # 20 dB louder: must fail
        shifted = np.concatenate([np.zeros(int(0.1 * sfx.SR)), voice])
        assert abs(sfx.av_offset(voice, shifted) - 0.1) < 0.002


def test_openverse_credit_and_fallback():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        sfx.write_wav(d / "rec.wav", tone(600, 0.5))
        api = {"results": [{"license": "by", "url": "x"}, {"license": "cc0", "url": "https://cdn/rec.wav",
               "title": "cash register", "creator": "someone", "foreign_landing_url": "https://freesound.org/s/1"}]}
        seen = []

        def fetch(url):
            seen.append(url)
            return json.dumps(api).encode() if "api.openverse.org" in url else (d / "rec.wav").read_bytes()
        words = voice_and_words(d / "v.wav")
        rep = sfx.run(d / "v.wav", words, d / "o1", {"chime": "cash register"}, fake_render, fetch, make_mp4=False)
        assert rep["pass"] and "license=cc0" in seen[0], seen
        cred = (d / "o1" / "credits.txt").read_text()
        assert 'chime: "cash register" by someone, CC0 1.0, https://freesound.org/s/1' in cred, cred

        def down(url):
            raise OSError("offline")
        rep = sfx.run(d / "v.wav", words, d / "o2", {"chime": "cash register"}, fake_render, down, make_mp4=False)
        assert rep["pass"] and "Openverse failed" in rep["notes"][0], rep["notes"]
        assert "used the synthesised sound" in (d / "o2" / "credits.txt").read_text()


def test_own_synth_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        for kind, sid, *_ in sfx.RULES:
            x = sfx.read_audio(sfx.synth_render(sid, d / f"{kind}.wav"))
            assert 0.03 < len(x) / sfx.SR < 0.6 and 0.5 < np.abs(x).max() <= 0.71, kind
        if not sfx.shutil.which("earshot"):
            assert sfx.auto_render()[0] is sfx.synth_render
        words = voice_and_words(d / "v.wav")
        rep = sfx.run(d / "v.wav", words, d / "out", render=sfx.synth_render)
        assert rep["pass"] and rep["sounds"] == sfx.OWN, {k: rep[k] for k in rep if k != "cues"}
        assert "own synthesised" in (d / "out" / "credits.txt").read_text()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} sfx tests passed")
