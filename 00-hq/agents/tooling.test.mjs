// A77: agent tooling policy guard. Run: node 00-hq/agents/tooling.test.mjs (no deps).
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const read = (p) => readFileSync(join(root, p), 'utf8');
let passed = 0;
const test = (name, fn) => { fn(); passed++; console.log('ok', name); };

test('AGENT-TOOLS.md exists and names all 7 add-ons', () => {
  assert.ok(existsSync(join(root, '00-hq/AGENT-TOOLS.md')));
  const doc = read('00-hq/AGENT-TOOLS.md').toLowerCase();
  for (const term of ['browser', 'memory', 'scientific', 'diagram', 'security', 'harness', 'openviking']) {
    assert.ok(doc.includes(term), `AGENT-TOOLS.md must mention "${term}"`);
  }
});

test('CLAUDE.md stays lean (<= 60 lines) and points to AGENT-TOOLS.md', () => {
  const md = read('CLAUDE.md');
  const lines = md.replace(/\n$/, '').split('\n').length;
  assert.ok(lines <= 60, `CLAUDE.md has ${lines} lines`);
  assert.ok(md.includes('00-hq/AGENT-TOOLS.md'));
});

const settings = JSON.parse(read('.claude/settings.json'));
test('settings.json keeps playwright as the only approved .mcp.json server', () => {
  assert.deepEqual(settings.enabledMcpjsonServers, ['playwright']);
  assert.equal(settings.enableAllProjectMcpServers, false);
});

test('settings.json deny list keeps old entries and blocks browser profiles + logged-in Chrome', () => {
  const deny = settings.permissions.deny;
  for (const old of ['Read(./**/.env)', 'Read(./**/.env.*)', 'Read(./**/*.pem)', 'Read(./**/*.key)',
    'Bash(sudo:*)', 'Bash(ssh:*)', 'Bash(chmod 777:*)']) assert.ok(deny.includes(old), `lost ${old}`);
  for (const rule of ['Read(~/.config/google-chrome/**)', 'Read(~/.config/chromium/**)', 'Read(~/.mozilla/**)',
    'Read(~/Library/Application Support/Google/Chrome/**)', 'Read(~/Library/Application Support/Firefox/**)',
    'Edit(~/.config/google-chrome/**)', 'Edit(~/.mozilla/**)', 'mcp__claude-in-chrome']) {
    assert.ok(deny.includes(rule), `missing deny ${rule}`);
  }
  // Claude Code skips mcp__ rules that carry parentheses, so none may be written that way.
  assert.ok(!deny.some((r) => /^mcp__.*\(/.test(r)), 'mcp__ deny rules must not use parentheses');
});

test('no third-party memory MCP server is configured or enabled', () => {
  const memoryish = /mem0|memory|zep|letta|openviking|viking|cognee|hindsight|engram|mempalace|supermemory|graphiti/i;
  const mcp = JSON.parse(read('.mcp.json'));
  for (const [name, cfg] of Object.entries(mcp.mcpServers || {})) {
    assert.ok(!memoryish.test(name + ' ' + JSON.stringify(cfg)), `memory server in .mcp.json: ${name}`);
  }
  for (const name of settings.enabledMcpjsonServers || []) assert.ok(!memoryish.test(name));
  for (const plugin of Object.keys(settings.enabledPlugins || {})) assert.ok(!memoryish.test(plugin), plugin);
});

test('diagrams skill has valid front matter', () => {
  const md = read('.claude/skills/diagrams/SKILL.md');
  const m = md.match(/^---\n([\s\S]*?)\n---\n/);
  assert.ok(m, 'front matter block');
  const name = m[1].match(/^name:\s*(.+)$/m)?.[1].trim();
  const desc = m[1].match(/^description:\s*(.+)$/m)?.[1].trim();
  assert.equal(name, 'diagrams');
  assert.ok(desc && desc.length > 20 && desc.length <= 1024, 'description 21..1024 chars');
  for (const hex of ['#2F6A3A', '#6B4226', '#C38E12', '#F2EEE3']) assert.ok(md.includes(hex), hex);
});

test('architecture.md has a mermaid diagram covering HQ, 7 worlds, n8n and Actions', () => {
  const md = read('00-hq/design/architecture.md');
  const block = md.match(/```mermaid\n([\s\S]*?)```/);
  assert.ok(block, 'mermaid block');
  for (const t of ['HQ', 'BotBhai', 'JobCard', 'Kits', 'Tab Lifeboat', 'Deals', 'Ledger Peaks', 'Trading Lab',
    'Task Runner', 'GitHub Actions']) assert.ok(block[1].includes(t), `diagram missing ${t}`);
});

console.log(`\n${passed} tooling checks passed`);
