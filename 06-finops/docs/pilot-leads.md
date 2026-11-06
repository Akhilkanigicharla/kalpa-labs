# Pilot leads: AI Cost X-ray + FinOps pilots (A157, replaces C43)

Built 6 Nov 2026 with the first-customer-finder method. These are **potential customers based on public signals**, not people who said yes. Nobody has been contacted.

**Why two tiers:** Reddit and LinkedIn block Claude's tools, so Tier A posts were seen only as search snippets. They open fine on Akhil's phone. Tier B companies match the profile but show no public cost complaint, so treat them as guesses.

**Rules for any message:** opt-in only, reply in the public thread or use the company's own contact page, one message, no follow-up spam (TRAI/DPDP). Never say "certified". The offer is a **free** pilot (A150): 3 slots.

## Tier A: they asked for help in public (open on phone, check, then reply)

| ID | Signal (paraphrased from the snippet) | Source | Score | What to check first |
|---|---|---|---|---|
| A1 | u/anirudh8398 (~Jul 2026, 211 upvotes, 234 comments): parses ~20,000 job descriptions/day with Claude Opus, ₹2.20/job ≈ ₹44K/day; Sonnet and DeepSeek lose quality on messy JDs; asks about routing and fine-tuning a small model. **Checked by Akhil on phone 6 Nov.** | [r/indianstartups post](https://www.reddit.com/r/indianstartups/comments/1ulr9yj/opus_costing_us_44kday_16kmo_how_can_we_reduce/) | 4.2 | 4 months old and already has strong free advice (cascade routing, dedupe, distillation from u/dark-mage-x), so a generic reply adds nothing; offer a measured test instead. **Caution:** their JDs are "pulled from LinkedIn" (likely scraping, against LinkedIn's terms). Akhil decides if Kalpa works with them; we never touch the scraping part. |
| A2 | u/GetALife_00 (~Oct 2026, "Roast My Idea"): plans an "AI spend doctor" tool for small startups. **Not a buyer: a would-be competitor.** Checked by Akhil 6 Nov. | [r/StartUpIndia post](https://www.reddit.com/r/StartUpIndia/comments/1wpr1ce/ai_startups_how_are_you_keeping_track_of_aiapi/) | 1.5 | Useful as market proof: founders feel this pain. Leads would be commenters who describe their own bill. |
| A3 | SaaS founder (UnisonWave) posts that LLM costs are outpacing revenue. | [LinkedIn post, Rajender Polu](https://www.linkedin.com/posts/rajender-polu_ai-saas-fintech-activity-7428643136190689281-Iuq1) | 3.5 | Is it about their own company or general advice? |
| A4 | MD & CEO posts that AI inference costs are eating gross margin. | [LinkedIn post, Paras Vishwakarma](https://www.linkedin.com/posts/paras-vishwakarma_ai-uniteconomics-saas-activity-7472008213845172224-4AKI) | 3.0 | Thought-leadership post or real pain? Indian company? |
| A5 | A tech lead says their company burns API money on AI tools daily. | [r/developersIndia thread](https://www.reddit.com/r/developersIndia/comments/1sl7p30/how_is_your_company_dealing_with_ai_costs_are/) | 2.8 | Employee, not a buyer. Only useful if a founder replies in the thread. |

**Reply for A1 (public comment in the thread, posted by Akhil):**
> Late to this, but if it's still a problem: we're running 3 free cost pilots for Indian startups. For a case like yours we'd take ~500 of your JDs (already labelled by Opus), run the cheap-model → schema check → Opus-fallback cascade suggested above, and send you field-by-field accuracy and cost per 1,000 JDs. Free, no sales call; you share only sample JDs, no API keys. Reply here if useful.

## Tier B: good fit, no public complaint found (guesses)

Small Indian YC-backed startups whose product runs on LLM or voice-AI calls, so API spend is likely a large cost. Source for all: YC directory (read 6 Nov 2026). Contact = the company's own website contact page; check it before writing.

| ID | Company | What they build | Team | Website |
|---|---|---|---|---|
| B1 | Bolna AI (Fall 2025) | Voice AI for India | 21 | https://bolna.ai |
| B2 | Floworks (W23) | AI sales employees (AI SDR) | 20 | https://floworks.ai |
| B3 | Lab0 (Spring 2026) | AI engineers to set up B2B SaaS | 7 | https://lab0.ai |
| B4 | ShortLoop (W23) | Phone AI for car dealerships | 8 | https://shortloop.dev |
| B5 | SuperKalam (W23) | AI mentor for exam prep | 20 | https://superkalam.com |
| B6 | Retape (W23) | AI for debt settlement | 3 | https://www.retape.ai |
| B7 | CORE (S23) | Personal AI assistant | 3 | https://getcore.me |
| B8 | RocketSDR (W21) | AI sales outreach | 30 | https://rocketsdr.ai |
| B9 | BusinessOnBot (W21) | WhatsApp selling with AI | 25 | https://www.businessonbot.com |
| B10 | Clueso (W23) | AI product videos and docs | 25 | https://clueso.io |

Caution: funded teams may already have cost tooling. Pitch as "design partner, free", ask for feedback, not money.

## Next
1. Akhil opens A1 and A2 on his phone (5 min), tells Claude what they say; Claude adjusts the reply.
2. Claude keeps searching weekly for new Tier A posts (accessible sources: dev.to, Hacker News, GitHub issues) and adds them here.
3. A157 is ticked when Akhil picks 3 leads to approach.
