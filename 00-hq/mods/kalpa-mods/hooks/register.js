// Kalpa mods (UNTESTED until a laptop session: load with `claude --plugin-dir 00-hq/mods/kalpa-mods`).
// Ideas from Nate Herk's short (8 Nov 2026); code is ours. Uses only documented events and $ calls:
// turn.start, turn.complete, prompt.submit, tool.call, ui.render(Spinner), $.ui.toast, $.store, $.session.usage, $.clock.now.
// No $.http, no $.model, no $.process, no $.env: nothing leaves the machine and no secret is read.

const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit'])
let lastTurnEnd = 0          // Cache Keeper: when the last answer finished (ms)
let goal = null              // Goal Meter: { startedAt, total, done }
let sessionId = 'session'

const mins = ms => Math.max(0, Math.round(ms / 60000))
const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

export function register(on, options) {
  const ttl = (Number(options?.cacheTtlSeconds) || 300) * 1000
  const window = (Number(options?.collisionMinutes) || 15) * 60000

  on('session.start', async ($, e, next) => {
    try { sessionId = String(typeof $.session.id === 'function' ? await $.session.id() : $.session.id) } catch {}
    return next(e)
  })

  // ---- Cache Keeper -------------------------------------------------------------
  on('turn.complete', async ($, e, next) => {
    lastTurnEnd = $.clock.now()
    const r = await next(e)
    if (goal) goal = null
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    const now = $.clock.now()
    if (lastTurnEnd && now - lastTurnEnd > ttl) {
      let tokens = ''
      try { const u = await $.session.usage(); if (u?.context?.tokens) tokens = ` (~${Math.round(u.context.tokens / 1000)}k tokens re-read)` } catch {}
      $.ui.toast(`Cache Keeper: cache went cold ${mins(now - lastTurnEnd - ttl)} min ago, so this message costs more${tokens}. Next time reply within ${fmt(ttl / 1000)}.`)
    }
    // ---- Goal Meter: a /goal prompt starts a meter ----
    if (/^\s*\/goal\b/i.test(e.text || '')) goal = { startedAt: now, total: 0, done: 0 }
    return next(e)
  })

  // ---- Goal Meter: count the task list Claude builds while a goal runs ------------
  on('tool.call', async ($, e, next) => {
    const name = e.tool || e.name || ''
    if (goal) {
      if (name === 'TaskCreate') goal.total += 1
      if (name === 'TaskUpdate' && /completed/.test(JSON.stringify(e.input || {}))) goal.done += 1
      if (name === 'TodoWrite' && Array.isArray(e.input?.todos)) {
        goal.total = e.input.todos.length
        goal.done = e.input.todos.filter(t => t.status === 'completed').length
      }
      $.ui.invalidate('ui.render')
    }

    // ---- Collision Guard: another session edited this file recently ------------------
    if (EDIT_TOOLS.has(name)) {
      const path = e.input?.file_path || e.input?.notebook_path
      if (path) {
        const key = 'edits'
        const edits = (await $.store.get(key)) || {}
        const last = edits[path]
        const now = $.clock.now()
        if (last && last.session !== sessionId && now - last.at < window) {
          return { deny: `Collision Guard: another Claude session edited ${path} ${mins(now - last.at)} min ago. Ask the user before changing it, or pull their changes first.` }
        }
        edits[path] = { session: sessionId, at: now }
        for (const [p, v] of Object.entries(edits)) if (now - v.at > 24 * 3600000) delete edits[p]
        await $.store.set(key, edits)
      }
    }
    return next(e)
  })

  on('ui.render', { component: 'Spinner' }, async ($, e, next) => {
    if (!goal) return next(e)
    const pct = goal.total ? Math.round((100 * goal.done) / goal.total) : 0
    const bar = '█'.repeat(Math.round(pct / 10)) + '░'.repeat(10 - Math.round(pct / 10))
    return next({ ...e, props: { ...e.props, suffix: ` · goal ${bar} ${goal.done}/${goal.total} · ${mins($.clock.now() - goal.startedAt)} min…` } })
  })
}
