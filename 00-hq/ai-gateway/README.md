# Vercel AI Gateway (AI SDK) · HQ

Free $5 of Vercel AI Gateway credit every 30 days gives Kalpa code access to DeepSeek, Kimi, GLM, Qwen and more through one key.

- `index.ts`: `generateText` from `ai`; default model `moonshotai/kimi-k3` (invents a holiday). **Kimi K3 needs paid Vercel credits** (free tier answers HTTP 403). Set `AI_MODEL=deepseek/deepseek-v4.1-flash` or `zai/glm-4.7-flashx` for the free $5 tier; the GitHub check uses DeepSeek by default.
- Key: `AI_GATEWAY_API_KEY`. On a machine: put it in `.env.local` here (git-ignored). In the cloud: GitHub → Settings → Secrets and variables → Actions → secret `AI_GATEWAY_API_KEY`. Never in code or chat.
- Run: `npm ci && npm start`, or GitHub → Actions → **AI Gateway check** → Run workflow.
