# Cloud hosting plan for the server apps

**Answer first:** **n8n Cloud stays the brain.** None of the new server apps replaces an n8n agent. They are **tools the agents call**. Phase 0 and Phase 1 cost ₹0 and need no new server: GitHub Actions does scraping and video rendering, PostHog Cloud does analytics, and a Hugging Face Space runs Presenton. Heavy apps (Chatwoot, Frappe CRM) wait until there is revenue.

Rules this plan follows: free tiers only, no accounts created by Claude, secrets only in GitHub/Netlify/Supabase/HF secrets that Akhil sets, and nothing installed on Akhil's PC (`CLAUDE.md` hard rules 1–2). Limits were checked on 17 Oct 2026, with sources cited. Free tiers change, so re-check before relying on any number.

## Free hosting options and their limits

| Host | Free limits (cited) | Good for | Bad for |
|---|---|---|---|
| **GitHub Actions** | Public repos free. Private repos get a monthly minute quota (2,000 min on Free in GitHub's docs, which may be out of date; verify on github.com/pricing) ([GitHub billing docs](https://docs.github.com/billing/managing-billing-for-your-products/managing-billing-for-github-actions)) | Batch jobs: Scrapling runs, HyperFrames renders, tests | Anything that must answer 24×7 |
| **GitHub Codespaces** | 120 core-hours plus 15 GB-month storage per month on a personal account, so a 2-core machine gets about 60 hours ([GitHub Codespaces billing](https://docs.github.com/ja/billing/managing-billing-for-github-codespaces/about-billing-for-codespaces)) | Trying Docker apps by hand (Presenton, openshorts, Expo dev) | Always-on hosting |
| **Hugging Face Spaces (CPU basic)** | 2 vCPU, 16 GB RAM and 50 GB of **non-persistent** disk. Sleeps after 48 h idle. Only ports 80/443/8080 ([HF Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [HF manage-spaces guide](https://huggingface.co/docs/huggingface_hub/main/guides/manage-spaces)) | Docker apps with big RAM needs but no saved data (Presenton) | Databases; anything that must keep files |
| **Cloudflare Workers / Pages (free)** | Account-level daily quotas; Workers AI has a daily allocation (per the [Talorys README](https://github.com/rociiu/talorys)); exact numbers: see Cloudflare pricing (not fetched) | Talorys, OpenSEO (Cloudflare self-host guide) | Docker apps |
| **Render (free)** | 512 MB RAM and 0.1 CPU. Spins down after 15 min idle, up to 1 min to wake. 750 h per workspace per month. Free Postgres expires after 30 days ([Render free docs](https://docs.render.com/free)) | Tiny webhooks | Chatwoot, Presenton (too little RAM) |
| **Koyeb (free)** | One instance per organisation: 512 MB, 0.1 vCPU, 2 GB SSD, Frankfurt or Washington ([Koyeb pricing FAQ](https://www.koyeb.com/docs/faq/pricing)) | Tiny always-on API | Anything above 512 MB |
| **Oracle Cloud Always Free** | Ampere A1 up to 4 OCPU and 24 GB RAM in docs (some report 2 OCPU / 12 GB for new accounts). **Needs a Visa/Mastercard credit card**; RuPay and prepaid reportedly declined ([dev.to, India report](https://dev.to/ashish-codejourney/getting-a-free-oracle-cloud-vps-from-india-the-full-guide-and-the-rupay-wall-nobody-warns-you-4p5o), [Oracle free tier](https://developer.oracle.com/free.html)) | The only free box big enough for Chatwoot (needs 4 GB RAM minimum, per [Chatwoot docs](https://developers.chatwoot.com/self-hosted/deployment/requirements)) | **CEO decision**: card on file |
| **Vendor free clouds** | PostHog Cloud free plan (limits unknown from here; posthog.com did not resolve from the build sandbox) | Analytics without running a server | — |

## Phase 0: this week, ₹0, no new account except PostHog

| What | Where | Replaces / joins in n8n | Who acts |
|---|---|---|---|
| **PostHog Cloud** snippet on the BotBhai web pages, calculator site (`05-deals/site`) and extension pages | PostHog Cloud free | **Dash** reads PostHog via the PostHog MCP (Claude) or the PostHog API (n8n HTTP node). Nothing replaced; it adds real numbers | Akhil signs up and puts the project key in Netlify env vars himself. Claude then adds the snippet |
| **Playwright** checks | Already in GitHub Actions (BotBhai CI) | **Probe** and **Vigil**. Nothing replaced | Claude |
| **Cloudflare security-audit skill** runs | Cloud Claude sessions, sandboxed | **Vigil** gets an audit report per world before go-live | Claude |

## Phase 1: next 2 weeks, ₹0

| What | Where | How n8n uses it | Notes |
|---|---|---|---|
| **HyperFrames renders** | GitHub Actions job (`workflow_dispatch`) on Ubuntu with Node 22 + FFmpeg. Output MP4 as a private artifact | **Reel** triggers the workflow from n8n (GitHub node), then fetches the artifact link | HTML compositions use Kalamkari tokens (`00-hq/design/tokens.css`). Rendering stays out of n8n, which has no FFmpeg |
| **Scrapling jobs** | GitHub Actions cron (`pip install scrapling` into a fresh venv) | **Scout** and **Deal** read the results (CSV artifact or Supabase table) | Only allowed sources: our sites, public price pages that permit it, robots.txt respected. **Never** Google Maps, Justdial, Instagram or personal numbers (rule 4). Amazon prices should come from the official affiliate API where possible, not scraping (ASCI and Amazon terms) |
| **Presenton** | Hugging Face **Docker Space** (CPU basic, private), image `ghcr.io/presenton/presenton`, `LLM=openrouter` with a free model, `DISABLE_ANONYMOUS_TRACKING=true`, `PRESENTON_COMMUNITY_ENABLED=false` | **Kavi** calls its `/mcp` or REST API with a Presenton key stored in n8n credentials | Disk is not persistent, so download each deck right away. OpenRouter key goes in **HF Space secrets** (Akhil sets it). Docker run flags are from the [Presenton README](https://github.com/presenton/presenton) |

Example GitHub Actions skeleton for the render job (placeholders only; Claude writes the real file when the item is built):

```yaml
# .github/workflows/render-video.yml  (to be added in a later PR, not this one)
on: { workflow_dispatch: { inputs: { composition: { required: true } } } }
jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: sudo apt-get update && sudo apt-get install -y ffmpeg
      - run: npx hyperframes render "${{ inputs.composition }}"
      - uses: actions/upload-artifact@v4
        with: { name: video, path: "**/*.mp4", retention-days: 7 }
```

## Phase 2: after the first paying salon, still ₹0 to ₹500/month

| What | Where | Why then |
|---|---|---|
| **OpenSEO** | Cloudflare free plan (its own self-host guide) | Only once Akhil approves a **DataForSEO** budget (pay per request) |
| **openshorts** | Codespaces on demand (8 GB+ RAM recommended by its README) | Needs a Gemini key (free tier) and optionally paid fal.ai, ElevenLabs and Upload-Post. Try after HyperFrames proves the video pipeline |
| **Talorys** | Akhil's Cloudflare account | Personal CEO assistant. Repo is 1 week old, so wait for it to mature |

## Phase 3: only with revenue or a CEO decision

| What | Where | Note |
|---|---|---|
| Chatwoot | Oracle Always Free (card) or a paid 4 GB VPS | BotBhai already has its own inbox (A04). Move only if salons need email/Instagram channels too |
| Frappe CRM | Same box | AGPL: internal use only, never inside sold code |

## Not hosted (decided)

| App | Reason |
|---|---|
| Dify, multica, Typebot, Zapier MCP | Duplicate n8n. Licence conditions (Dify multi-tenant ban, Typebot FSL competing-use ban), telemetry (multica) |
| Invoice Ninja, Autumn | BotBhai billing is built (A05). ELv2 bars hosting for clients. Autumn is Stripe-centric |
| Mautic | Heavy PHP stack. TRAI/consent rules limit outbound marketing anyway |
| OmniRoute, freellmapi | ToS risk from pooling free tiers. n8n already uses OpenRouter free models directly |
| MiroFish | AGPL plus "prediction" use conflicts with SEBI rules for b7 (paper only, no tips) |

## What changes in n8n

- **Nothing is removed.** The 22 agents keep their jobs.
- **New tool wiring:** Reel gets a GitHub-workflow trigger (HyperFrames). Kavi gets a Presenton HTTP tool. Scout and Deal read Scrapling output. Dash reads PostHog.
- **Credentials:** each new key (OpenRouter for the Space, Presenton API key, PostHog project key) is created and pasted by Akhil into n8n credentials or the host's secret store. Claude never sees the value.

**Next step:** Akhil creates the PostHog Cloud account (10 minutes) and says "PostHog ready". Claude then adds the snippet and wires Dash.
