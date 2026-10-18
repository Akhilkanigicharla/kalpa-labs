# Checked facts register

| Fact | Verdict | Checked | Sources / test |
|---|---|---|---|
| Vercel AI Gateway free tier runs only a few models (`nvidia/nemotron-3.5-lightning-free`, `poolside/laguna-s-2.1-free`, `convaiinnovations/laya-free`, …); DeepSeek V4.1 Flash and Kimi K3 return HTTP 403 "Free tier users do not have access to this model" | VERIFIED | 2026-10-18 | live GitHub Actions runs 4ed380f + c42e511 (403); vercel.com/ai-gateway/models?freeTier=true |
| Earlier claim "Vercel $5 free credit covers Qwen/DeepSeek/Kimi/GLM" | WRONG | 2026-10-18 | see row above; Vercel dropped from Kalpa |
| Hugging Face Inference Providers: free (non-PRO) accounts get **no** included monthly credit | VERIFIED (1 source, official) | 2026-10-18 | huggingface.co/docs/inference-providers/pricing |
| Sarvam API: one-time ₹100 signup credit, never expires, no recurring free tier; calls fail when used up | VERIFIED | 2026-10-18 | docs.sarvam.ai/api-reference-docs/ratelimits; docs.sarvam.ai/api-reference-docs/pricing; awesome-free-ai-coding probe 2026-10-15 |
| Sarvam Bulbul v3 TTS ₹30 per 10K characters; STT ₹30/hour (₹45 with diarization) | VERIFIED (official docs) | 2026-10-18 | docs.sarvam.ai/api-reference-docs/pricing |
| Swarm report claim "Bulbul V4 Flash ₹2.00/1k chars, Voice Agents ₹3.50/min" | UNVERIFIED | 2026-10-18 | not on docs pricing page today (V4 Flash price not listed); recheck sarvam.ai/api-pricing |
| ai4bharat Indic Parler-TTS: Apache-2.0, Telugu speakers Prakash/Lalitha/Kiran, Telugu native-speaker score ~89%, 0.9B params, gated download (accept terms) | VERIFIED (model card) | 2026-10-18 | huggingface.co/ai4bharat/indic-parler-tts |
| IndicF5 ranked last of 7 TTS systems in a large Indian-language preference study | VERIFIED (paper) | 2026-10-18 | arXiv 2604.21481 |
| Groq free key serves `qwen/qwen3.8-27b` with 7,000 input tokens/min on this account | VERIFIED (live) | 2026-10-18 | n8n call_agent runs + Groq 429 message |
| NVIDIA key in n8n lists only `nemotron-3-nano-omni-30b-a3b-reasoning` | VERIFIED (live) | 2026-10-18 | n8n discover_agent_assets |
| Mistral: no free Experiment plan on Akhil's account | VERIFIED (Akhil checked) | 2026-10-18 | Akhil |
| WhatsApp Cloud API works without Meta business verification; new business portfolios get a messaging limit of 250 unique recipients per 24 h (replies inside a customer-started window don't count); verification or 2,000 good template sends raises it to 2,000 | VERIFIED | 2026-10-18 | developers.facebook.com/docs/whatsapp/messaging-limits; blueticks.co (Aug 2026) |
| n8n agent Kalpa (free NVIDIA model) launch review said "16 Nov unrealistic without WhatsApp API approval today" | WRONG (overstated) | 2026-10-18 | no approval needed to start (row above); real path = C02 Meta app + C14 SIM number + template approval for reminders |
