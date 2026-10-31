# ai-job-search skills (vendored, MIT)

Source: https://github.com/MadsLorentzen/ai-job-search, commit in `UPSTREAM_COMMIT`, copied unmodified on 31 Oct 2026. Licence: `LICENSE` (MIT, (c) 2026 Mads Lorentzen).

Copied: `job-application-assistant/` (job-fit scoring, CV and cover-letter templates, interview prep) and `upskill/` (skill-gap plan).
Left out: `job-scraper` and the `.agents/skills/*-search` portal skills. They scrape LinkedIn and Danish job boards, and LinkedIn bans scraping (CLAUDE.md rule 4).

## How Kalpa uses it
- **b3 Kits, Job-Ready Kit (A140):** the evaluation, CV, cover-letter and interview files are the method behind a Telugu + English kit for graduates (fit check, CV, cover letter, 20 interview questions). The person pastes the job text in themselves; we never fetch job sites.
- **HQ hiring (later):** writing job posts and scoring applicants for Kalpa's first hire.
- It is reading material for agents and Claude, not auto-loaded. Kalpa rules win: DPDP for any CV data, no personal data kept without consent.
