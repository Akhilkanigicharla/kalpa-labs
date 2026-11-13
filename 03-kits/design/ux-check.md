# UX check: Kalpa exam kit shop (`03-kits/shop/dist`) · 14 Nov 2026 (A212)

Against `00-hq/design/UX-PATTERNS.md`. Static pages, no JavaScript, no forms. Tests: `python3 -m pytest 03-kits/shop/test_shop.py -q` (content, prices, SEO, 390 px tap sweep light + dark on all 6 pages): PASS.

| # | Pattern | Status |
|---|---|---|
| 1 | Optimistic UI | Not relevant: no actions that save anything on these pages. |
| 2 | Skeleton loaders | Not relevant: static HTML, nothing loads after the page. |
| 3 | Command palette | Not relevant: phone-first sales pages. |
| 4 | Persistent navigation | Done: every kit page starts with "All Kalpa exam kits" back to home. |
| 5 | Loading and empty states | Done: an empty payment or Telegram link shows "opens soon" text, never a dead button (test). |
| 6 | Autosave | Not relevant: no forms. |
| 7 | Debouncing | Not relevant: no search or typing. |
| 8 | Throttling | Not relevant: buttons are plain links to Razorpay Payment Pages, which handle double taps. |
| 9 | Smart form validation | Not relevant: no forms (payment fields live on Razorpay). |
| 10 | Bulk actions | Not relevant. |
| 11 | Reusable data table | Done: one dates table style, same as the phone tracker. |
| 12 | Advanced filtering | Not relevant: 5 kits on one screen. |
| 13 | Keyboard shortcuts | Not relevant: phone-first. |
| 14 | Tier-based UI indicators | Done: free mini-kit, ₹199 kit, ₹499 bundle, ₹99 × 30 institute, each says what it includes. |
| 15 | Onboarding data capture | Done: the free mini-kit needs only a Telegram follow, no sign-up form. |
| 16 | Referral and affiliate pages | Not relevant yet: mock-test links are not affiliate links (page says Kalpa is not linked to them). Add #ad if that ever changes (ASCI). |
| 17 | Custom 404 page | Done: `404.html`, noindex, link home, 44 px tap. |
| 18 | Mobile-optimised layout | Done: 390 px light + dark, no sideways scroll, nothing covered, taps ≥ 44 px (test). |
| 19 | Destructive action protection | Not relevant: nothing to delete. |
| 20 | Graceful error recovery | Done: works offline once loaded, no scripts to fail; refund line covers a kit that does not open. |
