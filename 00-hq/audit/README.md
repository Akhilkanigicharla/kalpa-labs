# Fact-check & audit desk (set up 18 Oct 2026)

Why: on 18 Oct Claude told Akhil that Vercel AI Gateway's free $5 would run DeepSeek/Kimi/GLM. Not checked; false (free tier blocks them, HTTP 403). Akhil asked for a separate team that checks every claim against ground reality.

## Rules (every session, every agent)
1. **No advice to Akhil without proof.** Anything he must sign up for, pay for, install or decide on needs: the provider's own page fetched today **and** a second independent source, **or** a live test that ran (a real API call, a test, a build). Write the source links and date.
2. **Verdicts:** `VERIFIED` (two sources or a live test, date given) · `WRONG` (contradicted; give the correct fact) · `UNVERIFIED` (could not check; must not be used for advice) · `STALE` (older than 30 days for prices/limits/free tiers).
3. **Free means free forever** (recurring, no card). One-time credits are called "trial credit ₹X, one time", never "free".
4. Income numbers from videos/blogs are always "creator's claim, unchecked".
5. Never fix by guessing: a WRONG fact becomes a roadmap item or a CEO note with the corrected source.

## Files
- `facts.md`: the living register of checked facts (provider limits, prices, licences). Update, don't duplicate.
- `YYYY-MM-DD.md`: each audit run's report (what was checked, verdicts, fixes queued).
