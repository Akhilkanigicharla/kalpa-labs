// "My customers" PWA logic, no DOM: Supabase auth (phone OTP) + REST, and the lists. Tested in test/web.test.mjs.
import { dueCustomers, reminderText, waLink } from "./vendor/reminders.mjs";
import { voiceQuota } from "./vendor/quota.mjs";

const DAY = 86400000;
export const istToday = (now = Date.now()) => new Date(now + 330 * 60000).toISOString().slice(0, 10);
export const addDays = (iso, n) => new Date(Date.parse(iso + "T00:00:00Z") + n * DAY).toISOString().slice(0, 10);
export const rupees = (paise) => "₹" + (paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 });

/** "+91 90000 33333", "090000-33333" → "9000033333"; null if not an Indian mobile. */
export function normPhone(s) {
  const d = String(s || "").replace(/\D/g, "").replace(/^(91|0)(?=[6-9]\d{9}$)/, "");
  return /^[6-9]\d{9}$/.test(d) ? d : null;
}

/** Supabase over plain fetch: phone OTP sign-in, token refresh, PostgREST with the user's token (RLS), Edge Function. */
export function createApi({ url, anonKey, fetchFn = fetch, store, now = () => Date.now() }) {
  const KEY = "jobcard.session";
  const read = () => { try { return JSON.parse(store.getItem(KEY) || "null"); } catch { return null; } };
  const write = (s) => { try { s ? store.setItem(KEY, JSON.stringify(s)) : store.removeItem(KEY); } catch { /* private mode: session lasts this tab only */ } };
  let session = read();
  const auth = async (path, body) => {
    const r = await fetchFn(`${url}/auth/v1/${path}`, { method: "POST", headers: { apikey: anonKey, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.msg || j.error_description || j.message || `auth ${r.status}`);
    return j;
  };
  const keep = (j) => { session = { access: j.access_token, refresh: j.refresh_token, exp: now() + (j.expires_in || 3600) * 1000, user: j.user && j.user.id }; write(session); return session; };
  async function token() {
    if (!session) return null;
    if (session.exp - now() < 60000) {
      try { keep(await auth("token?grant_type=refresh_token", { refresh_token: session.refresh })); }
      catch { session = null; write(null); return null; }
    }
    return session.access;
  }
  async function rest(path, { method = "GET", body, prefer } = {}) {
    const t = await token(); if (!t) throw Object.assign(new Error("signed out"), { signedOut: true });
    const r = await fetchFn(`${url}/rest/v1/${path}`, { method, body: body === undefined ? undefined : JSON.stringify(body),
      headers: { apikey: anonKey, Authorization: `Bearer ${t}`, "Content-Type": "application/json", ...(prefer ? { Prefer: prefer } : {}) } });
    if (r.status === 401) { session = null; write(null); throw Object.assign(new Error("signed out"), { signedOut: true }); }
    if (!r.ok) throw new Error(`${method} ${path.split("?")[0]} ${r.status}`);
    const txt = await r.text(); return txt ? JSON.parse(txt) : null;
  }
  return {
    signedIn: () => !!session,
    sendOtp: (phone10) => auth("otp", { phone: `+91${phone10}` }),
    verifyOtp: async (phone10, code) => keep(await auth("verify", { type: "sms", phone: `+91${phone10}`, token: String(code).trim() })),
    signOut: () => { session = null; write(null); },
    rest,
    async load(today) {
      const since = addDays(today, -400);
      const [tech, customers, jobs, invoices, amc, usage] = await Promise.all([
        rest("technicians?select=name,business_name,plan,language&limit=1"),
        rest("customers?select=id,name,phone,area,opted_in_whatsapp&order=name"),
        rest(`job_cards?select=customer_id,next_service,appliance,visited_at&visited_at=gte.${since}`),
        rest("invoices?select=number,issued_on,payable_paise,paid,customer_id&order=issued_on.desc&limit=100"),
        rest("amc_contracts?select=customer_id,ends_on,visits_per_year,price_paise"),
        rest(`usage_minutes?select=seconds&month=eq.${today.slice(0, 8)}01`),
      ]);
      return { tech: tech[0] || null, customers, jobs, invoices, amc, usedSeconds: usage[0] ? usage[0].seconds : 0 };
    },
    setOptIn: (id, on) => rest(`customers?id=eq.${encodeURIComponent(id)}`, { method: "PATCH", body: { opted_in_whatsapp: !!on }, prefer: "return=minimal" }),
    async transcribe(base64, mime, lang) {
      const t = await token(); if (!t) throw Object.assign(new Error("signed out"), { signedOut: true });
      const r = await fetchFn(`${url}/functions/v1/transcribe-extract`, { method: "POST", headers: { Authorization: `Bearer ${t}`, apikey: anonKey, "Content-Type": "application/json" },
        body: JSON.stringify({ audio_base64: base64, mime, lang: `${lang}-IN` }) });
      if (!r.ok) throw new Error(`transcribe ${r.status}`);
      return r.json();
    },
  };
}

/** Everything the four tabs show, from the raw rows. */
export function views(data, today, lang = "te") {
  const byId = new Map(data.customers.map((c) => [c.id, c]));
  const supplier = (data.tech && (data.tech.business_name || data.tech.name)) || "";
  const due = dueCustomers(data.jobs, data.customers, today, { aheadDays: 30, overdueDays: 30, max: 50 }).map((r) => {
    const text = reminderText(r, supplier, lang);
    return { id: r.customer.id, name: r.customer.name, area: r.customer.area || "", phone: r.customer.phone, due: r.job.next_service, overdue: r.job.next_service < today, wa: waLink(r.customer.phone, text), text };
  });
  const notOpted = dueCustomers(data.jobs, data.customers.map((c) => ({ ...c, opted_in_whatsapp: true })), today, { aheadDays: 30, max: 50 })
    .filter((r) => !byId.get(r.customer.id).opted_in_whatsapp).length;
  const amc = data.amc.filter((a) => a.ends_on >= today && a.ends_on <= addDays(today, 30))
    .map((a) => ({ ...a, customer: byId.get(a.customer_id) })).filter((a) => a.customer).sort((a, b) => a.ends_on.localeCompare(b.ends_on));
  const spent = new Map(); const last = new Map();
  for (const i of data.invoices) spent.set(i.customer_id, (spent.get(i.customer_id) || 0) + i.payable_paise);
  for (const j of data.jobs) if (!last.has(j.customer_id) || j.visited_at > last.get(j.customer_id)) last.set(j.customer_id, j.visited_at);
  const customers = data.customers.map((c) => ({ ...c, spentPaise: spent.get(c.id) || 0, lastVisit: last.get(c.id) ? String(last.get(c.id)).slice(0, 10) : null }));
  const bills = data.invoices.map((i) => ({ ...i, customer: (byId.get(i.customer_id) || {}).name || "—" }));
  const unpaidPaise = data.invoices.filter((i) => !i.paid).reduce((s, i) => s + i.payable_paise, 0);
  return { due, notOpted, amc, customers, bills, unpaidPaise, quota: voiceQuota(data.tech ? data.tech.plan : "free", data.usedSeconds) };
}

export function filterCustomers(list, q) {
  const s = String(q || "").trim().toLowerCase(); if (!s) return list;
  const digits = s.replace(/\D/g, "");
  return list.filter((c) => c.name.toLowerCase().includes(s) || (c.area || "").toLowerCase().includes(s) || (digits.length >= 3 && (c.phone || "").includes(digits)));
}

/** Made-up data for the demo page and screenshots (every phone is a 90000 xxxxx number). */
export function demoData(today) {
  const c = (id, name, phone, area, opted = true) => ({ id, name, phone, area, opted_in_whatsapp: opted });
  const customers = [c("c1", "Sita Devi", "9000033333", "Ameerpet"), c("c2", "Ravi Teja", "9000044444", "SR Nagar"), c("c3", "Anjali", "9000055555", "Kukatpally"),
    c("c4", "Lakshmi", "9000066666", "Madhapur", false), c("c5", "Imran Khan", "9000077777", "Tolichowki"), c("c6", "Padma", "9000088888", "Uppal")];
  const j = (customer_id, daysAgo, nextIn, appliance = "split_ac") => ({ customer_id, appliance, visited_at: addDays(today, -daysAgo) + "T10:00:00Z", next_service: nextIn == null ? null : addDays(today, nextIn) });
  const jobs = [j("c1", 178, 2), j("c2", 185, -5, "window_ac"), j("c3", 170, 9), j("c4", 175, 4, "fridge"), j("c5", 12, 170), j("c6", 160, 21)];
  const inv = (n, cid, daysAgo, rs, paid = true) => ({ number: `JC/26-27/${String(n).padStart(4, "0")}`, customer_id: cid, issued_on: addDays(today, -daysAgo), payable_paise: rs * 100, paid });
  const invoices = [inv(6, "c5", 12, 3450, false), inv(5, "c6", 160, 600), inv(4, "c3", 170, 2950), inv(3, "c4", 175, 1800), inv(2, "c1", 178, 2500), inv(1, "c2", 185, 750)];
  const amc = [{ customer_id: "c3", ends_on: addDays(today, 12), visits_per_year: 3, price_paise: 450000 }];
  return { tech: { name: "Ravi", business_name: "Ravi Cooling Services", plan: "pro", language: "te" }, customers, jobs, invoices, amc, usedSeconds: 41 * 60 };
}
