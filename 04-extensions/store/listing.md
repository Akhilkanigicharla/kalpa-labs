# Chrome Web Store listing · Tab Lifeboat (E10)

Images in this folder come from the real built extension (`npm run test:store` in `04-extensions/src`):
- Screenshots 1280×800: `screenshot-1-save`, `-2-proof`, `-3-import`, `-4-private` (light and dark; upload the light set, or mix).
- Small promo tile 440×280: `promo-small-440x280.png`. Marquee 1400×560: `promo-marquee-1400x560.png`.

## Name

Tab Lifeboat

## Short description

Save all tabs and tab groups in one click. Automatic snapshots on your computer, so a crash or update never wipes them.

## Description

Lost your tabs to a crash, an update or a "helpful" cleanup? Tab Lifeboat keeps them safe.

• Save every window, pinned tab and tab group in one click. Nothing gets closed.
• Restore brings back tab group names, colours and collapsed state.
• Automatic snapshots every few minutes, kept on your computer.
• Move in from OneTab or Session Buddy, with a preview before anything is added.
• Download one backup file with every session. Restoring it twice never makes doubles.

Privacy: your tabs stay on your computer. No account, no servers, no analytics, no ads. Policy: https://<pages-url>/privacy.html

Free for ever: saving, restoring, imports, the backup file and the last 3 snapshots.
Pro (opens soon) is a one-time licence key, not a subscription: 90-day snapshot history and a daily backup to your own Google Drive. Founding lifetime $19 / ₹899 (first 50), yearly $12 / ₹499, lifetime $29 / ₹1,199. Sold by Dodo Payments as merchant of record; 14-day refunds: https://<pages-url>/terms.html

## Category · language

Workflow & Planning (Productivity) · English

## Single purpose

Save and restore the user's browser tabs, windows and tab groups, including automatic snapshots, so they are not lost.

## Permission justifications

- **tabs**: read the titles and URLs of open tabs to save them, and reopen them on restore.
- **tabGroups**: save and restore tab group names, colours and collapsed state.
- **alarms**: take an automatic snapshot every few minutes.
- **storage**: keep settings and snapshot times.
- **unlimitedStorage**: keep large sessions (thousands of tabs) in IndexedDB without hitting the default quota.
- **downloads** (optional, requested only when a Pro user turns on the daily backup file): save one backup file a day to Downloads/Tab Lifeboat on the user's own computer.
- Remote code: none. All code ships in the package.

## Privacy practices form (Developer Dashboard → Privacy)

| Question | Answer |
|---|---|
| Data types | **Web history** (titles and URLs of the user's tabs). Nothing else in v0.1. |
| Is it sent off the device? | No. Stored in the browser (IndexedDB) only, for the single purpose above. |
| Certify: not sold to third parties | ✅ |
| Certify: not used or transferred for purposes unrelated to the single purpose | ✅ |
| Certify: not used or transferred to determine creditworthiness or for lending | ✅ |
| Privacy policy URL | `https://<pages-url>/privacy.html` |

When Pro opens (E8 licence, E13 Drive), add **Authentication information** (licence key → Dodo Payments) and update both this form and the policy in the same release.
