// In-memory stand-in for Supabase REST + Meta Graph API, used only by tests.
module.exports = function installFake(seed) {
  Object.assign(process.env, { WA_VERIFY_TOKEN: "verify", WA_ACCESS_TOKEN: "x", WA_APP_SECRET: "appsecret", SUPABASE_URL: "https://fake.supabase.co", SUPABASE_SERVICE_ROLE_KEY: "k" });
  const store = Object.assign({ clients: [], client_secrets: [], sessions: [], leads: [], messages: [], ad_stats: [], members: [], jobs: [], bookings: [], processed: [] }, seed);
  const graph = { sent: [], calls: [], responses: {} };
  global.fetch = async (url, opts = {}) => {
    const ok = (data) => ({ ok: true, status: 200, text: async () => JSON.stringify(data), json: async () => data });
    if (url.startsWith("https://graph.facebook.com")) {
      const path = url.replace(/^https:\/\/graph\.facebook\.com\/v[\d.]+\//, "");
      const reqBody = opts.body ? JSON.parse(opts.body) : null;
      graph.calls.push({ path, method: opts.method || "GET", body: reqBody });
      if (reqBody && reqBody.type === "text" && graph.failNextTextTo && reqBody.to === graph.failNextTextTo) { // simulate "outside 24 h window"
        graph.failNextTextTo = null; return { ok: false, status: 400, text: async () => "{}", json: async () => ({ error: { code: 131047, message: "Re-engagement message" } }) };
      }
      if (/\/messages$/.test(path)) graph.sent.push(JSON.parse(opts.body));
      const key = Object.keys(graph.responses).find((k) => path.startsWith(k));
      return ok(key ? graph.responses[key] : { success: true });
    }
    const u = new URL(url); const table = u.pathname.split("/").pop(); const method = opts.method || "GET";
    if (u.pathname.endsWith("/rpc/book_slot")) { // same logic as the SQL function
      const p = JSON.parse(opts.body);
      const taken = store.bookings.filter((b) => b.client_id === p.p_client && b.date_iso === p.p_date && b.slot === p.p_slot && b.status === "confirmed" && !(p.p_replaces_date === p.p_date && p.p_replaces_slot === p.p_slot && b.contact === p.p_contact)).length;
      if (taken >= Math.max(p.p_capacity, 1)) return ok(false);
      if (p.p_replaces_date) store.bookings.filter((b) => b.client_id === p.p_client && b.contact === p.p_contact && b.date_iso === p.p_replaces_date && b.slot === p.p_replaces_slot && b.status === "confirmed").forEach((b) => { b.status = "rescheduled"; });
      store.bookings.push({ id: "bk" + (store.bookings.length + 1), client_id: p.p_client, contact: p.p_contact, name: p.p_name, service: p.p_service, date_iso: p.p_date, slot: p.p_slot, status: "confirmed", source: p.p_source });
      return ok(true);
    }
    const get = (r, k) => (k.includes("->>") ? (r[k.split("->>")[0]] || {})[k.split("->>")[1]] : r[k]);
    const filt = (rows) => { for (const [k0, v] of u.searchParams) { const k = k0;
      if (v.startsWith("eq.")) rows = rows.filter((r) => String(get(r, k)) === decodeURIComponent(v.slice(3)));
      if (v.startsWith("gte.")) rows = rows.filter((r) => get(r, k) != null && String(get(r, k)) >= v.slice(4));
      if (v === "not.is.null") rows = rows.filter((r) => get(r, k) != null); }
      return rows; };
    if (method === "GET") return ok(filt(store[table]));
    if (method === "PATCH") { const b = JSON.parse(opts.body); filt(store[table]).forEach((r) => Object.assign(r, b)); return ok([]); }
    const body = [].concat(JSON.parse(opts.body)); const keys = (u.searchParams.get("on_conflict") || "").split(",").filter(Boolean);
    const ignore = /ignore-duplicates/.test((opts.headers || {}).Prefer || ""); const out = [];
    for (const row of body) { const i = keys.length ? store[table].findIndex((r) => keys.every((k) => r[k] === row[k])) : -1;
      if (i >= 0 && ignore) continue;
      if (i >= 0) store[table][i] = Object.assign({}, store[table][i], row); // PostgREST merge-duplicates replaces given columns
      else store[table].push(Object.assign({ id: String(store[table].length + 1) }, row));
      out.push(row); }
    return ok(out);
  };
  return { store, graph };
};
