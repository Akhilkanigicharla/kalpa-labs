# The "41-agent AI social media team for real estate": every paid tool → our free one

Source: restructureai reel (24 Oct 2026), screenshots only. We take the ideas, not the tools.
Research: 10 KL Tasks rows run by the n8n Task Runner on free models (rows 27–36, 24 Oct). Claude then checked the key facts itself.
- Licences come from each repo's LICENSE file (shallow clone, 24 Oct) or the Hugging Face model card (24 Oct).
- Anything checked only once is marked **unverified** (rule 8).

**Status key:** ✅ built · 🔨 new roadmap item · 🟡 needs Akhil (key or connector) · ⛔ skipped, with the reason.

## Brain: "Marketing Director"
| Reel (paid) | Kalpa (free) | Licence / cost | Status |
|---|---|---|---|
| Triage, writes & runs (Claude) | n8n Task Runner, using Groq `openai/gpt-oss-120b` and OpenRouter free models. Sarvam-M is also an option (Telugu/Hindi, 24B, open model). | Groq free tier; Sarvam-M Apache-2.0 (HF card) | ✅ runner live; 🟡 C48 GROQ secret |
| "Jev decides" | The owner approves on WhatsApp ("skip 3, rest ok") | — | ✅ `social/approve.py` |
| Speaks: voiceovers (ElevenLabs) | **Indic Parler-TTS** (en, hi, te + 18 more). Fallback: **IndicF5** (hi, te; no English). English only: **Kokoro-82M** (Apache-2.0). | Parler Apache-2.0 and IndicF5 MIT, both **gated** on HF; Kokoro Apache-2.0 | 🔨 A98; 🟡 accept the HF gate |
| Speaks: buyer calls (ElevenLabs + Twilio) | BotBhai voice agent (Pipecat, BSD-2), **only when the lead asks for a call** (TRAI) | Pipecat BSD-2 | ✅ `voice/`; calls are never cold |
| Checks the work | `social/compliance.py` (ASCI, RERA no., no fake reviews) + Vigil in n8n | — | ✅ |

## Departments
| Department | Reel tools (paid) | Kalpa (free) | Status |
|---|---|---|---|
| **Data sources** | MLS, Instagram, TikTok, Reddit, Calendly, Facebook | India has no MLS: listings come from the owner's own sheet (`bot.config` catalog) plus the project's public RERA number. Instagram/Facebook data only for the owner's own account, via Meta's official API. TikTok is banned in India. Reddit: read-only and official API only, still to be researched (row 34). No scraping (rule 4). | ✅ catalog · ⛔ TikTok · 🟡 row 34 |
| **Market research** | analysts + paid data | Free public sources (RERA portals, RBI/NHB price indexes, data.gov.in), still to be researched (row 34) | 🟡 research running |
| **Content engine** | phone photos → Claude script → **Higgsfield** video → **ElevenLabs** voice → **CapCut** captions + music → **Slack** approve | photos come in on WhatsApp. Script from `copywriter.py` / n8n. **`social/walkthrough.py`**: 6–12 photos → 9:16 MP4 with camera moves. Voice from A98. Captions from **faster-whisper** (MIT) burned in with ffmpeg (A99). Approval on WhatsApp. AI motion option: **Wan2.2 TI2V-5B** (Apache-2.0); it needs a GPU, so it is "later". | ✅ A96 · 🔨 A98, A99 |
| **Content studio** | Notion calendar, Canva | `plan.csv` + Kingdom board; `design.py` (Pillow, Kalpa design system) | ✅ |
| **Publishing** | FB/IG, TikTok, LinkedIn, YouTube, Google local posts; best time per channel | `publish.py` (Meta Graph API, free). YouTube Data API v3: free, 10,000 units/day (row 35; the upload cost per video is unverified). LinkedIn and Google Business Profile APIs are free but need app/access approval (unverified). **Best time** is learned from the owner's insights CSV. | ✅ Meta · ✅ A97 · 🔨 A102 YouTube · LinkedIn/GBP later |
| **Lead intelligence** | **Manychat** (comments + DMs), Reddit alerts, real-buyer check, form, **Zapier**, CRM | Meta webhooks for own-account comments and DMs. Needs `instagram_manage_comments` / `instagram_manage_messages` + Meta App Review (row 30). Replies only inside the 24-hour window, after the person writes first. Qualify questions in BotBhai chat. n8n instead of Zapier. BotBhai inbox as the CRM. | 🔨 A100; 🟡 Meta app |
| **Booking & qualification** | **Twilio** call in 60 s, budget/timeline, **Calendly**, confirm with seller | WhatsApp reply in seconds (lead wrote first = opt-in). Budget/timeline asks in the realestate setup. BotBhai slot booking with a lock. Owner gets a WhatsApp confirm. Row 31 was rejected by Vigil (unsourced claims), so outbound calling stays out. | ✅ booking · ⛔ cold calls (TRAI) |
| **Follow-up & nurture** | Meta + Google retargeting, **Mailchimp**, texts, home-value updates, "tracks who comes back" | Retargeting is paid ads: skip until a client pays for ads. Email: free tier still to be researched (row 32). Texts: WhatsApp templates to opted-in leads only. "Who comes back": **Umami** (MIT) on the listing page with a DPDP notice. | ⛔ ads · 🟡 row 32/33 · 🔨 A103 |
| **Reviews & referrals** | review asks | BotBhai asks after a visit; posts only real reviews | ✅ compliance blocks fake ones |
| **Data & observability** | buyers per listing, speed to lead, showings, offers, activity log | 9 PM day-close + A80 owner nudges. To add: speed to lead and showings per listing. | 🔨 A101 |
| **Morning loop 7 AM** | scheduler | n8n schedule (free) | with A101 |

## YouTube agent skills (MIT, `00-hq/vendor/youtube-agent`)
| Skill | Kalpa | Status |
|---|---|---|
| yt-chapters | `social/youtube.py`: valid chapters from a faster-whisper transcript (≥3 chapters, first at 00:00, each ≥10 s) | ✅ |
| yt-package | `youtube.title_check`: 60-character desktop and 40-character mobile cut points; title ideas from n8n | ✅ |
| yt-seo | `youtube.description` (CTA + ASCI disclosure) + `tags_fit` (500 characters); text from n8n | ✅ |
| yt-plan | `plan.py` month plan + A97 times | ✅ |
| yt-script, yt-comment | n8n free models (Kavi/Echo) with the skill text as the prompt; comment replies wait for the owner's OK | via DELEGATE.md |
| yt-shorts, yt-edit | faster-whisper transcript → cut points → ffmpeg 9:16 cut | 🔨 A102 |
| yt-retention | reads the YouTube Studio CSV, like A97 | 🔨 A102 |
| yt-viral, yt-audit | YouTube Data API search (free quota) instead of yt-dlp downloads: YouTube's terms forbid downloading | 🔨 A102 |

## Checked licences (24 Oct 2026)
- **Copied as code: no.** Run as separate tools: faster-whisper MIT · Kokoro Apache-2.0 · Indic Parler-TTS Apache-2.0 · IndicF5 MIT (HF card; the GitHub repo has no LICENSE file) · Wan2.2 Apache-2.0 · LTX-Video Apache-2.0 · Sarvam-M Apache-2.0 · Umami MIT · OSRM BSD-2.
- **Library or service only:** ffmpeg (LGPL/GPL build, called as a program) · LanguageTool LGPL.
- **Never copied (AGPL):** Postiz, listmonk, Twenty CRM.

## Keys and connectors Akhil adds himself (never pasted in chat)
1. **GROQ_API_KEY** GitHub secret (C48): the free model for writing.
2. **Hugging Face:** accept the terms on the `ai4bharat/indic-parler-tts` page with the kalpalabs5145 account, then add a read token as the `HF_TOKEN` GitHub secret (A98).
3. **Meta app** for comments and DMs + `IG_ACCESS_TOKEN` (A100). App Review is needed before real clients.
4. **YouTube:** Google Cloud OAuth client for the Data API (A102). Free, with no card for the API itself (unverified).
