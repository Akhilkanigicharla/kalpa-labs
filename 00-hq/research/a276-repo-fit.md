# A276 · Five repos from Corey Ganim's video as Kalpa paid services

Checked 20 Nov 2026 (Lane B build sprint). Source: `videos-2026-11-14.md`. Free-model drafts K120, K122, K132 used for the offer wording only; every licence below was checked by Claude today.

**How licences were checked (rule 8, two sources each):** (1) GitHub's own licence field via the repository search API, (2) the repo's `LICENSE` file read raw from its default branch. Both agreed for all six. Which `openshorts` the video meant is unverified (several MIT repos share the name).

## Fit table

| Repo (link) | Licence (LICENSE file) | Extra conditions that matter to us | What a Hyderabad business pays us for | Offer: assessment → setup + monthly (draft, Akhil sets final) | Main risk | Fit |
|---|---|---|---|---|---|---|
| [presenton/presenton](https://github.com/presenton/presenton) | Apache-2.0 | Keep NOTICE + licence text | Branded sales/proposal decks made from a short brief, on the client's own server | ₹1,500 deck review → ₹10,000 setup + ₹3,000/mo | Paid model API bills if usage is not capped; use free models + a monthly cap | Good |
| [faris-sait/openshorts](https://github.com/faris-sait/openshorts) (most-starred; mutonby/openshorts LICENSE file also MIT, but GitHub search did not list it, so 1 source) | MIT | Keep copyright line | Long video → captioned shorts for shops, coaching centres, real estate | ₹2,000 audit + 3 sample shorts → ₹15,000 setup + ₹5,000/mo | Upload only the client's own videos; posting stays with the client (no auto-posting for them) | Good |
| [every-app/open-seo](https://github.com/every-app/open-seo) | MIT | Keep copyright line | Local SEO audit + monthly keyword/report for service businesses | ₹2,500 audit → ₹12,000 setup + ₹4,000/mo | Paid SEO data APIs may be needed; check before quoting; no AI-spam pages | Good (pairs with our 20 SEO checks) |
| [langgenius/dify](https://github.com/langgenius/dify) | "Dify Open Source License" = Apache-2.0 **plus conditions** | (a) no multi-tenant service without Dify's written OK; (b) don't remove/modify the Dify logo or copyright in the console/app | 5-language support chatbot / workflow, one private instance per client | ₹2,000 flow blueprint → ₹20,000 setup + ₹6,000/mo | One instance per client only; a shared "Kalpa Dify for many shops" needs Dify's commercial licence. Overlaps BotBhai + Agent Engine (A240) | Fair (only single-tenant) |
| [paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) | GPL-3.0 | Rule 3: never copy GPL code into a product we sell. Installing it **unmodified** for a client and charging for setup/support is allowed | Scan + search bills, GST papers, contracts (OCR) on the client's own machine/server | ₹1,500 paper-flow audit → ₹18,000 setup + ₹4,000/mo | Client data is sensitive (DPDP): their server, our processor clause, backups they own | Good as a service; never as our code |
| [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) (named in the video) | BSD-3-Clause | Keep copyright + no use of author's name to promote | Not sold on its own; a tool inside other jobs | — | Rule 4: never on Google Maps, Justdial, Instagram or personal numbers; only sites whose terms allow it | Tool only |

## Notes
- Prices are drafts from K122 (marked ESTIMATE by the free model). They are our own offer, not a market fact; Akhil decides before any customer sees them.
- Hosting: all five run on the client's machine or a free tier the client owns; we never hold client secrets (rule 1).
- Fastest to sell with what we already have: open-seo (we run the same 20 SEO checks on our own site) and paperless-ngx (clear pain: GST paperwork).
- Not checked: model API or SEO-data API prices; any quote that depends on them says "unverified" until checked.
