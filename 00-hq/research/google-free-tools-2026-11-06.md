# Google free tools: what we use and how (6 Nov 2026)

Akhil, 6 Nov: "use Google free tools … transfer 50-50 work load to that set and remaining to our existing setup." Checked today with two sources each (links at the end); "free" means no card, recurring.

| Tool | Free? (6 Nov 2026) | Our use | Status |
|---|---|---|---|
| **Gemini API (Google AI Studio key)** | Yes, no card. Flash models about 10-15 requests/min and about 1,500/day per project (Google does not publish one table; check aistudio.google.com rate-limit page). Free-tier inputs may be used by Google to improve models. | **50% of agent work:** worlds b2, b4, b6, hq start on Gemini, b1, b3, b5, b7 on Groq/OpenRouter; Vigil checks each draft with a different provider. **n8n Morning Councils** run on Gemini. Never send customer personal data (training clause), so NOT used in the website chat or BotBhai. | built; waits for the `GEMINI_API_KEY` GitHub secret (C60) |
| **Stitch** (stitch.withgoogle.com) | Free, daily credits, "available where Gemini is" | Quick screen mock-ups for the BotBhai owner app and JobCard before Claude builds them in our design system | Akhil may try |
| **Pomelli** | Free Labs tool; India on the list; English only, 18+ | On-brand social post images for Telugu Deals and Kalpa launch, from our website's look | after website v7 is live |
| **NotebookLM** | Free | Akhil reads long agent drafts and research by asking questions or listening to audio summaries | Akhil may try |
| Opal | Free but **Google shuts it down on 17 Nov 2026** | none | ❌ skip |
| Antigravity (IDE/CLI), Gemini CLI | Desktop install (rule 2); Gemini CLI personal-account free login ended 18 Jun 2026 | none (Claude + GitHub Actions do this) | ❌ skip |
| Mixboard | Free Labs moodboards | optional for design ideas | later |

Sources: Gemini API free tier (klymentiev.com/blog/gemini-api-free-tier, tokenmix.ai/blog/gemini-api-free-tier-limits); Gemini CLI change (agentdeals.dev/vendor/gemini-cli); Stitch/Opal/Pomelli limits and countries (claudecodeclub.ai/free-resources/free-google-ai-tools). Exact model names in the free tier differ between sources: the runner tries gemini-2.5-flash, then gemini-2.5-flash-lite, then falls back to Groq/OpenRouter, so a wrong name costs nothing.
