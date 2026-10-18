// Kalpa Labs · Vercel AI Gateway example (AI SDK).
// The key comes from the AI_GATEWAY_API_KEY environment variable:
// .env.local on a machine (git-ignored) or the GitHub Actions secret of the same name.
// This file never reads, prints or logs the key itself.
import { generateText } from 'ai';

if (!process.env.AI_GATEWAY_API_KEY) {
  console.error('AI_GATEWAY_API_KEY is not set (add it to .env.local or as a GitHub secret).');
  process.exit(1);
}

const { text, usage } = await generateText({
  model: 'moonshotai/kimi-k3',
  prompt: 'Invent a new holiday and describe its traditions.',
});

console.log(text);
console.log(`\n[tokens] in=${usage.inputTokens} out=${usage.outputTokens}`);
