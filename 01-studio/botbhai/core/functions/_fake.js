// In-memory stand-in for Supabase REST + Meta Graph API, used only by tests.
module.exports = function installFake(seed) {
  Object.assign(process.env, { WA_VERIFY_TOKEN: "verify", WA_ACCESS_TOKEN: "x", WA_APP_SECRET: "appsecret", SUPABASE_URL: "https://fake.supabase.co", SUPABASE_SERVICE_ROLE_KEY: "k" });
  const store = Object.assign({ clients: [], client_secrets: [], sessions: [], leads: [], messages: [], ad_stats: [], members: [], jobs: [], bookings: [] }, seed);
  const graph = { sent: [], calls: [], responses: {} };
  global.fetch = async (url, opts = {}) => {
    const ok = (data) => ({ ok: true, status: 200, text: async () => JSON.stringify(data), json: async () => data });
    if (url.startsWith("https://graph.facebook.com")) {
      const path = url.replace(/^https:\/\/graph\.facebook\.com\/v[\d.]+\//, "");
      graph.calls.push({ path, method: opts.method || "GET", body: opts.body ? JSON.parse(opts.body) : null });
      if (/\/messages$/.test(path)) graph.sent.push(JSON.parse(opts.body));
      const key = Object.keys(graph.responses).find((k) => path.startsWith(k));
      return ok(key ? graph.responses[key] : { success: true });
    }
    const u = new URL(url); const table = u.pathname.split("/").pop(); const method = opts.method || "GET";
    const filt = (rows) => { for (const [k, v] of u.searchParams) {
      if (v.startsWith("eq.")) rows = rows.filter((r) => String(r[k]) === decodeURIComponent(v.slice(3)));
      if (v.startsWith("gte.")) rows = rows.filter((r) => String(r[k]) >= v.slice(4));
      if (v === "not.is.null") rows = rows.filter((r) => r[k] != null); }
      return rows; };
    if (method === "GET") return ok(filt(store[table]));
    if (method === "PATCH") { const b = JSON.parse(opts.body); filt(store[table]).forEach((r) => Object.assign(r, b)); return ok([]); }
    const body = [].concat(JSON.parse(opts.body)); const keys = (u.searchParams.get("on_conflict") || "").split(",").filter(Boolean);
    for (const row of body) { const i = keys.length ? store[table].findIndex((r) => keys.every((k) => r[k] === row[k])) : -1;
      if (i >= 0) store[table][i] = Object.assign(store[table][i], row); else store[table].push(Object.assign({ id: String(store[table].length + 1) }, row)); }
    return ok(body);
  };
  return { store, graph };
};
