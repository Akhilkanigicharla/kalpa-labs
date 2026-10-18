// In-memory stand-in for Supabase REST/RPC/Edge Functions and the Meta Graph API (tests only, no network).
import crypto from "node:crypto";
export function installFake(seed = {}) {
  Object.assign(process.env, { WA_VERIFY_TOKEN: "verify", WA_ACCESS_TOKEN: "x", WA_APP_SECRET: "appsecret", SUPABASE_URL: "https://fake.supabase.co", SUPABASE_SERVICE_ROLE_KEY: "k" });
  const store = { technicians: [], customers: [], job_cards: [], invoices: [], bot_sessions: [], wa_processed: [], usage_minutes: [], invoice_counters: [], amc_contracts: [], ...seed };
  const fx = { store, sent: [], media: [], nextVoice: null, transcribeDown: false };
  const ok = (data) => ({ ok: true, status: 200, text: async () => (data === undefined ? "" : JSON.stringify(data)), json: async () => data, arrayBuffer: async () => new ArrayBuffer(8) });
  const fail = (status) => ({ ok: false, status, text: async () => "{}", json: async () => ({}) });
  globalThis.fetch = async (url, opts = {}) => {
    const u = new URL(url); const method = opts.method || "GET";
    if (u.hostname === "graph.facebook.com") {
      const path = u.pathname.replace(/^\/v[\d.]+\//, "");
      if (/\/media$/.test(path)) { const f = opts.body; const file = f.get("file"); fx.media.push({ type: f.get("type"), name: file.name, bytes: Buffer.from(await file.arrayBuffer()) }); return ok({ id: "MEDIA" + fx.media.length }); }
      if (/\/messages$/.test(path)) { fx.sent.push(JSON.parse(opts.body)); return ok({ messages: [{ id: "out" }] }); }
      return ok({ url: `https://lookaside.fbsbx.com/${path}`, mime_type: "audio/ogg" }); // media metadata
    }
    if (u.hostname === "lookaside.fbsbx.com") return ok();
    if (u.pathname === "/functions/v1/transcribe-extract") {
      if (fx.transcribeDown) return fail(503);
      const b = JSON.parse(opts.body); fx.lastTranscribe = b;
      return ok(fx.nextVoice || { text: "", seconds: 0 }); // the test sets what the note "said"
    }
    if (u.pathname === "/rest/v1/rpc/next_invoice_no_for") { const p = JSON.parse(opts.body); const [y, m] = p.p_date.split("-").map(Number); const s0 = m < 4 ? y - 1 : y;
      const fy = `${String(s0).slice(2)}-${String(s0 + 1).slice(2)}`; let c = store.invoice_counters.find((x) => x.technician_id === p.p_tech && x.fy === fy);
      if (!c) store.invoice_counters.push((c = { technician_id: p.p_tech, fy, last_seq: 0 })); c.last_seq++; return ok(`JC/${fy}/${String(c.last_seq).padStart(4, "0")}`); }
    if (u.pathname === "/rest/v1/rpc/add_usage") { const p = JSON.parse(opts.body); const month = new Date(Date.now() + 330 * 60000).toISOString().slice(0, 8) + "01";
      let r = store.usage_minutes.find((x) => x.technician_id === p.p_tech && x.month === month); if (!r) store.usage_minutes.push((r = { technician_id: p.p_tech, month, seconds: 0 })); r.seconds += p.p_seconds; return ok(r.seconds); }
    const table = u.pathname.split("/").pop(); const rows = store[table]; if (!rows) return fail(404);
    const filt = (list) => { for (const [k, v] of u.searchParams) {
      if (v.startsWith("eq.")) list = list.filter((r) => String(r[k]) === decodeURIComponent(v.slice(3)));
      if (v.startsWith("lte.")) list = list.filter((r) => r[k] != null && String(r[k]) <= v.slice(4));
      if (v.startsWith("gte.")) list = list.filter((r) => r[k] != null && String(r[k]) >= v.slice(4));
      if (v.startsWith("in.(")) { const set = v.slice(4, -1).split(","); list = list.filter((r) => set.includes(String(r[k]))); } }
      return list; };
    if (method === "GET") return ok(filt(rows));
    if (method === "PATCH") { const b = JSON.parse(opts.body); const hit = filt(rows); hit.forEach((r) => Object.assign(r, b)); return ok(hit); }
    const prefer = (opts.headers || {}).Prefer || ""; const keys = (u.searchParams.get("on_conflict") || "").split(",").filter(Boolean); const out = [];
    for (const row of [].concat(JSON.parse(opts.body))) {
      const i = keys.length ? rows.findIndex((r) => keys.every((k) => r[k] === row[k])) : -1;
      if (i >= 0 && /ignore-duplicates/.test(prefer)) continue;
      if (i >= 0) { rows[i] = { ...rows[i], ...row }; out.push(rows[i]); }
      else { const r = { id: crypto.randomUUID(), ...row }; rows.push(r); out.push(r); }
    }
    return ok(/return=representation/.test(prefer) ? out : undefined);
  };
  return fx;
}
export const sign = (body, secret = "appsecret") => "sha256=" + crypto.createHmac("sha256", secret).update(body).digest("hex");
