# Plugin Isles (b4) as a real business: 5 paid browser extensions

Akhil, 24 Oct 2026: "find the best problems on the entire internet, build extensions people pay genuine money for, test, publish, promote, get feedback, keep updating… 24×7… this stream to be top on my leadership dashboard. Use free tools, build the best products, not vibe-coded stuff."

**Decisions (Akhil, 24 Oct):**
- **Stores:** Chrome + Edge + Firefox. Akhil pays the one-time Chrome developer fee himself (C52); Edge and Firefox are free.
- **Extension #1:** Tab Lifeboat, already built (25 unit tests green). The swarm finds #2–#5.
- **Promotion:** Kalpa Labs brand accounts that Akhil creates himself with the business Gmail (C53). Agents draft every post; Akhil approves and posts.

## The rules this business keeps
1. **People pay for a solved problem, not for a clever demo.** No extension is built without evidence that people asked for it or paid for something similar: real reviews, requests or rival revenue, linked in its scorecard.
2. **Honest selling.** We use real persuasion, not tricks:
   - Allowed: show the pain, a free tier that is truly useful, social proof only from real users, a clear price, a 14-day refund.
   - Never: fake reviews, fake scarcity timers, hidden auto-renewal, or nagging popups.
   This keeps us within ASCI and the store policies, and it is how we keep paying users for years.
3. **Privacy first.** Data stays on the device by default. AI runs inside the browser (Chrome's built-in AI, Transformers.js / WebLLM with Hugging Face models), which costs ₹0 per user and gives a privacy promise competitors can't make.
4. **Store-safe.** Manifest V3, no remote code, the minimum permissions, and a privacy form that matches the code. Every release passes a policy check before upload.
5. **Free tools only** for building, testing and promotion. Money is spent only by Akhil on the store fee and, later, a payment provider's normal per-sale fee.
6. **Nothing public without Akhil's "go"** (CLAUDE.md rule 9), per extension and per release.

## The engine: 41 jobs, run by the 22 n8n agents + Claude + GitHub Actions
| Stage | Jobs (count) | Who runs it | Runs |
|---|---|---|---|
| **1. Scout** | store-review complaint miner, Reddit/HN "I'd pay for" finder, indie revenue tracker, India-problem finder, in-browser AI scout, GitHub MIT/Apache scout, trend watcher (7) | Scout, Forge, Pulse on n8n (KL Tasks), free models + web search | every 3 h, 24×7 |
| **2. Score** | evidence checker, demand scorer, competition mapper, payment-willingness scorer, policy-risk checker, build-cost estimator (6) | Vigil + Guard on n8n; Claude checks the top 3 | weekly |
| **3. Spec** | user-story writer, free-vs-Pro splitter, pricing designer, privacy planner (4) | Kavi, Ledger on n8n; Claude finalises | per idea |
| **4. Build** | coder, test writer, accessibility + 390 px checker, store-policy linter (4) | Claude (code, tests), GitHub Actions (CI) | per release |
| **5. Ship** | store listing writer (SEO), screenshot maker, privacy-form filler, release-notes writer (4) | Kavi, Lens, Pixel on n8n + Playwright screenshots | per release |
| **6. Promote** | Reddit/HN/Product Hunt post drafter, YouTube short script + video, comparison-page writer, AlternativeTo/SaaSHub lister, X thread drafter, newsletter pitch drafter (6) | Adi, Reel, Kavi on n8n; Social Team video tools; **Akhil approves and posts** | daily drafts |
| **7. Sell** | landing-page optimiser, checkout + licence checker, refund handler drafts (3) | Forge, Ledger, Echo | always on |
| **8. Listen** | store-review reader, uninstall-survey reader, support-mail drafter, bug triager (4) | Echo, Probe on n8n | daily |
| **9. Improve** | weekly what-to-fix list, A/B result reader, kill/keep judge (3) | Dash, Kalpa (chief of staff); Claude builds the fixes | weekly |

Total: 41 jobs. Every draft passes Vigil (QA) and Guard (risk) before Akhil sees it.

## Scorecard for each idea (used in stage 2, out of 30)
| Factor | 1 | 5 |
|---|---|---|
| Demand evidence | 1 vague mention | many dated complaints + a rival with 100k+ users |
| Payment willingness | nobody pays for this | rivals charge and people pay |
| Competition gap | strong free rival with no complaints | rivals hated in reviews, or abandoned |
| Build effort (inverse) | months, servers needed | 1–2 weeks, runs fully in the browser |
| Policy risk (inverse) | needs broad permissions / touches WhatsApp, banking | narrow permissions, nothing risky |
| Kalpa fit | we can't support it | India angle, or reuses our code (AI, Telugu/Hindi, PDF) |

Kill rule: below 20 → drop. An extension already built is dropped if it has fewer than 3 paying users 60 days after launch with promotion running.

## Money targets (what the leadership dashboard tracks)
| | Month 1 | Month 3 | Month 6 |
|---|---|---|---|
| Extensions live | 1 (Tab Lifeboat) | 3 | 5 |
| Weekly active users | 100 | 1,500 | 6,000 |
| Paying users | 3 | 40 | 200 |
| Monthly revenue | ₹500 | ₹8,000 | ₹40,000 |

These are goals, not forecasts. The dashboard shows the real numbers from store stats and the payment provider. Nothing is invented.

## Where it lives
- `04-extensions/src/` holds Tab Lifeboat. Each new extension gets `04-extensions/<slug>/`, with the same WXT setup and the same test bar.
- Research is in `04-extensions/research/`. Scout results arrive in the KL Tasks table (stream b4) and are summarised in `research/scout-<date>.md`.
- Roadmap items are A105–A113 and C52–C54.
