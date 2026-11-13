"""Every SKILL.md must have front matter with a name and a description, or Claude Code
cannot load it. Idea from steipete/agent-scripts `validate-skills` (MIT); our own code."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def skill_files():
    return [p for p in ROOT.rglob("SKILL.md") if "node_modules" not in p.parts and ".git" not in p.parts]


def test_every_skill_has_name_and_description():
    files = skill_files()
    assert files, "no SKILL.md files found"
    bad = []
    for p in files:
        m = re.match(r"^---\r?\n(.*?)\r?\n---", p.read_text(encoding="utf-8", errors="replace"), re.S)
        fm = m.group(1) if m else ""
        if not (re.search(r"^name:\s*\S", fm, re.M) and re.search(r"^description:\s*\S", fm, re.M)):
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f"SKILL.md without name/description: {bad}"
