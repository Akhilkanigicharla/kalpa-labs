# YouTube money swarm · 18 Oct 2026

**Question (Akhil):** what do YouTube creators say makes money with Claude/AI in 2026? Check it against GitHub, Hugging Face and voice tools, compare with Kalpa's 8 worlds (HQ + b1–b7), and propose swaps.

**Short answer:** no new idea beats the plan. Three YouTube ideas fit Akhil better than parts of the current plan, and all three plug into existing worlds: **(1) sell Claude Skill / template packs through b3**, **(2) a pre-sold Telugu "Claude Code with me" workshop**, **(3) ghostwriting for founders as the way in to b6**. Voice: **Sarvam beats ElevenLabs for Telugu at about ¼–⅓ of the price**. The real blocker is still the CEO queue (0 of ~29 done, ₹0 revenue), not a lack of ideas.

**How this was made:** 5 parallel research agents (superpowers:dispatching-parallel-agents), merged by the lead session. 12 new transcripts read with the Firecrawl YouTube reader, plus the 4 videos already in the n8n KL Knowledge table (rows 1–2). Repo data via repos.ecosyste.ms (GitHub API blocked here), model data via the Hugging Face Hub, prices from ElevenLabs' and Sarvam's own pages (fetched 18 Oct 2026, ₹88 = $1, add 18% GST).

> **Every income number in this file is the creator's own claim, not checked.** 11 of the 12 new videos sell a course, community, sponsor or affiliate link. Nothing here promises income to anyone.

## 1. Sources

| # | Video | Channel | Date | Pitch |
|---|---|---|---|---|
| A1 | [Beginner-friendly Claude AI side hustle](https://www.youtube.com/watch?v=quYKZushRPo) | The Koerner Office (guest Ryan Doser) | 2026-05-13 | sponsor + paid PDF |
| A2 | [$20k/month selling AI from India](https://www.youtube.com/watch?v=CkSsZtfLiBc) | Hamza Automates | 2025-11-17 | course |
| A3 | [5 most in-demand AI automations 2026](https://www.youtube.com/watch?v=tgjYMym_0-c) | Nate Herk | 2026-08-20 | sponsor + Skool |
| A4 | [Sell AI agents to local businesses 2026](https://www.youtube.com/watch?v=HTWrhbtETuI) | Mikey No Code | 2026-04-20 | affiliate + course |
| A5 | [Automated $1k/day side hustle with Claude](https://www.youtube.com/watch?v=wEEi2bCuZGQ) | Wholesale Ted | 2026-09-24 | sponsor + membership |
| A6 | [3 real ways to make money with Claude 2026](https://www.youtube.com/watch?v=Zvnt4S3aFJk) | Kimberly Mitchell | 2026-06-30 | sponsor; says figures are third-party |
| B1 | [How to sell your Claude Skills](https://www.youtube.com/watch?v=Geg9TyNoi3w) | Jake Dawson | 2026-08-06 | promotes Expertise.ai |
| B2 | [4 Claude digital products that pay rent](https://www.youtube.com/watch?v=ye5sr67Jo5U) | Molly Keyser | 2026-07-16 | membership + affiliate |
| B3 | [Faceless channel "made $39K" with Claude](https://www.youtube.com/watch?v=8Rf0xna31xg) | Sanji Nai-Chien | 2026-08-24 | likely sponsored |
| B4 | [Faceless channel YouTube won't demonetize](https://www.youtube.com/watch?v=d_csri5M9xw) | vidIQ | 2026-08-10 | promotes vidIQ |
| B5 | [AI voice agents: build & sell](https://www.youtube.com/watch?v=a3NHWkiHbiU) (Hindi) | Pritam Nagrale | 2025-03-02 | course |
| B6 | [Best Indian telephony for AI voice agents](https://www.youtube.com/watch?v=C-QdmmicOpY) | Shreyas Raj | 2026-06-17 | referral code |
| K1–K4 | jVOk8oc-a70, mQtwgEXBc_I, Johann Sathianathen, Ac Hampton | (n8n KL Knowledge rows 1–2) | 2026 | — |

What every creator agrees on: **one niche, one offer, one number; selling beats building (Johann: "20% build, 80% offer + distribution")**. Most common model: setup fee + monthly retainer (US prices quoted: $2–5k setup, $300–800/month; Indian prices are far lower).

## 2. Ranked ideas

Fit score /10 = skills 20% · fits 1 h/day 25% · ₹0–5,000 budget 15% · legal safety 20% · time to first rupee 20% (fit agent; rows marked * scored by the lead session with the same weights).

| Rank | Idea | Source videos | World | Fit /10 | First rupee | Free tools · repos · HF models | Risks / legal |
|---|---|---|---|---|---|---|---|
| 1 | **Claude Skill / prompt / n8n template packs** (sell your know-how as a skill bundle; B1: buyers can use a skill without seeing it) | A1, A6, B1, K1, K3 | b3 (upgrade) | **8.4** | 1–3 weeks (after UPI QR / Razorpay) | Claude skill-creator; [obra/superpowers](https://github.com/obra/superpowers) MIT (model), [wshobson/agents](https://github.com/wshobson/agents) MIT (marketplace layout), [anthropics/skills](https://github.com/anthropics/skills) example skills Apache (docx/pdf/pptx/xlsx skills **not** redistributable) | Easy to copy once shared; crowded. A1's "$3k+ in 30–45 days" (claimed) came from a seller who already had an agency, SEO traffic and an email list. Never resell vendored code as ours. |
| 2 | **Ghostwriting / LinkedIn content for founders** | K1, A1 (video→blog) | NEW, as the way in to b6 | **7.8** | 2–3 weeks | [inovector/mixpost](https://github.com/inovector/mixpost) MIT; Ghost MIT; Postiz/listmonk AGPL = run unmodified only | Cap at 2 clients (time). Google penalises mass AI posts; write with the founder's own facts. Disclose nothing false. |
| 3 | **Telugu "Claude Code with me" workshop, pre-sold, then sell the recording** | B2 (workshop → recording, pre-sell), K1 (AI educator) | NEW, sold through b3, marketed by b5 | **7.5** | 2–4 weeks | Google Meet (free), Canva, Sarvam Bulbul / Kokoro for narration (below) | Akhil is a beginner, so frame it "learn with me", never "expert"; no income promises in the pitch (ASCI). Refund if it doesn't run. |
| 4 | Resume + LinkedIn rewrite service * | A6 | NEW (HQ side gig) | 7.0* | 1–2 weeks | Claude, Docs | Service work, not passive; never invent experience. Indian prices ~₹500–2,500. |
| 5 | Thumbnail / design service | K1 | NEW | 6.9 | 2–3 weeks | FLUX.1-schnell (Apache, Colab GPU); FLUX.1-dev is non-commercial | Prices race to the bottom; overlaps the BotBhai Social Team add-on. |
| 6 | Invoice / document → draft bill automation (GST, Tally) * | A3 (creator's top first project) | b1 add-on | 6.8* | with b1's first client | Claude, [activepieces](https://github.com/activepieces/activepieces) MIT | Keep outputs as drafts; a person approves payments. DPDP processor clause. |
| 7 | Micro-SaaS / Chrome extension | K3 | b4 (duplicate) | 6.8 | M3+ | [wxt-dev/wxt](https://github.com/wxt-dev/wxt) MIT | Store discovery is slow. |
| 8 | Programmatic SEO calculators + affiliate | — | b5 (duplicate) | 6.8 | 4–6 months | [withastro/astro](https://github.com/withastro/astro) MIT, astrowind MIT | Google strict on money pages; ASCI disclosure. |
| 9 | LLM cost audits for startups | — | b6 (duplicate) | 6.7 | Jan 2027 (plan) | [langfuse](https://github.com/langfuse/langfuse) MIT core, [litellm](https://github.com/BerriAI/litellm) MIT core | Trust; long B2B cycle. |
| 10 | Custom MCP servers / Claude agents for businesses | A3, K3 | HQ / b6 / b1 | 6.4 | 4–8 weeks | [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) Apache, MCP TS/Python SDKs MIT | Client data → DPDP duties. |
| 11 | AI automation agency for local businesses (setup + retainer) | A2, A3, A4, K3 | b1 (this *is* BotBhai) | 6.2 | b1's plan (pilot by 15 Dec) | [pipecat](https://github.com/pipecat-ai/pipecat) BSD-2, heyoo MIT (official WhatsApp Cloud API). **AVOID** Baileys/WAHA (unofficial WhatsApp Web) | Running a second agency would undercut b1. A2's cold-email agency ("$20k/mo", claimed) = spam/consent risk under TRAI/DPDP. |
| 12 | Clipping / repurposing long video → shorts | K1 | NEW | 5.9 | 2–4 weeks | [openshorts](https://github.com/mutonby/openshorts) MIT, [whisperX](https://github.com/m-bain/whisperX) BSD-2, faster-whisper MIT | Commoditised by AI clip tools; deadlines clash with 1 h/day. |
| 13 | Voice job cards for technicians | — | b2 (duplicate) | 5.5 | not started | IndicConformer (MIT) STT | b2's 20 Oct gate will be missed. |
| 14 | Faceless Telugu YouTube channel | B3, B4, K1 | b5 (as a free funnel only) | 5.3 | months (monetisation thresholds) | [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) MIT, Remotion (free ≤3 people), Indic Parler-TTS Apache | YouTube's July-2025 "inauthentic / mass-produced content" rule demonetises templated AI channels (B4). Indian views pay little (B3: "7–20 cents per 1,000 Shorts views", claimed). Tick the synthetic-content box. |
| 15 | AI voice receptionist (Telugu/Hindi), sold separately | A3, A4, B5, B6 | b1 add-on (already in b1's voice stack) | 4.6 | after b1 sells | Pipecat / LiveKit Agents (Apache); Sarvam Voice Agents | TRAI: no outbound calls without consent; DPDP for recordings; say it's an AI. B5's "$5–10K per agent" (claimed) is US pricing. |
| 16 | Print-on-demand shop run by Claude overnight * | A5 | — reject | 3.8* | — | — | Sponsored; trademark/IP risk from copying best-sellers; GST for goods. |
| 17 | Dropshipping run by Claude | K4 | — reject | 3.5 | — | — | Needs ad spend, COD returns, GST registration for goods. |
| 18 | Paper-trading research tools | — | b7 (duplicate) | 5.5 | never by design | — | Selling signals = SEBI risk. |

Rejected outright: LinkedIn scraping skill (A1, breaks LinkedIn terms + rule 4), sleep-video channels (B4, demonetisation), cold-email agency at volume (A2, TRAI/DPDP).

## 3. Voice: ElevenLabs vs open models vs Sarvam

| | ElevenLabs | Sarvam (Indian API) | Open models (₹0) |
|---|---|---|---|
| Telugu | Only v3/v4 models (Multilingual v2 and Flash v2.5 have **no** Telugu) | Yes (te-IN), 11 Indian languages, 83 voices | [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) Apache-2.0 (Telugu ✓); [IndicF5](https://huggingface.co/ai4bharat/IndicF5) MIT (voice clone, needs consent) |
| Text-to-speech price | $0.08 / 1k chars (₹7.04) v3/v4; plans $6 / $22 / $99 per month (₹528 / ₹1,936 / ₹8,712) | Bulbul V4 Flash ₹2.00 / 1k chars (₹1.85 on Pro); Bulbul V3 ₹3.00 | ₹0 (free CPU for batch, faster on free Colab GPU) |
| Voice agents | $0.08/min over plan minutes + LLM + your own phone line | ₹3.50/min all-in (STT + LLM + TTS); phone ₹0.20 / 30 s + ₹59 per number / 30 days | Build it: Pipecat + IndicConformer (MIT) + Gemma 4 E4B (now Apache-2.0) |
| Commercial use | **Free plan = non-commercial only**, needs "elevenlabs.io" in the title. Paid plans OK | Yes | Yes for Apache/MIT. **Not** for mms-tts-tel, F5-TTS (CC-BY-NC), XTTS-v2 (Coqui NC). Also avoid sarvam-translate (GPL-3.0) |
| Rupee billing | No (USD) | Yes, credits don't expire | — |

**₹ per month (before 18% GST):**

| Job | Pick | Cost | ElevenLabs equivalent |
|---|---|---|---|
| Telugu voiceover, 100k chars (~100 min audio) | Sarvam Bulbul V4 Flash | **₹200** (₹0 with Indic Parler-TTS) | Creator ₹1,936 |
| BotBhai Telugu phone receptionist, 1,000 call-minutes | Sarvam Voice Agents | **≈ ₹3,960** (₹3,500 + ~₹400 line + ₹59 number) | ≈ ₹7,040 + LLM + phone line (over budget) |
| Course narration, 100k chars (te/hi/en) | Sarvam for te/hi + Kokoro-82M (Apache, CPU) for English | **₹200–300** | Starter ₹528 / Creator ₹1,936 (best English or Akhil's cloned voice) |

**Recommendation:** keep Sarvam as BotBhai's voice (it already is) and use it for any Telugu narration; Indic Parler-TTS for ₹0 batch jobs; ElevenLabs only as an optional paid premium for an English showcase voice, never on its Free plan. Sources: elevenlabs.io/pricing, /pricing/api, ElevenLabs terms + model docs; sarvam.ai pricing pages; Hugging Face model cards (all fetched 18 Oct 2026).

## 4. World swaps

| World | Verdict | What changes | Evidence |
|---|---|---|---|
| 🏰 HQ | **UPGRADE** | Focus rule: CEO time on 2–3 live worlds (b1, b3, one B2B way in); agents stop building ahead of selling. One first-rupee path: UPI QR (C08) → one sale. | 47 agent items ticked, 0 CEO items, ₹0 revenue. Every creator: selling > building. |
| 🤖 b1 BotBhai | **KEEP + UPGRADE** | Add two menu items creators say sell: missed-call/after-hours voice receptionist (Sarvam, inbound only) and invoice/document → draft bill. A live demo is the sales tool (B6). | A2, A3, A4, B5, B6: local-business automation with setup + retainer is the most repeated model. b1 is already built (623 checks green). |
| 🛠️ b2 JobCard | **PARK** | Revisit at the 15 Dec review only if b1 sells; its voice→card logic can become a b1 add-on later. | No interviews done; 20 Oct gate will be missed; no video evidence for this niche. |
| 📚 b3 Kits | **UPGRADE** | Becomes the digital-products world: Sheets kits + Claude Skill packs + n8n templates + the workshop recording. Manual UPI delivery works from day 1. | Rank 1 + 3 ideas; A1, A6, B1, B2. Fastest first rupee in the plan. GATE 2027 tracker must sell now. |
| 🧩 b4 Tab Lifeboat | **PARK** (agent-only) | No CEO time; ship when the $5 store fee is approved. | Same idea scored 6.8 but first rupee M3+; no video evidence. |
| 🛍️ b5 Deals & Tools | **UPGRADE** (Akhil decides) | Keep calculators on autopilot. Proposal: swap the Telugu deals channel for a Telugu AI-tips channel (human-led, not mass-produced) that feeds b3's packs and the workshop. | Affiliate revenue tiny in plan (₹800 in M3); B2: funnel long video → freebie → email → product; B4: templated AI channels lose ads, human-led ones don't. |
| 📊 b6 Ledger Peaks | **KEEP + UPGRADE the way in** | Add founder ghostwriting (rank 2) and small MCP/agent builds as trust-building first jobs for the same founders before the X-ray sale. | Long B2B cycle + trust gap in plan; K1, A3. |
| 🔮 b7 Trading Lab | **PARK** | Paper gate runs at zero CEO time; never sold as signals. | SEBI; 91% F&O loss study in its own PLAN. |

Nothing here was restructured or deleted; the three decisions are C30–C32 in `00-hq/ROADMAP.md`.

## 5. Follow-ups (not read yet)

Unread leads for a second pass: mJLuN-kXzKI (12 ways), E57vDFkBu_Q (Alek, digital products), zMouHT0r8dY (20 agency offers), HILk6VrGQ_4 + XenE9mV0yyE (Hindi agency videos), JrFZ_ky7AzE (Claude for KDP books), Liam Ottley (Retell), Bolna (₹5/min Indian voice agents). Agent notes with full tables are in the session scratchpad only (not committed).
