# Reel reader: Facebook / Instagram videos, frame by frame

Akhil sends a video **file** (saved or screen-recorded on the phone). Claude turns it into frames, contact sheets, on-screen text and a speech transcript, then reads the sheets instead of the whole video. We never download from Instagram or Facebook (CLAUDE.md rule 4): the tool refuses links.

## Use
```bash
/home/claude/venv-reel/bin/python 00-hq/tools/reel/reel_frames.py reel.mp4 --out /tmp/reel
# --every 0.5  more frames   --max 120  frame cap   --no-audio  skip speech   --model medium  better Telugu (slower)
```
Out: `frames/`, `sheet_01.jpg…` (12 frames each, timestamped), `report.md` (timeline: on-screen text + what was said), `report.json`.

## How it works
1. ffprobe reads length, size, fps. ffmpeg finds scene cuts (threshold 0.25) and adds one frame per second; near-duplicates (< 0.4 s) are merged, capped evenly at `--max`.
2. Tesseract reads on-screen text in English, Telugu and Hindi; repeated text is shown once.
3. faster-whisper "small" (runs on CPU, free) writes what is said, with times and the detected language.

## Setup (once per cloud session, about 2 min)
`python3 -m venv /home/claude/venv-reel && /home/claude/venv-reel/bin/pip install -r 00-hq/tools/reel/requirements.txt`; Telugu/Hindi OCR data from `tesseract-ocr/tessdata_fast` into `/home/claude/tessdata` (sparse git clone). Licences: ffmpeg (LGPL, used as a tool), Tesseract + tessdata (Apache-2.0), faster-whisper + Whisper weights (MIT). Nothing here ships in a product.

## Test
`/home/claude/venv-reel/bin/python 00-hq/tools/reel/test_reel_frames.py` builds a 3-scene test video and checks frames, cuts, OCR, sheets, report and the link guard (14 checks).

Limits: Whisper "small" is good for English and Hindi, weaker for Telugu; use `--model medium` for Telugu-heavy reels. Very fast cuts under 0.4 s are merged.
