# Kit QA checklist (25 items) · GATE 2027 CS Tracker v1 (A19) and Tax + SIP Planner (A20)

✅ = checked automatically on every push (`03-kits/gate-2027/test_kit.py`, `03-kits/tax-sip/test_kit.py`, CI job "kits"). ☐ = Akhil checks once before selling (about 20 min in total, part of C24).

## Content and facts
1. ✅ Exam dates are the official ones: 6, 7, 13, 14, 20, 21 Feb 2027 (IIT Madras). The date cell accepts only these days.
2. ✅ The countdown is right on a known day: 113 days from 16 Oct 2026 to 6 Feb 2027.
3. ☐ Syllabus topics match the **official** GATE 2027 CS syllabus PDF on gate2027.iitm.ac.in. The 2027 changes are marked "(2027)"; the source is a summary site, so check it.
4. ✅ Subject weights equal the cited GATE 2023–25 marks (Maths 11.7, COA 9.7, GA 15) and are labelled as a guide, not a prediction.
5. ✅ Tax kit: official fixtures (₹12.75L / ₹13L / ₹25L) PASS on the in-sheet Self-check tab.
6. ✅ Tax kit: 157 random and edge cases equal the calculator site's tested engine exactly.
7. ✅ Tax kit: HRA, SIP and EMI tabs equal the site's engine.
8. ✅ Tax kit warns above ₹50 lakh (surcharge not included) instead of giving a wrong number.
9. ✅ No fund names, return promises or "guaranteed" wording (SEBI); both Start tabs say "not advice".

## Works as a sheet
10. ✅ Only functions that exist in Google Sheets (static scan of every formula).
11. ✅ No error cells (#VALUE!, #NAME?, #REF!, Err:) after a full recalculation of all files.
12. ✅ Spaced revision: +1 / +3 / +7 / +21 days; due items show "Revise"; off the list after 4 revisions.
13. ✅ Streak counts consecutive days, including "today not logged yet".
14. ✅ This-week hours and the target use Monday–Sunday.
15. ✅ Mock analyser: best, average and last-3 average; the biggest leak; "Re-learn" vs "Slow down".
16. ✅ Tiers contain only their own features: Lite (countdown + checklist), Kit (+ log, revision, week), Pro (+ weights, mocks, Telugu/Hindi).
17. ☐ Upload each .xlsx to Google Drive → "Save as Google Sheets" → open on a phone: tabs, drop-downs and yellow input cells work.
18. ☐ In Google Sheets, the Self-check tab of the tax kit says PASS on every row (proves the import kept the formulas).
19. ☐ The `/copy` link makes a fresh copy for a test Gmail account, and the copy has no access to your Drive.

## Words and design
20. ✅ Telugu and Hindi instructions are present in Pro; Telugu in the tax kit Start tab.
21. ☐ A Telugu speaker reads the Telugu lines (with C23/C17).
22. ✅ Kalamkari colours: indigo headers, turmeric input cells; inputs vs calculated cells are visually distinct.

## Selling rules
23. ✅ The landing page shows the full price once, with no fake urgency or countdown sale (`05-deals/site/src/lib/kits.test.ts`).
24. ☐ Razorpay Payment Page: the price matches the landing page, the success page shows the copy link, and the refund policy is linked.
25. ✅ "Not an official GATE product" and the source of every date are written in the kit and on the page.
