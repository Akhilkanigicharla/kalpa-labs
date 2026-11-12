# A152 · b2 Mobile app: where people pay, 10 ideas, 3 for Akhil to pick

Research by Claude, 6 Nov 2026 (evening IST). Every number below was found in two sources today unless marked UNVERIFIED. Akhil picks; Claude does not choose for him (VISION.md, CLAUDE.md rule 0).

## 1. The answer in 5 lines
1. People pay most for apps in the US and other rich countries: revenue per install at day 60 is about 5x higher in North America than in India/South-East Asia (RevenueCat SOSA 2026, via SaaStr).
2. A **hard paywall** (pay after a free trial) earns about 8x more per install than freemium: $2.32 vs $0.27 at day 14 (RevenueCat SOSA 2026; SaaStr + ppc.land + mobilemarketingreads).
3. **Photo & Video** is the category where the most new apps reach $1,000 a month (21.4%); only 17% of all new apps get there (RevenueCat via 9to5mac + apfelpatient + computing.co.uk).
4. AI apps earn 41% more per payer but lose subscribers about 30% faster (annual retention 21.1% vs 30.7%) (TechCrunch 10 Mar 2026 + veed.io + ppc.land). So AI must be a daily habit, not a one-time trick.
5. Shortlist: **(A) AI Vedic astrology + naming + muhurat app for Indians worldwide**, **(B) AI photo studio (passport/visa photos + product photos)**, **(C) AI mother-tongue tutor for NRI kids (Telugu, Hindi, Tamil…)**. All three start as a free web app (PWA), then Play Store.

## 2. Where the money is (market facts)
| Fact | Status | Sources |
|---|---|---|
| Consumer app spend 2025 ≈ $155.8 B; non-game apps grew 33.9% to $82.6 B and passed games ($72.2 B) | VERIFIED | Appfigures via dataconomy; savedelete (non-game overtook games 2025) |
| Q2 2026: GenAI spend +108% YoY; 9 of top 10 non-game categories grew; games fell | VERIFIED (1 primary + press) | Sensor Tower Q2 2026 via idropnews; Q1 2026 IAP $43.5 B (+9%) via mobilemarketingreads |
| Top-grossing apps 2025: TikTok ~$3.3 B, Google One ~$2.5–2.6 B, ChatGPT ~$2.4 B, YouTube ~$2.1 B | VERIFIED | savedelete; xtendedview; mmminimal |
| New subscription apps launched per month: ~14,700 (Jan 2026) vs 2,000 (Jan 2022) | VERIFIED | SaaStr; RevenueCat founder letter |
| Median download-to-paid in 35 days ≈ 2.0%; North America 2.8% | VERIFIED | thesocialoutline; SaaStr |
| Astrotalk (India astrology app) FY25 revenue from operations ₹1,176 cr, ~20% from outside India | VERIFIED | Outlook Business; startuppedia (RoC filings); entrackr |
| Shoonya Kids (Indian-language app for kids, US) charges $5.99–7.99/month, $57.99/year | VERIFIED (App Store listing) | apps.apple.com id866047646; educationalappstore.com |

## 3. Ten ideas, scored (1 = weak, 5 = strong)
Scores are Claude's judgement on the facts above, not measured data.

| # | Idea | Demand | Will pay | Competition (5 = little) | Build effort (5 = easy) | Promotion path (5 = easy) | Total |
|---|---|---|---|---|---|---|---|
| 1 | **AI Vedic astrology + baby/business naming + muhurat** for Indians worldwide (Telugu, Hindi, English; diaspora pays in $) | 5 | 5 | 2 | 4 | 4 | **20** |
| 2 | **AI photo studio**: passport/visa photos to each country's rules + clean product photos for small sellers | 4 | 4 | 2 | 4 | 4 | **18** |
| 3 | **AI mother-tongue tutor for NRI kids** (voice chat in Telugu/Hindi/Tamil, games, parent progress) | 4 | 4 | 3 | 3 | 4 | **18** |
| 4 | AI exam-prep companion (worldwide) | 4 | 3 | 1 | 3 | 3 | 14 (overlaps b3 Exam Kits) |
| 5 | AI habit + fitness coach | 4 | 4 | 1 | 3 | 2 | 14 |
| 6 | Voice journal / meeting notes | 3 | 3 | 1 | 3 | 2 | 12 |
| 7 | Pet care tracker + AI vet questions | 3 | 3 | 3 | 3 | 2 | 14 |
| 8 | Scanner / PDF / file tools | 4 | 3 | 1 | 4 | 2 | 14 |
| 9 | Shop billing / GST invoices | 4 | 2 | 1 | 3 | 2 | 12 (Vyapar/Khatabook own it: UNVERIFIED share) |
| 10 | Short-drama video app | 5 | 5 | 1 | 1 | 1 | 13 (AppsFlyer: dominated by a few big players) |

## 4. The 3 for Akhil to pick
**A. "Kalpa Jyotish" (working name): AI Vedic astrology, naming and muhurat**
- Who pays: Indian families in India, US, UK, Gulf, Australia for baby names, business names, marriage and griha-pravesh dates, daily rasi-phalam. Proof: Astrotalk ₹1,176 cr in FY25, 20% abroad.
- How it differs: no human astrologer marketplace (that is Astrotalk's costly model); instant AI reports from open astronomy maths (Swiss Ephemeris-type calculations), in Telugu, Hindi and English, with lucky number and colour, which Akhil already uses himself.
- Money: free daily rasi + paid reports (₹99–499 / $4.99–19.99) + yearly plan.
- Safety built in: "for guidance and tradition", no health, legal or money predictions; no fear-based upsells; DPDP privacy notice for birth data. Licence check of the ephemeris library before use (Swiss Ephemeris is AGPL or paid: UNVERIFIED today, check before use; pick an MIT/BSD option or call it as a separate service).

**B. "Kalpa Photo Studio": passport/visa photos + product photos**
- Who pays: travellers and visa applicants worldwide (per-country size rules), and small online sellers. Photo & Video is the top category for new apps reaching $1k/month.
- Money: pay per photo set ($2.99 / ₹99) + seller plan for product photos.
- Free tools: open-source background removal and face checks from Hugging Face (licences checked before use).
- Risk: crowded category; must win on "accepted first time" for each country's rules.

**C. "Kalpa Bhasha Kids": AI mother-tongue tutor for NRI kids**
- Who pays: NRI parents who want kids to speak Telugu, Hindi, Tamil. Proof: Shoonya Kids charges up to $57.99/year; tutors and channels sell NRI kids programs.
- How it differs: voice conversation practice (most apps teach alphabets only), uses Kalpa's 5-language bot work.
- Money: $4.99–7.99/month, $49/year; India price lower.
- Safety built in: kids' data rules (COPPA in the US, DPDP for children in India: parent consent), no chat with strangers, parent dashboard.

## 5. Same for all three
- Launch as a free PWA web app first (no store fee), payments only after Akhil's "go" and payment setup (rules 9 and 18 Oct).
- Play Store developer account is a one-time paid fee (Akhil's call; check today's price before deciding).
- Promotion: Telugu/Hindi reels, YouTube @KalpaLabs, NRI Facebook groups and Reddit (no spam, ASCI disclosure).

## 6. For Akhil to decide (CEO queue C63)
Pick one: **A** (astrology + naming), **B** (photo studio) or **C** (NRI kids tutor). Or name your own idea.

## 7. Lessons from "How I Made $1M Building 30 Micro-Apps" (Starter Story, Sanskar Tiwari), added 12 Nov 2026
Source: stork.ai write-up of the video (the video's captions were blocked here).
- **Many small apps, not one big bet:** 30+ products in 6 years, 8 earn, about 1,000 paying customers, over $1M total. First 2 years: zero revenue.
- **One problem per app** (MagicSlides makes slides, SheetAI adds AI to Sheets, MagicForm turns content into quizzes).
- **Ideas from data:** TrustMRR (public, payment-verified revenue of 8,800+ startups), Twitter talk, his own daily pain.
- **Proof before building:** a simple offer page; only real purchases count. Kalpa rule (18 Oct): no money taken until delivery is proven, so Kalpa uses a free "notify me" list as the first signal and real payments only after Akhil's go.
- **Free distribution from stores and video:** Google Workspace add-ons, Chrome extensions, Facebook groups, AppSumo, one evergreen YouTube demo channel per product, short videos.
- **What Kalpa does with it (agent tasks):** K034 Scout: 10 TrustMRR micro-apps Kalpa could build in under 2 weeks. K035 Kavi: evergreen demo video scripts for the 3 prototypes. K036 Forge: exam tracker as a free Google Sheets add-on (store = distribution). Same idea already in Kalpa: b4 Chrome extension, 3 small apps.
