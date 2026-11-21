# Your Langfuse: handover note

_Kalpa Labs · P1 AI Cost Audit · give this to the client on install day. Fill every `{{...}}`._

1. **What Langfuse is.** An open-source tool that records each AI call your app makes: which model, how many tokens, what it cost, whether it failed. Its core code is MIT-licensed, so you can keep using it after we leave, free of any Kalpa Labs contract.
2. **Where your data lives.** In your own Langfuse: `{{your server, or your Langfuse Cloud project and the region you picked}}`. Kalpa Labs does not host it and has no login to it.
3. **The two keys.** You create a project key pair in Langfuse (Settings → API keys): a public key (`pk-lf-…`) and a secret key (`sk-lf-…`). You put them yourself into the place the audit script runs (`{{your laptop / your GitHub Actions secrets}}`) as `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`. **Never send keys by chat or email**, not even to us.
4. **What our script reads.** `langfuse_pull.py` asks Langfuse only for model name, token counts, cached tokens, cost, status and time. It never requests prompt or answer text, user emails or phone numbers. The result is one file, `usage.csv`, with daily totals per feature and model.
5. **What we keep.** Only `usage.csv` and the audit report. We delete both 30 days after delivery unless you ask us in writing to keep them longer. Ask us any time to delete earlier: `{{contact email}}`.
6. **How to revoke.** When the audit is done, delete that key pair in Langfuse (Settings → API keys). The script stops working at once. Do it even if you trust us; it is good hygiene.
7. **What changes in your app.** Langfuse is added through its SDK or an OpenTelemetry exporter next to your existing AI calls. The SDK sends records in the background. Before production we test on your staging app, with Langfuse switched off, that your app still answers normally.
8. **Who to ask.** `{{name}}`, Kalpa Labs, `{{contact email}}`. Reply within 1 working day.
