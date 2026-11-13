# UX check: Kalpa site (kalpalabs.dpdns.org) · 9 Nov 2026

Against `00-hq/design/UX-PATTERNS.md`. Tests: `test_tap_sweep.py`, `test_chat_button.py`, `test_form_ux.py`, `test_seo.py` (all PASS, 390 px light + dark).

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | ✅ Chat shows your message at once, then a typing bubble; a failed reply shows the offline answer instead of nothing. |
| 2 | Skeleton loaders | ✅ Chat typing bubble while waiting; page is static HTML (no data loads that need a skeleton). |
| 3 | Command palette | ➖ Phone-first marketing page with 6 sections; nothing to jump between. |
| 4 | Persistent navigation | ✅ Top nav on desktop, fixed bottom bar on phones (lifted above the Netlify badge). |
| 5 | Loading and empty states | ✅ Chat opens with a greeting + 3 starter questions (never an empty box); countdowns show "…" until computed. |
| 6 | Autosave | ✅ Pilot form draft (name, phone, interest) saved in this browser as you type, restored after reload, deleted after sending. |
| 7 | Debouncing | ✅ Draft save waits 250 ms after typing stops; chat sends only on Send. |
| 8 | Throttling | ✅ Chat and form buttons disable while sending; form button says "Sending…". |
| 9 | Smart form validation | ✅ Inline messages under each field on blur, in English or Telugu; Indian mobile check (accepts +91, 91…, 0…, spaces); focus jumps to the first problem. |
| 10 | Bulk actions | ➖ No lists. |
| 11 | Reusable data table | ➖ No tables. |
| 12 | Advanced filtering | ➖ No data to filter. |
| 13 | Keyboard shortcuts | ➖ Marketing page; Enter sends chat and form already. |
| 14 | Tier indicators | ➖ Nothing is on sale yet (no paid tier). Revisit when plans go on sale. |
| 15 | Onboarding capture | ✅ Pilot form asks only interest, name, WhatsApp number + plain-words DPDP consent. |
| 16 | Referral / affiliate | ➖ No live paid product yet. Revisit at launch. |
| 17 | Custom 404 | ✅ Branded noindex 404 with a Telugu line and buttons home / chat (live since 9 Nov). |
| 18 | Mobile layout | ✅ Tap sweep: nothing covered or off-screen, taps ≥ 44 px, light + dark. |
| 19 | Destructive action protection | ➖ Nothing on the page deletes or cancels. |
| 20 | Graceful error recovery | ✅ Chat: 30 s timeout → offline answer, status dot turns amber. Form: offline detected before sending, failure says "your details are safe" with a Try again button, nothing lost. |
