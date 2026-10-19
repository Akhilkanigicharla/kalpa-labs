// Re-run saved agent evals against the live agent before any prompt/model change goes live.
// Usage: node 00-hq/agents/evals/run.js kalpa-bhai   (no secrets needed; uses the agent's own chat endpoint)
const fs = require('fs'), path = require('path');
const name = process.argv[2] || 'kalpa-bhai';
const spec = JSON.parse(fs.readFileSync(path.join(__dirname, name + '.json'), 'utf8'));
function check(c, out) {
  const low = out.toLowerCase(), fails = [];
  for (const w of c.must_contain) if (!low.includes(w.toLowerCase())) fails.push('missing "' + w + '"');
  for (const w of c.must_not_contain) if (low.includes(w.toLowerCase())) fails.push('contains "' + w + '"');
  return fails;
}
module.exports = { check };
if (require.main === module) (async () => {
  let bad = 0;
  for (const c of spec.cases) {
    const r = await fetch(spec.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'sendMessage', sessionId: 'eval-' + c.id + '-' + Date.now(), chatInput: c.ask }) });
    const d = await r.json(); const out = String((Array.isArray(d) ? d[0]?.output : d.output) || '');
    const fails = check(c, out); if (fails.length) bad++;
    console.log((fails.length ? '  ✗ ' : '  ✓ ') + c.id + (fails.length ? ': ' + fails.join(', ') : '') + '\n    ' + out.slice(0, 220));
  }
  console.log(bad ? `${bad} case(s) failed` : `all ${spec.cases.length} cases passed`); process.exit(bad ? 1 : 0);
})();
