# 📚 Exam Kit engine (b3)

One engine builds a kit for **any exam** from one data file. Each kit has 4 files in `dist/<exam-id>/`:

| File | What the student gets |
|---|---|
| `<id>-tracker.xlsx` | Study tracker: every syllabus topic with a status dropdown, progress % per subject, revision dates (1, 3, 7, 21 days), dates, free material and video slots. Opens in Google Sheets. |
| `<id>-calendar.ics` | Calendar: official CONFIRMED dates (with 7-day and 1-day alerts), a daily study block with that day's topics and revisions, and a Sunday check. |
| `<id>-tracker.html` | Phone page: tick topics, see % done, countdown and revisions due. Progress stays on the phone. Kalpa design colours and fonts only. |
| `<id>-telegram.json` | Reminder messages (one a day, English, plus Telugu for TGPSC kits) for the BotBhai Telegram flow. The file sends nothing. |

Kits today: TGPSC Group 2 (88 topics, Telugu), TGPSC Group 3 (70, Telugu), SSC CGL (76), RRB NTPC (61), GATE 2027 CS (65; taken from `../gate-2027`, which still works the same).

## Build and test (2 minutes)
```
python3 03-kits/engine/kit_engine.py --start 2026-11-10     # check + build every exam into dist/
python3 03-kits/engine/kit_engine.py --check                # only check the data files
python3 -m pytest 03-kits/engine/tests -q                   # all tests (LibreOffice re-calculates the sheet)
```

## Add a new exam (about 30 minutes)
1. Copy the closest file in `exams/` (a state exam: `tgpsc-group2.yaml`; a central exam: `ssc-cgl.yaml`) and name it `<new-id>.yaml`, for example `ibps-po.yaml`. Set `id:` to the same name.
2. Fill the top part: `short`, `name`, `body`, `category` (state-govt, central-govt, bank, private or entrance), `official_site` (an https link), `languages` (`[en]`, or `[en, te]` for a Telugu kit) and `checked_on` (today).
3. **Dates**, one line each under `key_dates`. The status rule is strict:
   - `CONFIRMED`: the date is on the official site. Put the date (`2027-02-06`) and the official https link in `source`.
   - `EXPECTED`: you have a reason to expect it but it is not official. Use `date: null` and say why in `note`.
   - `NOT_ANNOUNCED`: no date yet. Use `date: null`.
   Never type a date you have not seen on the official site. The check fails if you do.
4. **Syllabus** under `subjects`: each subject has a `name`, a `paper`, and 60–100 topic rows in total, written as `- {en: "Topic name"}`. Telugu kits add `te:` to every topic, plus `name_te` and `event_te`.
5. **Videos:** give each subject at least one slot: `- {query: "IBPS PO quant English", status: TO_CURATE, url: null}`. Only after a person has watched a video do you set `status: CURATED` and paste its real `https://www.youtube.com/watch?v=...` link. Never guess a link.
6. **Material:** free and official links only, `status: TO_VERIFY` until someone opens the link and sets `VERIFIED`. Never upload coaching PDFs (copyright).
7. Run the build and the tests above. If the check prints `BAD`, each line says what to fix.

## Rules built into the engine
- Only CONFIRMED dates reach the calendar, the alerts and the countdown.
- Progress is saved with `localStorage` inside try/catch. Private browsing shows a warning and the page still works.
- The sheet uses only formulas that also work in Google Sheets, and the GATE kit's colours.
- Telegram: at most one message a day per language, no "only today" wording. Messages go only to people who joined or opted in.
- Nothing here goes online until Akhil says "go" (CLAUDE.md rule 9).
