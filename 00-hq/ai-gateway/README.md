# Vercel AI Gateway (AI SDK) · HQ

Free $5 of Vercel AI Gateway credit every 30 days gives Kalpa code access to DeepSeek, Kimi, GLM, Qwen and more through one key.

- `index.ts`: `generateText` from `ai` with `moonshotai/kimi-k3` (invents a holiday). Kimi K3 is a premium model ($3 / $15 per million tokens); for everyday jobs use `deepseek/deepseek-v4.1-flash` or `zai/glm-4.7-flashx` (about 40× cheaper).
- Key: `AI_GATEWAY_API_KEY`. On a machine: put it in `.env.local` here (git-ignored). In the cloud: GitHub → Settings → Secrets and variables → Actions → secret `AI_GATEWAY_API_KEY`. Never in code or chat.
- Run: `npm ci && npm start`, or GitHub → Actions → **AI Gateway check** → Run workflow.
