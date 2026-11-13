# Exam Kits explainer clips (A201)

Three vertical 1080x1920 clips (simple interest, speed-time graph, profit %), 24–29 s each, Kalpa light palette (b3 = `--l3`), English + Telugu captions. Built with Manim CE (MIT) and the Anek fonts (OFL). Text only, no LaTeX.

| File | What |
|---|---|
| `clips.json` | the scripts: titles, steps, captions, and `check` sums that must add up |
| `scenes.py` | Manim scenes (`SimpleInterest`, `SpeedTimeGraph`, `ProfitPercent`) |
| `render.sh [out]` | checks the data, renders all 3, checks 1080x1920 + under 60 s, writes `contact-sheet.png` |
| `check_clips.py` | the check (data + ffprobe) and contact sheet |
| `test_clips.py` | unit tests (hostile sums, missing Telugu, wrong size, too long) |

CI: `.github/workflows/manim-clips.yml` renders on every change here (or Actions > "Explainer clips (Manim)" > Run) and uploads the MP4s + contact sheet as a run artifact. Nothing is posted.

To add a clip: add an entry to `clips.json` (kind `steps` or `graph`), a 3-line scene class in `scenes.py`, and its id to `render.sh`.

Before public use: a native Telugu read of the captions (machine-drafted by K082, corrected by Claude).
