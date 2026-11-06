# Exam kits engine (A159)

Akhil's pick (6 Nov 2026, C62): **Andhra + Telangana state exams, teachers, banks and central government**. One engine builds every kit from a data file, so a new exam is just a new `exams/<id>.json`.

| Family | Kits built (20) | Still to add (A161) |
|---|---|---|
| State PSC · Telangana | `tgpsc-group-1`, `tgpsc-group-2`, `tgpsc-group-3`, `tgpsc-group-4` | — |
| State PSC · Andhra Pradesh | `appsc-group-1`, `appsc-group-2` | — |
| Police | `tslprb-constable` (Telangana) | AP police constable |
| Teachers | `ctet`, `tg-tet`, `ap-tet` | TS DSC, AP DSC (subject-wise) |
| Banks | `ibps-po`, `sbi-po`, `ibps-clerk` | IBPS RRB PO / Clerk |
| Central Government | `ssc-cgl`, `ssc-chsl`, `ssc-mts`, `ssc-gd`, `rrb-ntpc`, `rrb-group-d`, `upsc-cse` | — |

**What each kit has (Akhil's list):** tracker (Syllabus sheet), reminders (spaced revisions; Telegram/WhatsApp alerts come in A163), status/progress (Start sheet), exam dates and alerts (Dates sheet), best material and YouTube videos (the link column per topic, filled in A160).

**Run:** `python3 03-kits/exam-kits/build.py` → `03-kits/products/` (git-ignored, never committed). **Test:** `python3 03-kits/exam-kits/test_build.py` (LibreOffice recalculation, pinned date).

**Rules:** syllabi are checked against the official site plus 2 more sources (listed in each file and on the kit's Sources sheet). Dates are typed from the official notice, never guessed. We link to videos and official PDFs; we never re-host coaching material. The kits are "not affiliated with the exam body". Telugu labels reviewed and fixed (C64, 6 Nov).
