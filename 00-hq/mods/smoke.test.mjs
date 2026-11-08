// Logic smoke test for kalpa-mods with a fake `on` and `$` (NOT the real Claude Code runtime; see README).
import assert from 'node:assert'

async function harness(session) {
  const { register } = await import('./kalpa-mods/hooks/register.js?' + session)  // one copy per session, as in Claude Code
  const hooks = {}, toasts = [], store = globalThis.__store ||= {}
  globalThis.__now ||= 1_000_000
  const on = (ev, a, b) => { (hooks[ev] ||= []).push(b || a) }
  const $ = { clock: { now: () => globalThis.__now }, ui: { toast: t => toasts.push(t), invalidate() {} },
    store: { get: async k => store[k], set: async (k, v) => { store[k] = v } },
    session: { id: () => session, usage: async () => ({ context: { tokens: 480000 } }) } }
  const fire = (ev, e) => hooks[ev][0]($, e, async x => x ?? e)
  register(on, { cacheTtlSeconds: 300, collisionMinutes: 15 })
  return { fire, toasts, tick: ms => { globalThis.__now += ms } }
}

const a = await harness('A'), b = await harness('B')
await a.fire('session.start', {}); await b.fire('session.start', {})

// Cache Keeper: warm reply -> no toast; cold reply -> toast with token estimate
await a.fire('turn.complete', {}); a.tick(60_000); await a.fire('prompt.submit', { text: 'hi' })
assert.strictEqual(a.toasts.length, 0, 'no toast while warm')
await a.fire('turn.complete', {}); a.tick(400_000); await a.fire('prompt.submit', { text: 'back' })
assert.match(a.toasts[0], /cache went cold.*480k tokens/, 'cold toast')

// Goal Meter: /goal starts it, TodoWrite updates the spinner suffix
await a.fire('prompt.submit', { text: '/goal ship the site' })
await a.fire('tool.call', { tool: 'TodoWrite', input: { todos: [{ status: 'completed' }, { status: 'pending' }, { status: 'pending' }, { status: 'completed' }] } })
const sp = await a.fire('ui.render', { component: 'Spinner', props: { word: 'Working' } })
assert.match(sp.props.suffix, /goal █████░░░░░ 2\/4/, 'goal bar')

// Collision Guard: A edits, B edits same file soon -> denied; A again -> allowed; later -> allowed
const edit = p => ({ tool: 'Edit', input: { file_path: p } })
assert.ok(!(await a.fire('tool.call', edit('/r/x.md'))).deny, 'first edit allowed')
assert.match((await b.fire('tool.call', edit('/r/x.md'))).deny, /another Claude session edited/, 'B denied')
assert.ok(!(await a.fire('tool.call', edit('/r/x.md'))).deny, 'same session allowed')
b.tick(16 * 60_000)
assert.ok(!(await b.fire('tool.call', edit('/r/x.md'))).deny, 'allowed after window')
console.log('PASS kalpa-mods logic smoke test (fake runtime)')
