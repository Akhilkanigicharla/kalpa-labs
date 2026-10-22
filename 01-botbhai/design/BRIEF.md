# BotBhai owner screens: design brief (A10)

**Who:** the owner of a 2–6 chair salon in Hyderabad. They use a phone only, between clients, often with wet hands, and mix Telugu and English. They open BotBhai about 3 times a day: in the morning ("who's coming today?"), between clients ("does anyone need me?") and at night ("how was the day?").

**Screens (all built, phone first, on the Kalpavruksha tokens in `00-hq/design/`):**

| Screen | File | Job |
|---|---|---|
| Owner dashboard | `botbhai/web/dashboard.html` | Today's bookings, chats waiting, leads, and a 30-day report with Excel export |
| Shared inbox | `botbhai/web/inbox.html` (A04) | Take over a chat, reply as the salon, hand back to the bot |
| Billing (Kalpa only) | `botbhai/web/billing.html` (A05) | Akhil invoices salons |

Try them with `?demo=1` (sample data, nothing sent). With a real key, they read the live API (`functions/leads`, `functions/inbox`).

## Research (16 Oct 2026)
- **[satnaing/shadcn-admin](https://github.com/satnaing/shadcn-admin)** (MIT, 15.8k★) and **shadcn/ui `dashboard-01`**: section cards (KPIs) on top, then one chart and one list/table. We use the same order and copy the *pattern*, not the React code. BotBhai pages are single files with no build step, per the toolkit table in `DESIGN-SYSTEM.md`.
- **Mobile dashboard guidance** ([querio summary](https://querio.ai/articles/how-to-design-dashboards-for-mobile-users) of UXCam, ArcGIS and Toptal; NN/g-style progressive disclosure):
  - stack vertically
  - 3–5 bottom tabs
  - primary actions in the thumb zone
  - 44–48 px targets
  - details only on tap
  - big bold numbers for the few metrics that matter
- **Salon apps (Zylu, DINGG):** appointments first, then clients, reminders and reports. Staff, POS and inventory are out of scope for BotBhai (`docs/requirements/salon.md`).

## Rules for these screens
1. **Three numbers, no more, at the top of Today:** bookings today, confirmed by the customer, and chats that need you. Each one is a tap target that opens the detail.
2. **One timeline for today**, in time order, with a status chip per booking (confirmed · customer confirmed · done · no-show · cancelled). Past and future days are one tap away, never on the first screen.
3. **Bottom tab bar under 760 px** (Today · Leads · Inbox · Report). Inbox is a link to `inbox.html`, with a red count when chats wait.
4. **Every state is designed:** loading (skeleton), empty ("No bookings today yet: share your WhatsApp link"), error (retry), offline (last data kept), wrong key (sign in again).
5. **Words from the owner's side:** "Needs you", "Came", "Didn't come", never "status=no_show". Phone numbers are shown as `+91 98480 12345` and are tap-to-call.
6. **Privacy:** the key lives in the page's local storage on that phone, never in the URL (a `#key=` setup link is read once and wiped). No analytics or third-party scripts; Google Fonts is the only external request.
7. **Both themes, 390 px, no sideways scroll.** `tools/screens.py` checks every screen; `tools/test_dashboard_ui.py` clicks through the demo.

## Next (not in this item)
Telugu labels toggle (needs the C17-style read-through), tap to mark done / no-show from the timeline (today that's the owner's 9 PM WhatsApp list, A03), and a phone PWA with an unread badge (P1-M2-05).
