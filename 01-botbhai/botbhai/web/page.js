// BotBhai demo page script (was inline in index.src.html; moved out for a strict CSP, A220).
// build.py writes web/dist/app.js = core/engine.js + setup registrations + this file.
(function(){
"use strict";
const B = window.BotBhai;
const qs = new URLSearchParams(location.search);
// Live owner dashboard link: https://<site>/#token=<dashboard_token>. The part after # never reaches the server or its
// logs; an old ?token= link still works once and is then wiped from the address bar and history.
const LIVE_TOKEN = new URLSearchParams(location.hash.slice(1)).get("token") || qs.get("token");
if (LIVE_TOKEN && history.replaceState) history.replaceState(null, "", location.pathname + location.search.replace(/([?&])token=[^&]*&?/, "$1").replace(/[?&]$/, ""));
const LIVE_CLIENT = qs.get("client");        // live website chat for one client
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (t) => esc(t).replace(/\*([^*\n]+)\*/g, "<b>$1</b>").replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
const now = () => new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
const store = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };

// ---- sample leads so the dashboard opens in a working state (clearly marked)
const SAMPLE = [
  { id: "s1", sample: true, niche: "salon", business: "Glow Studio Unisex Salon", name: "Lakshmi P.", score: "hot", status: "booked", service: "Hair spa", date: "Wed, 14 Oct", slot: "4:00 PM", source: "meta_ads", contact: "+91 98xxx xxx21", updated: Date.now() - 36e5 * 3 },
  { id: "s2", sample: true, niche: "salon", business: "Glow Studio Unisex Salon", name: "Meghana R.", score: "warm", status: "new", service: "", intents: ["prices", "faq"], source: "web", contact: "web visitor", updated: Date.now() - 36e5 * 5 },
  { id: "s3", sample: true, niche: "realestate", business: "Skyline Homes Realty", name: "Anil Reddy", score: "hot", status: "booked", purpose: "Buy", bhk: "3 BHK", budget: "₹1Cr – ₹2Cr", area: "Tellapur", date: "Sun, 18 Oct", slot: "10:00 AM", source: "whatsapp", contact: "+91 99xxx xxx08", updated: Date.now() - 36e5 * 20 },
  { id: "s4", sample: true, niche: "gym", business: "IronPulse Fitness", name: "Sai K.", score: "warm", status: "callback", goal: "Weight loss", source: "voice", contact: "web visitor", updated: Date.now() - 36e5 * 26 },
  { id: "s5", sample: true, niche: "examkits", business: "Vidya Competitive Academy", name: "Ravi T.", score: "hot", status: "quiz_done", service: "TSPSC Group 2", quiz_score: "2/3", source: "whatsapp", contact: "+91 97xxx xxx55", updated: Date.now() - 36e5 * 30 },
];
let leads = (store.get("bf_leads", null) || SAMPLE.slice()).filter((l) => B.NICHES[l.niche]);
let convos = store.get("bf_convos", {});
let niche = store.get("bf_niche", "salon"); if (!B.NICHES[niche]) niche = Object.keys(B.NICHES)[0];
let state = B.newState();
let visitor = "v" + Math.random().toString(36).slice(2, 10);
let speak = false;
let lang = store.get("bf_lang", "en-IN");

// ---- niche switcher
const nicheBox = $("#niches"), fN = $("#f-niche");
Object.values(B.NICHES).forEach((n) => {
  const b = document.createElement("button"); b.className = "niche"; b.dataset.id = n.id; b.textContent = `${n.emoji} ${n.label}`;
  b.onclick = () => setNiche(n.id); nicheBox.appendChild(b);
  const o = document.createElement("option"); o.value = n.id; o.textContent = n.label; fN.appendChild(o);
});
function setNiche(id) {
  niche = id; store.set("bf_niche", id); state = B.newState(); visitor = "v" + Math.random().toString(36).slice(2, 10);
  const n = B.NICHES[id];
  nicheBox.querySelectorAll(".niche").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.id === id)));
  $("#avatar").textContent = n.business.split(/\s+/).filter((w) => /^\p{L}/u.test(w)).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  $("#bizname").textContent = n.business;
  $("#msgs").innerHTML = ""; $("#quick").innerHTML = "";
  welcome(n);
  if (LIVE_CLIENT) quickWords(["Book", "Prices", "Timings", "Talk to a person"]); // live site: nothing reaches the server until the customer speaks
  else send("hi", null, null, true); // demo: the real greeting + menu from the engine, without a fake customer bubble
  renderEmbed(); renderCards();
}
const CARD_SETS = { salon: ["booking_confirmed", "day_before", "two_hours", "after_visit", "winback", "festival"], gym: ["booking_confirmed", "day_before", "two_hours", "after_visit", "renew_7", "winback"], realestate: ["booking_confirmed", "day_before", "after_visit", "winback", "festival"], examkits: ["booking_confirmed", "daily_question", "day_before", "after_visit", "renew_7"] };
const CARD_WHEN = { booking_confirmed: "Right after booking", day_before: "Day before", two_hours: "2 hours before", after_visit: "Day after the visit", winback: "Lapsed customer", festival: "Festival week", renew_7: "7 days before renewal / fee", daily_question: "Daily 7 AM question" };
function renderCards() {
  const g = document.getElementById("cardgrid"); if (!g) return;
  g.innerHTML = (CARD_SETS[niche] || []).map((k) => `<figure><img loading="lazy" src="cards/demo/${niche}-${k}.png" alt="${esc(CARD_WHEN[k])} card"><figcaption>${esc(CARD_WHEN[k])}</figcaption></figure>`).join("");
}

// ---- chat rendering
function welcome(n) { // a business card first, so the customer knows who they're talking to before typing anything
  const d = document.createElement("div"); d.className = "b in welcome";
  d.innerHTML = `<span class="biz">${esc(n.business)}</span>AI assistant: book, check prices and timings, any time. A person takes over whenever you ask.` +
    `<span class="facts">${n.hours ? `<span>Open: ${esc(n.hours)}</span>` : ""}${n.address ? `<span>${esc(n.address)}</span>` : ""}</span>`;
  $("#msgs").appendChild(d);
}
// "Reply with a number" lists are shown as tap buttons instead, so the bubble keeps only the words
const tidy = (text, options) => (options && options.length ? String(text).replace(/\n?(How can I help\? )?Reply with a number:?/gi, "").replace(/^\s*\*?\d+\.\*?\s.*$/gm, "").replace(/\n{3,}/g, "\n\n").trim() : text);
function quick(options) {
  const q = $("#quick"); q.innerHTML = "";
  (options || []).forEach((label, i) => { const b = document.createElement("button"); b.type = "button"; b.textContent = label; b.onclick = () => send(String(i + 1), label); q.appendChild(b); });
}
function quickWords(words) { // first tap sends the word itself (the engine understands "book", "prices", …)
  const q = $("#quick"); q.innerHTML = "";
  words.forEach((w) => { const b = document.createElement("button"); b.type = "button"; b.textContent = w; b.onclick = () => send(w); q.appendChild(b); });
}
function bubble(dir, text, options) {
  const m = $("#msgs"); const body = tidy(text, options);
  if (body) { const d = document.createElement("div"); d.className = "b " + dir; d.innerHTML = fmt(body) + `<time>${now()}${dir === "out" ? " ✓✓" : ""}</time>`; m.appendChild(d); }
  if (dir === "out") quick([]); else if (options && options.length) quick(options);
  m.scrollTop = m.scrollHeight;
}
function typing(on) {
  const m = $("#msgs"); m.querySelectorAll(".typing").forEach((t) => t.remove());
  if (on) { const t = document.createElement("div"); t.className = "typing"; t.setAttribute("aria-label", "typing"); t.innerHTML = "<i></i><i></i><i></i>"; m.appendChild(t); m.scrollTop = m.scrollHeight; }
}
// ---- Cloudflare Turnstile (A50): the script loads only when the server asks for a check before saving a booking
let tsLoad = null;
function loadTurnstile() {
  return tsLoad || (tsLoad = new Promise((ok, no) => {
    const s = document.createElement("script"); s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"; s.async = true;
    s.onload = () => (window.turnstile ? ok(window.turnstile) : no(new Error("turnstile"))); s.onerror = () => { tsLoad = null; no(new Error("turnstile")); };
    document.head.appendChild(s);
  }));
}
async function humanCheck(sitekey, text, shown) {
  const m = $("#msgs"); m.querySelectorAll(".ts").forEach((x) => x.remove());
  const box = document.createElement("div"); box.className = "ts"; m.appendChild(box); m.scrollTop = m.scrollHeight;
  const dark = (document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
  try {
    (await loadTurnstile()).render(box, { sitekey, action: "booking", theme: dark ? "dark" : "light", size: "flexible",
      callback: (token) => { box.remove(); send(text, shown, token); } }); // resend the same message: the server replays the same booking
    m.scrollTop = m.scrollHeight;
  } catch (e) { box.remove(); bubble("in", "The robot check didn't load. Please message us on WhatsApp to book."); }
}
async function send(text, shown, turnstile, silent) {
  if (!text.trim()) return;
  if (!turnstile && !silent) bubble("out", shown || text);
  let replies, check;
  if (LIVE_CLIENT) {
    try {
      const r = await fetch("/.netlify/functions/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ client: LIVE_CLIENT, visitor, text, source: speak ? "voice" : "web", turnstile, lang: lang.slice(0, 2) }) });
      const j = await r.json(); replies = j.replies || []; check = j.check && j.check.sitekey ? j.check : null;
    } catch (e) { replies = [{ text: "Connection problem. Please try again in a moment." }]; }
  } else {
    const out = B.createBot(niche).handle(state, text, { contact: "demo visitor", source: speak ? "voice" : "web", lang: lang.slice(0, 2) });
    state = out.state; replies = out.replies;
    if (!silent) { logConvo(text, out); saveLead(out.lead); }
  }
  $("#status").textContent = "typing…";
  for (const r of replies) { typing(true); await new Promise((ok) => setTimeout(ok, silent ? 150 : 550)); typing(false); bubble("in", r.text, r.options); }
  $("#status").textContent = "AI assistant · replies in seconds";
  if (check) humanCheck(check.sitekey, text, shown);
  if (speak && replies.length) say(replies.map((r) => r.text).join(". "));
}
$("#compose").addEventListener("submit", (e) => { e.preventDefault(); const t = $("#text"); send(t.value); t.value = ""; });

// ---- leads
function saveLead(l) {
  if (!l || l.turns < 2) return; // ignore one-word drive-bys
  const id = niche + ":" + visitor; const i = leads.findIndex((x) => x.id === id);
  const row = Object.assign({}, l, { id, contact: "demo visitor", updated: Date.now() });
    if (l.name == null && i >= 0) row.name = leads[i].name;
  if (i >= 0) leads[i] = row; else leads.unshift(row);
  store.set("bf_leads", leads); renderLeads();
  if (i < 0) toast("New lead in the dashboard →");
}
function logConvo(text, out) {
  const id = niche + ":" + visitor; const c = convos[id] || (convos[id] = { niche, business: B.NICHES[niche].business, msgs: [] });
  c.msgs.push({ d: "in", t: text }); out.replies.forEach((r) => c.msgs.push({ d: "out", t: r.text }));
  if (out.events.some((e) => e.type === "unanswered")) c.unanswered = (c.unanswered || 0) + 1;
  c.msgs = c.msgs.slice(-40); store.set("bf_convos", convos); renderConvos();
}
function wants(l) { return [l.service, l.purpose, l.bhk, l.budget, l.area, l.goal, l.quiz_score ? "quiz " + l.quiz_score : "" ].filter(Boolean).concat(!l.service && !l.goal && !l.bhk && l.intents ? l.intents.map((x) => "asked " + x) : []).join(" · ") || "—"; }
function when(l) { return l.date ? `${l.date}${l.slot ? " " + l.slot : ""}` : "—"; }
function ago(t) { const m = Math.round((Date.now() - t) / 6e4); return m < 1 ? "just now" : m < 60 ? m + " min ago" : m < 1440 ? Math.round(m / 60) + " h ago" : Math.round(m / 1440) + " d ago"; }
function filtered() {
  const n = fN.value, s = $("#f-score").value, q = $("#f-q").value.toLowerCase();
  return leads.filter((l) => (!n || l.niche === n) && (!s || l.score === s) && (!q || JSON.stringify(l).toLowerCase().includes(q)));
}
function renderLeads() {
  const list = filtered();
  $("#k-total").textContent = list.length; $("#k-hot").textContent = list.filter((l) => l.score === "hot").length;
  $("#k-booked").textContent = list.filter((l) => l.status === "booked" || l.status === "quiz_done").length; $("#k-call").textContent = list.filter((l) => l.status === "callback").length;
  $("#rows").innerHTML = list.map((l) => `<tr><td><span class="pill ${esc(l.score)}">${esc(l.score)}</span></td><td>${esc(l.name || "Unknown")} ${l.sample ? '<span class="sample">sample</span>' : ""}</td><td>${esc(l.business)}</td><td>${esc(wants(l))}</td><td>${esc(when(l))}</td><td><span class="tag">${esc(l.status)}</span></td><td>${esc(l.source)}</td><td>${l.updated ? ago(l.updated) : "—"}</td></tr>`).join("") || `<tr><td colspan="8">No leads yet. Chat on the phone to create one.</td></tr>`;
}
["#f-niche", "#f-score", "#f-q"].forEach((s) => $(s).addEventListener("input", renderLeads));
function renderConvos() {
  const ids = Object.keys(convos).reverse();
  $("#convo").innerHTML = ids.length ? ids.map((id) => { const c = convos[id]; return `<div class="kpi"><span>${esc(c.business)}${c.unanswered ? ` · <b style="display:inline;font-size:12px;color:var(--hot)">${c.unanswered} unanswered</b>` : ""}</span>${c.msgs.slice(-6).map((m) => `<div style="font-size:13px"><b style="display:inline;font:600 13px var(--f-body)">${m.d === "in" ? "Customer" : "Bot"}:</b> ${esc(m.t.split("\n")[0])}</div>`).join("")}</div>`; }).join("") : '<p class="note">No conversations yet in this browser. Chat on the phone first.</p>';
}

// ---- exports (Excel + CSV)
const COLS = ["name", "business", "niche", "score", "status", "service", "quiz_score", "purpose", "bhk", "budget", "area", "goal", "date", "slot", "source", "contact"];
function tableRows() { return filtered().map((l) => Object.fromEntries(COLS.map((c) => [c, l[c] || ""]).concat([["updated", l.updated ? new Date(l.updated).toLocaleString() : ""], ["sample", l.sample ? "yes" : ""]]))); }
let downloads = null;
if (window.claude && window.claude.use) window.claude.use("downloads").then((d) => { downloads = d; }).catch(() => {});
async function offer(filename, data, mime) {
  if (downloads) { try { await downloads.save({ filename, data }); toast("Saved " + filename); return; } catch (e) { if (e && e.code === "declined") return; } }
  try { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([data], { type: mime })); a.download = filename; document.body.appendChild(a); a.click(); a.remove(); toast("Downloading " + filename); }
  catch (e) { toast("Download blocked here. Use the live dashboard."); }
}
$("#x-xlsx").onclick = () => {
  if (!window.XLSX) return toast("Excel library didn't load. Try CSV.");
  const ws = XLSX.utils.json_to_sheet(tableRows()); ws["!cols"] = COLS.concat(["updated", "sample"]).map((c) => ({ wch: c === "business" ? 26 : c === "name" ? 18 : 12 }));
  const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, "Leads");
  const out = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  offer(`botforge-leads-${new Date().toISOString().slice(0, 10)}.xlsx`, new Uint8Array(out), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
};
$("#x-csv").onclick = () => {
  const rows = tableRows(); const head = Object.keys(rows[0] || { name: "" });
  const csv = "﻿" + [head.join(",")].concat(rows.map((r) => head.map((h) => `"${String(r[h]).replace(/"/g, '""')}"`).join(","))).join("\n");
  offer(`botforge-leads-${new Date().toISOString().slice(0, 10)}.csv`, csv, "text/csv");
};
const resetBtn = $("#x-reset");
resetBtn.onclick = () => {
  if (resetBtn.dataset.armed) { leads = SAMPLE.slice(); convos = {}; store.set("bf_leads", leads); store.set("bf_convos", convos); renderLeads(); renderConvos(); resetBtn.textContent = "Reset demo"; delete resetBtn.dataset.armed; toast("Demo reset"); }
  else { resetBtn.dataset.armed = "1"; resetBtn.textContent = "Tap again to reset"; setTimeout(() => { resetBtn.textContent = "Reset demo"; delete resetBtn.dataset.armed; }, 3000); }
};

// ---- voice agent (free: the browser's own speech engine, no key; Chrome on Android/desktop, Safari on iOS)
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const LANG_NAME = { "en-IN": "English", "te-IN": "Telugu", "hi-IN": "Hindi" };
function setLang(l) {
  lang = l; store.set("bf_lang", l);
  document.querySelectorAll(".langs button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === l)));
  $("#vstatus").textContent = SR ? `Listening in ${LANG_NAME[l]}. Replies come in ${LANG_NAME[l]} and are read aloud.` : "This browser can't listen. Type instead; replies are still read aloud.";
}
const LANG_WORD = { "en-IN": "english", "te-IN": "telugu", "hi-IN": "hindi" }; // A73: the bot switches its replies too
document.querySelectorAll(".langs button").forEach((b) => b.onclick = () => { const was = lang; setLang(b.dataset.lang); if (b.dataset.lang !== was && document.querySelector("#msgs .b.in")) send(LANG_WORD[b.dataset.lang], undefined, undefined, true); });
function voiceFor(l) { // best installed voice for a language; null = the browser default
  const vs = "speechSynthesis" in window ? speechSynthesis.getVoices() : [];
  return vs.find((v) => v.lang === l) || vs.find((v) => v.lang && v.lang.startsWith(l.slice(0, 2))) || null;
}
function say(text) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/\*/g, "").replace(/https?:\/\/\S+/g, "").replace(/\p{Extended_Pictographic}/gu, "").replace(/\s{2,}/g, " "));
  const l = /[\u0C00-\u0C7F]/.test(text) ? "te-IN" : /[\u0900-\u097F]/.test(text) ? "hi-IN" : "en-IN"; // A73: read in the reply's language
  u.lang = l; const v = voiceFor(l); if (v) u.voice = v; u.rate = 1;
  const orb = $("#orb"); u.onstart = () => orb.classList.add("speaking"); u.onend = u.onerror = () => orb.classList.remove("speaking");
  speechSynthesis.speak(u);
}
function setMode(v) {
  speak = v; $("#phone").classList.toggle("voicemode", v); $("#m-voice").setAttribute("aria-pressed", String(v)); $("#m-chat").setAttribute("aria-pressed", String(!v));
  if (v) say(`Hi, this is the ${B.NICHES[niche].business} assistant. How can I help?`); else if ("speechSynthesis" in window) speechSynthesis.cancel();
}
$("#m-voice").onclick = () => setMode(true); $("#m-chat").onclick = () => setMode(false);
function listen(btn, onText) { // one utterance in the chosen language
  if (!SR) { $("#vstatus").textContent = "This browser can't listen. Type instead; replies are still read aloud."; toast("Voice input needs Chrome or Safari"); return; }
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  const rec = new SR(); rec.lang = lang; rec.interimResults = true; rec.maxAlternatives = 1;
  btn.classList.add("live", "listening"); if (btn.id === "orb") $("#orbtxt").textContent = "Listening…";
  rec.onresult = (e) => { const r = e.results[e.results.length - 1]; $("#heard").textContent = r[0].transcript; if (r.isFinal) onText(r[0].transcript); };
  rec.onerror = (e) => { $("#vstatus").textContent = e.error === "not-allowed" || e.error === "service-not-allowed" ? "Allow the microphone for this site, then tap again." : e.error === "language-not-supported" ? `${LANG_NAME[lang]} listening isn't available on this phone. Try English.` : "Didn't catch that. Tap and try again."; };
  rec.onend = () => { btn.classList.remove("live", "listening"); if (btn.id === "orb") $("#orbtxt").textContent = "Tap and speak"; };
  try { rec.start(); } catch (e) { rec.onerror({ error: "not-allowed" }); rec.onend(); }
}
$("#orb").onclick = () => listen($("#orb"), (t) => send(t));
$("#mic").onclick = () => listen($("#mic"), (t) => { $("#heard").textContent = ""; send(t); });
setLang(lang);
if ("speechSynthesis" in window) speechSynthesis.getVoices(); // warm the voice list (it loads async)

// ---- tabs
document.querySelectorAll(".tab").forEach((t) => t.onclick = () => {
  document.querySelectorAll(".tab").forEach((x) => x.setAttribute("aria-selected", String(x === t)));
  document.querySelectorAll(".pane").forEach((p) => { p.hidden = p.dataset.pane !== t.dataset.tab; p.classList.toggle("rise", !p.hidden); });
});

// ---- widget embed code
function renderEmbed() {
  $("#embed").textContent = `<!-- BotBhai chat for ${B.NICHES[niche].business} -->
<script src="https://YOUR-SITE.netlify.app/widget.js"
        data-client="CLIENT-UUID-FROM-SUPABASE" defer><\/script>`;
}
$("#copy-embed").onclick = () => { const t = $("#embed").textContent; (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => toast("Copied"), () => { const r = document.createRange(); r.selectNodeContents($("#embed")); getSelection().removeAllRanges(); getSelection().addRange(r); toast("Selected. Press Ctrl+C"); }); };

function toast(msg) { const d = document.createElement("div"); d.className = "toast"; d.textContent = msg; document.body.appendChild(d); setTimeout(() => d.remove(), 2200); }

// ---- live dashboard mode (deployed site with #token=)
async function loadLive() {
  try {
    const r = await fetch("/.netlify/functions/leads", { headers: { Authorization: "Bearer " + LIVE_TOKEN } }); if (!r.ok) throw new Error("token");
    const d = await r.json();
    leads = d.leads.map((l) => Object.assign({ business: d.client.name, niche: d.client.niche, contact: l.contact, name: l.name, score: l.score, status: l.status, source: l.source, updated: Date.parse(l.updated_at) }, l.details));
    convos = {}; d.messages.slice().reverse().forEach((m) => { const c = convos[m.contact] || (convos[m.contact] = { business: d.client.name, msgs: [] }); c.msgs.push({ d: m.direction === "in" ? "in" : "out", t: m.body || "" }); });
    $("#mode-note").textContent = `Live dashboard for ${d.client.name}. Refreshes every 30 seconds.`;
    renderLeads(); renderConvos();
  } catch (e) { $("#mode-note").textContent = "This dashboard link isn't valid. Ask Kalpa Labs for a new one."; }
}

if (qs.get("embed")) document.body.classList.add("embed");
if (qs.get("niche") && B.NICHES[qs.get("niche")]) niche = qs.get("niche");
setNiche(niche); renderLeads(); renderConvos();
if (LIVE_TOKEN) { loadLive(); setInterval(loadLive, 30000); }
})();
