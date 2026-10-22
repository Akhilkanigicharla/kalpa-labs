# Code map (Graphify, code only)

Ask "where is X / who calls Y" from a graph instead of reading many files: about 1 KB of answer instead of several files of tokens.
[safishamsi/graphify](https://github.com/safishamsi/graphify) (`graphifyy` 0.9.93 on PyPI, Apache-2.0). Checked 22 Oct 2026: code mode is local tree-sitter parsing, no LLM, no API key; its query log is off by default; no telemetry found in the package.

```bash
python3 -m venv /home/claude/venv-graph && /home/claude/venv-graph/bin/pip install graphifyy==0.9.93   # once per cloud session
/home/claude/venv-graph/bin/graphify extract . --code-only        # whole repo: 489 files → 4,183 nodes in ~14 s
/home/claude/venv-graph/bin/graphify query "who calls book_slot"   # BFS answer with file:line
/home/claude/venv-graph/bin/graphify explain "automations.js::ownerNudges()"
/home/claude/venv-graph/bin/graphify path "dayclose.js" "ownerNudges()"
```
Output goes to `graphify-out/` (git-ignored). Rules: `--code-only` always (the docs/PDF/image mode sends files to a model); never run `graphify claude install` (it adds hooks and a CLAUDE.md section); never use Graphify Cloud or its sign-in.
