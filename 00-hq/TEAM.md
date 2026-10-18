# Two build sessions, one roadmap (set up 18 Oct 2026)

Akhil runs two Claude cloud sessions on this repo at the same time. GitHub `main` is the only shared state: there is no other link between them. Split the Agent queue by lane so they never build the same thing.

## Lanes

| Lane | Who | Items (in order) |
|---|---|---|
| **A** | session `kalpa-labs-a5` (this file's author) | b7 A26 → b6 A28, A30, A31, A33 |
| **B** | the other cloud session | b2 A35, A36, A37 → b4 A40 → b1 A49, A50, A51 → design A52 |

New items added later: the lane whose world it is takes it (b6/b7 → A; b1/b2/b3/b4/b5/HQ/design → B).

## Rules for both sessions
1. **Pull first:** `git fetch origin main && git rebase origin/main` before choosing work and before every push.
2. **Claim before building:** add ` (claimed: lane A|B, YYYY-MM-DD)` to the item's ROADMAP line, mark it `[~]`, commit and push at once. A `[~]` item claimed by the other lane is not yours, even though CLAUDE.md says "resume `[~]` first".
3. **Stay in your folders.** Lane A touches `06-finops/`, `07-trading/` and their workflows; lane B touches `01-`…`05-`, `00-hq/design/`. Shared files (ROADMAP.md, log, LINKS.md) get small line edits or appends only, so rebases merge cleanly.
4. **Log with your lane:** start each log entry with `Lane A` or `Lane B`.
5. **Finished your lane?** Take the other lane's last unclaimed item (from the bottom), claiming it first.
6. Rebase conflict in a shared file: keep both sides' lines, never drop the other lane's ticks.
