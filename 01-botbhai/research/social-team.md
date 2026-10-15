# BotBhai Social Team · research (15 Oct 2026)

**Why:** Akhil sent the YouTube Short "I Built an Entire Social Media Team With 0 Employees" (ReStructure AI, https://youtube.com/shorts/JhM-rGP5Kx0) and asked to update BotBhai from it.
**What could be read:** the video's title and channel (YouTube oEmbed). The session cannot watch video frames or hear audio, and downloading YouTube videos breaks YouTube's terms, so the frames were **not** reviewed. The idea in the title (a set of AI "roles" doing a social media team's job) was rebuilt from public sources below.

## The idea, as it applies to BotBhai clients
A Hyderabad salon, gym, coaching centre or builder can't afford a social media person (₹15–25k a month). BotBhai already holds their services, prices, FAQs, address and WhatsApp number. A "team" of small programs can turn that into a month of posts, and the owner only taps OK on WhatsApp.

| Role in a real team | BotBhai module | What it does |
|---|---|---|
| Strategist | `social/plan.py` | 4-week calendar: 1 Reel + 1 carousel + 1 post + 2 stories a week, Telangana festivals, pillar mix |
| Copywriter | `social/copywriter.py` | English caption + one Telugu line, 3–5 local hashtags, WhatsApp link, Reel script |
| Legal check | `social/compliance.py` | Blocks claims Indian ad rules forbid, before the owner even sees them |
| Designer | `social/design.py` | Branded 1080×1350 JPEGs, 1080×1920 stories, carousel slides, 7-second Reel MP4 |
| Manager | `social/approve.py` | One WhatsApp message a week; owner replies OK / skip 3 / change 2: … / photo 4 |
| Scheduler | `social/publish.py` | Posts approved items through Meta's official API at the planned time |
| Analyst | `social/analyst.py` | Weekly report; shifts next month toward what earned saves and shares |

## Evidence
| Source | Finding | Used for |
|---|---|---|
| Metricool × HypeAuditor study of 700M posts (H1 2025) | Accounts under 1,000 followers: median Reel reach 134 vs carousels 56 vs images 23; carousels earn more likes as accounts grow | One Reel a week for reach, one carousel for saves |
| Meta, Instagram Content Publishing docs ([link](https://developers.facebook.com/docs/instagram-platform/content-publishing)) and IG User Media reference ([link](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)) | Container → status → `media_publish`; JPEG only; carousels up to 10; Reels via `media_type=REELS`; stories via `STORIES`; rolling 24-hour cap read from `content_publishing_limit`; media must be at a public URL; `alt_text` on images | `publish.py` follows this exactly; tests check the call order |
| Instagram creator guidance (Mosseri, 2024–25) | Use 3–5 relevant hashtags; sends/shares and saves are strong ranking signals | Hashtag cap; analyst weights saves and shares ×3 |
| ASCI Code + influencer guidelines | No misleading/unverifiable claims; paid partnerships need a clear label | Blocks "guaranteed", "100%", "permanent", "miracle"; #ad rule |
| ASCI skin-tone guidelines | No "fair is better" messages | Blocks fairness/whitening |
| Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 | No claims to cure listed conditions | Blocks "cures hair fall/dandruff/PCOS…" |
| CCPA guidelines on misleading coaching ads (13 Nov 2024) | No 100% selection or job claims; toppers only with written consent | Blocks; topper warning |
| RERA Act 2016 / TG RERA (₹7.59 lakh penalty, June 2026, ad without RERA number) | RERA number in every project ad; no pre-launch sales | Real-estate captions blocked until the number is in the config |

## Open source looked at
| Project | Licence | Take-away |
|---|---|---|
| [gitroomhq/postiz-app](https://cdn.jsdelivr.net/gh/gitroomhq/postiz-app@main/README.md) | AGPL-3.0 (ideas only; never copied, per CLAUDE.md rule 3) | Multi-channel scheduler with an AI agent; their blog shows a 5-agent "marketing team" made with Claude. Confirms the role split. |
| [inovector/mixpost](https://github.com/inovector/mixpost) | MIT (Lite edition) | Self-hosted scheduler; uses official APIs and an approval/queue model, same as ours. |
| Easel and other browser-automation posters | Apache-2.0 | They drive a logged-in browser. Instagram can restrict accounts for automated behaviour, so we use only the official API. |

No code was copied. Everything in `social/` is ours (Pillow and ffmpeg are used as libraries).

## Honest rules built in
- **No fake proof.** Review posts carry a placeholder and are held until the owner sends a real review with the customer's OK. "Work" and "team" posts ask for a real photo.
- **Nothing posts without the owner's OK.** Held, blocked or un-approved items are refused by the publisher, even in a live run.
- **No account handling by us.** Live posting needs the client's own `IG_ACCESS_TOKEN` in their secrets; dry run is the default.
- **Owner opt-in on WhatsApp.** The weekly batch goes to the owner (our client) who chose the add-on, inside the 24-hour window or as an approved utility template.

## What's still needed before a client goes live (CEO queue)
1. Client: Instagram Business/Creator account linked to a Facebook Page; a Meta app with `instagram_content_publish` (+ `pages_manage_posts` for Facebook). The client creates and owns these.
2. A public folder for the images (Netlify site or Supabase storage, free tier) so Meta can fetch them.
3. Price the add-on (suggestion to decide: ₹999–1,499/month on top of BotBhai).
