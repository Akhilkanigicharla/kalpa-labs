// Kalpa Labs · Vercel AI Gateway example (AI SDK).
// The key comes from the AI_GATEWAY_API_KEY environment variable:
// .env.local on a machine (git-ignored) or the GitHub Actions secret of the same name.
// This file never reads, prints or logs the key itself.
import { generateText } from 'ai';

// Default is the requested Kimi K3 (paid credits only on Vercel); AI_MODEL overrides it,
// e.g. deepseek/deepseek-v4.1-flash, which the free $5 tier allows.
const model = process.env.AI_MODEL || 'moonshotai/kimi-k3';
const inActions = process.env.GITHUB_ACTIONS === 'true';
// Short, key-free failure note; in GitHub Actions it also becomes a run annotation.
function fail(reason: string): never {
  const msg = reason.replace(/\u001b\[[0-9;]*m/g, '').replace(/\s+/g, ' ').slice(0, 400);
  console.error(inActions ? `::error title=AI Gateway::${msg}` : msg);
  process.exit(1);
}

if (!process.env.AI_GATEWAY_API_KEY) {
  fail('AI_GATEWAY_API_KEY is not set (add it to .env.local, or as a GitHub Actions *secret*, not a variable).');
}

try {
  const { text, usage } = await generateText({
    model,
    prompt: 'Invent a new holiday and describe its traditions.',
  });
  if (!text.trim()) fail('The model returned empty text.');
  console.log(text);
  console.log(`\n[tokens] in=${usage.inputTokens} out=${usage.outputTokens}`);
  if (inActions) console.log(`::notice title=AI Gateway::OK, ${text.length} characters from ${model}`);
} catch (err) {
  const e = err as { name?: string; statusCode?: number; message?: string };
  fail(`${e.name ?? 'Error'}${e.statusCode ? ` (HTTP ${e.statusCode})` : ''}: ${e.message ?? String(err)}`);
}
