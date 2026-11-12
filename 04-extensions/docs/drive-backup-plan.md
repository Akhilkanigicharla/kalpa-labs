# Tab Lifeboat Pro: Google Drive backup (A234, 12 Nov 2026)

**Why (data, checked 12 Nov 2026):** cross-device cloud backup/sync is the one feature people pay for in this category (Workona Pro $7/mo, OneTab sync $7/yr, Toby $6/member). Local saving is free everywhere. Rivals' own users lose data after updates and "repairs"; a copy outside Chrome fixes that.

**What it does**
- Pro users switch on "Back up to Google Drive". Tab Lifeboat copies every saved session to a hidden app folder in *their own* Drive, gzipped.
- Runs every hour, but only uploads when something changed (SHA-256 of the backup). "Back up now" button.
- On any computer: connect the same Google account, see every backup (date, device, sessions, tabs), preview, restore. Restoring never makes doubles.
- Keeps every backup from the last 48 hours, then one a day for 30 days. Older ones are deleted.

**Design rules**
- Scope `drive.appdata` only (Google: "Recommended, Non-sensitive"). Only Tab Lifeboat can see that folder; we never receive the data. No server of ours.
- `identity` is an optional permission, asked only when the user switches Drive on. No host permissions (Google APIs allow CORS).
- `chrome.identity.getAuthToken` (Chrome). Other Chromium browsers get a clear message.
- Every call: 20 s timeout; 429/5xx retried with backoff (1 s, 2 s, 4 s, honours Retry-After); 401 → drop cached token, retry once; Drive full → plain message.
- OAuth client id comes from the build setting `WXT_GOOGLE_CLIENT_ID` (public id, not a secret). Without it, the card says Drive backup isn't set up yet.
- Privacy policy gets the Chrome Web Store Limited Use statement; store privacy form adds "Authentication information" only for the Google token handled by Chrome.

**Akhil (laptop, later):** create the Chrome-extension OAuth client in Google Cloud (free), put its id in the GitHub secret `WXT_GOOGLE_CLIENT_ID`, then a real-account test before release. Payment company stays C54.

**Checks:** unit tests against an in-memory fake Drive (upload, list, paging, download, retention, 401/429/503/quota/offline/timeout), real-Chrome e2e for the screen and the Pro gate, screens light + dark, eng_check 0 FAIL.
