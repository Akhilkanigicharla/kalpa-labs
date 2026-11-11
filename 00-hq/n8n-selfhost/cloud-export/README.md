# n8n Cloud export (9 Nov 2026)

Akhil downloaded these 18 workflows after the n8n Cloud trial ended. Cleaned: credential IDs and webhook IDs removed, all set inactive. **Not synced**: `sync.py` only loads `../workflows/`. Moving one to the self-hosted n8n is roadmap item A203 (data tables must be recreated; anything with a public URL waits for Akhil's go).

| Workflow | File | Uses n8n data tables | Public entry | Credentials |
|---|---|---|---|---|
| Save Site Lead (guarded) | `save-site-lead-guarded.json` | yes | no | telegramApi |
| Daily n8n Workflow Backup to GitHub | `daily-n8n-workflow-backup-to-github.json` | no | no | githubOAuth2Api, n8nApi |
| Kalpa Smart Router (Jev) | `kalpa-smart-router-jev.json` | no | chatTrigger | openRouterApi, typeSafeAiApi |
| n8n Activity Dashboard | `n8n-activity-dashboard.json` | no | webhook | n8nApi |
| World Keeper (daily company health) | `world-keeper-daily-company-health.json` | yes | no | githubOAuth2Api |
| Kalpa HQ Revenue Rollup (all businesses) | `kalpa-hq-revenue-rollup-all-businesses.json` | yes | no | githubOAuth2Api, telegramApi |
| Kalpa Revenue Workforce (24-item kits) | `kalpa-revenue-workforce-24-item-kits.json` | yes | no | githubOAuth2Api, groqApi, nvidiaApi |
| Kalpa CEO Daily Update (Telegram) | `kalpa-ceo-daily-update-telegram.json` | yes | no | telegramApi |
| Feedback Intake (A60, Form + Telegram + WhatsApp) | `feedback-intake-a60-form-telegram-whatsapp.json` | no | telegramTrigger, webhook | telegramApi |
| KL Usage Collector (OpenRouter) | `kl-usage-collector-openrouter.json` | yes | no | openRouterApi |
| Model Bake-off (free OpenRouter) | `model-bake-off-free-openrouter.json` | no | no | openRouterApi |
| BotBhai Groq model check (private test, A85) | `botbhai-groq-model-check-private-test-a85.json` | no | no | groqApi |
| BotBhai AI fallback (private test, A74) | `botbhai-ai-fallback-private-test-a74.json` | no | no | groqApi |
| Kalpa Site Chat (Kalpa Bhai) | `kalpa-site-chat-kalpa-bhai.json` | no | chatTrigger | groqApi |
| Read Kalpa Repo File (for agents) | `read-kalpa-repo-file-for-agents.json` | no | no | githubOAuth2Api |
| Web Search (compact, for agents) | `web-search-compact-for-agents.json` | no | no | braveSearchApi |
| Kalpa Task Runner (agents do KL Tasks) | `kalpa-task-runner-agents-do-kl-tasks.json` | yes | no | groqApi, nvidiaApi, openAiApi, openRouterApi |
| Feedback Save (A60, clean + sentiment + insert) | `feedback-save-a60-clean-sentiment-insert.json` | yes | no | openRouterApi |
