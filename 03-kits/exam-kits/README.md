# Exam kits engine (A159)

Akhil's pick (6 Nov 2026, C62): **Andhra + Telangana state exams, teachers, banks and central government**. One engine builds every kit from a data file, so a new exam is just a new `exams/<id>.json`.

| Family | First kit (built) | Next in this family (A161) |
|---|---|---|
| State PSC · Telangana | `tgpsc-group-2` (58 topics, Telugu labels) | TGPSC Group 1, 3, 4; TSLPRB police |
| State PSC · Andhra Pradesh | `appsc-group-2` (41 topics, Telugu labels) | APPSC Group 1; AP police |
| Teachers | `ctet` (Paper 1 + 2) | TS TET, AP TET, DSC |
| Banks | `ibps-po` (prelims + mains) | SBI PO, IBPS Clerk, RRB PO/Clerk |
| Central Government | `ssc-cgl` (Tier 1 + Tier 2) | SSC CHSL, MTS, GD; RRB NTPC / Group D; UPSC CSE |

**What each kit has (Akhil's list):** tracker (Syllabus sheet), reminders (spaced revisions; Telegram/WhatsApp alerts come in A163), status/progress (Start sheet), exam dates and alerts (Dates sheet), best material and YouTube videos (the link column per topic, filled in A160).

**Run:** `python3 03-kits/exam-kits/build.py` → `03-kits/products/` (git-ignored, never committed). **Test:** `python3 03-kits/exam-kits/test_build.py` (LibreOffice recalculation, pinned date).

**Rules:** syllabi are checked against the official site plus 2 more sources (listed in each file and on the kit's Sources sheet). Dates are typed from the official notice, never guessed. We link to videos and official PDFs; we never re-host coaching material. The kits are "not affiliated with the exam body". The Telugu labels need one read by a native speaker before sale (C64).
