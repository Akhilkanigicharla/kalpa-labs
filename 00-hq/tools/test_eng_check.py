"""Tests for eng_check world ids (A328): b1–b7 expand, unknown names exit 2, b2 covers the three apps with 0 FAIL."""
import pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import eng_check as e

TOOL = str(pathlib.Path(__file__).parent / "eng_check.py")


def test_groups_cover_only_known_worlds():
    for gid, names in e.GROUPS.items():
        assert names and all(n in e.WORLDS for n in names), gid
    assert set(e.WORLDS) <= {n for v in e.GROUPS.values() for n in v}   # every world reachable by an id


def test_expand():
    assert e.expand(["b2"]) == ["jobcard", "jyotish", "photo-studio", "bhasha-kids"]
    assert e.expand(["jobcard", "b2"]) == ["jobcard", "jyotish", "photo-studio", "bhasha-kids"]   # no duplicates
    assert e.expand([]) == list(e.WORLDS)


def test_unknown_world_exits_2_with_message():
    r = subprocess.run([sys.executable, TOOL, "b9"], capture_output=True, text=True)
    assert r.returncode == 2 and "unknown world 'b9'" in r.stderr and "b2" in r.stderr


def test_b2_apps_have_no_fail():
    for n in ["jyotish", "photo-studio", "bhasha-kids"]:
        res = e.run(n)
        assert res and not [x for x in res if x[1] == "FAIL"], (n, res)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("eng_check tests: 4 passed")
