# Chrome Web Store listing · Tab Lifeboat (E10)

Images in this folder come from the real built extension (`npm run test:store` in `04-extensions/src`):
- Screenshots 1280×800: `screenshot-1-save`, `-2-proof`, `-3-import`, `-4-private` (light and dark; upload the light set, or mix).
- Small promo tile 440×280: `promo-small-440x280.png`. Marquee 1400×560: `promo-marquee-1400x560.png`.

## Name

Tab Lifeboat

## Short description

Never lose your tabs. Save every tab and group in one click, with automatic snapshots kept on your computer.

## Description

Never lose your tabs again. A crash, an update or a cleanup can wipe a whole day of work. Tab Lifeboat keeps a copy on your computer, all the time.

• One click saves every window, pinned tab and tab group. Nothing gets closed.
• Restore brings back group names, colours and collapsed state.
• Automatic snapshots every few minutes, so even tabs you forgot to save are kept.
• Move in from OneTab or Session Buddy: paste the text or open the file, and see a preview before anything is added.
• One backup file holds every session. Restoring it twice never makes doubles.
• Big sessions reopen gently: a few tabs load at a time, and the rest wait asleep until you click them, so Chrome doesn't freeze.
• A reminder when your last backup file is over a week old.

Privacy: your tabs stay on your computer. No account, no servers, no analytics, no ads. Policy: https://akhilkanigicharla.github.io/kalpa-labs/privacy.html

Free, with no daily limit: saving, restoring, imports, the backup file and the last 3 snapshots. Nothing is for sale yet; if a paid plan ever opens, its price will be shown first. Terms: https://akhilkanigicharla.github.io/kalpa-labs/terms.html

Moving from another tab saver? Step-by-step guides: https://akhilkanigicharla.github.io/kalpa-labs/switch-onetab.html and https://akhilkanigicharla.github.io/kalpa-labs/switch-session-buddy.html

## Headline options (for the promo tile and posts)

1. Never lose your tabs.
2. Your tabs, saved every few minutes, on your own computer.
3. One click saves every tab and group. Nothing leaves your PC.

## FAQ (for the site and replies)

- **Does it send my tabs anywhere?** No. Everything is stored in your browser on your computer.
- **Will saving close my tabs?** No. Saving only copies them.
- **Can I bring my OneTab or Session Buddy tabs?** Yes. Export there, then paste or open the file in Options. You see the count first.
- **What if my computer dies?** Download the backup file now and then, and keep it in Drive or email it to yourself.

## Screenshot captions

1. Save every tab and group in one click.
2. Automatic snapshots: proof your tabs are kept.
3. Move in from OneTab or Session Buddy with a preview.
4. Your tabs stay on your computer. No account, no tracking.

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
| Privacy policy URL | `https://akhilkanigicharla.github.io/kalpa-labs/privacy.html` |

When Google Drive backup ships (A234, needs the OAuth client id), add the **identity** permission justification: "optional; asked only when a Pro user turns on Google Drive backup, to get Google's permission for the drive.appdata scope (Tab Lifeboat's hidden app folder in the user's own Drive)". When Pro opens (E8 licence, E13 Drive), add **Authentication information** (licence key → the payment company Akhil chooses, C54) and update both this form and the policy in the same release.
