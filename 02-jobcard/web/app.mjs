// "My customers" PWA (b2.q15): phone-OTP sign-in, due services with wa.me reminders, customers, bills, record.
import config from "./config.js";
import { parseTranscript } from "./vendor/parse.mjs";
import { createApi, demoData, filterCustomers, istToday, normPhone, rupees, views } from "./logic.mjs";
import { pickLang, t } from "./i18n.mjs";

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = (() => { try { localStorage.setItem("jc.t", "1"); localStorage.removeItem("jc.t"); return localStorage; } catch { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), removeItem: (k) => m.delete(k) }; } })();
const params = new URLSearchParams(location.search);
let lang = params.get("lang") || store.getItem("jc.lang") || pickLang(navigator.language);
const api = config.demo ? null : createApi({ url: config.supabaseUrl, anonKey: config.anonKey, store });
let data = null; let tab = params.get("tab") || "due"; let query = "";
const L = (k, v) => t(lang, k, v);
const nice = (iso) => new Date(iso + "T00:00:00Z").toLocaleDateString(lang === "en" ? "en-IN" : `${lang}-IN`, { day: "numeric", month: "short", timeZone: "UTC" });

function chrome() {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll("[data-t]")) el.textContent = L(el.dataset.t);
  for (const b of document.querySelectorAll(".tabs button")) { if (b.dataset.tab === tab) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current"); }
  const banner = $("#banner");
  const msg = config.demo ? L("demo") : !navigator.onLine ? L("offline") : "";
  banner.hidden = !msg; banner.textContent = msg;
}

function signInView(step = "phone", phone = "", err = "") {
  $("#tabs").hidden = true; $("#signout").hidden = true;
  $("#main").innerHTML = `<section class="card" style="margin-top:16px"><h2 style="margin-top:0">${esc(L("signIn"))}</h2>
    <form id="f" novalidate>
      ${step === "phone"
        ? `<label class="field"><span>${esc(L("phone"))}</span><input id="ph" type="tel" inputmode="numeric" autocomplete="tel-national" enterkeyhint="send" placeholder="90000 00000" value="${esc(phone)}" required></label>
           <button class="btn" style="width:100%">${esc(L("sendCode"))}</button>`
        : `<label class="field"><span>${esc(L("code"))}</span><input id="code" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" enterkeyhint="done" required></label>
           <button class="btn" style="width:100%">${esc(L("verify"))}</button>`}
      <p class="err" id="err">${esc(err)}</p></form></section>`;
  $("#f").addEventListener("submit", async (e) => {
    e.preventDefault(); const btn = $("#f button"); btn.disabled = true;
    try {
      if (step === "phone") { const p = normPhone($("#ph").value); if (!p) throw new Error(L("badPhone")); await api.sendOtp(p); return signInView("code", p); }
      await api.verifyOtp(phone, $("#code").value); await start();
    } catch (x) { btn.disabled = false; $("#err").textContent = x.message || L("error"); }
  });
}

function dueView(v) {
  const amc = v.amc.length ? `<h2>${esc(L("amc"))}</h2><ul class="list">${v.amc.map((a) => `<li class="card row"><div><p class="name">${esc(a.customer.name)}</p><p class="meta">${esc(a.customer.area || "")}</p></div><span class="tag">${esc(nice(a.ends_on))}</span></li>`).join("")}</ul>` : "";
  return `<h2>${esc(L("due"))} · ${v.due.length}</h2>
    ${v.due.length ? `<ul class="list">${v.due.map((d) => `<li class="card">
      <div class="row"><div><p class="name">${esc(d.name)}</p><p class="meta">${esc(d.area)} · ${esc(d.phone)}</p></div>
      <span class="tag ${d.overdue ? "late" : ""}">${esc(d.overdue ? L("overdue") : L("dueOn"))} ${esc(nice(d.due))}</span></div>
      <div class="actions"><a class="btn wa" href="${esc(d.wa)}" target="_blank" rel="noopener">${esc(L("remind"))}</a><a class="btn line" href="tel:+91${esc(d.phone)}">${esc(L("call"))}</a></div></li>`).join("")}</ul>`
    : `<p class="card meta">${esc(L("none"))}</p>`}
    ${v.notOpted ? `<p class="meta" style="margin-top:8px">${esc(L("notOpted", { n: v.notOpted }))}</p>` : ""}${amc}`;
}

function customersView(v) {
  const list = filterCustomers(v.customers, query);
  return `<label class="field" style="margin-top:16px"><input id="q" type="search" enterkeyhint="search" placeholder="${esc(L("search"))}" value="${esc(query)}" aria-label="${esc(L("search"))}"></label>
    <ul class="list">${list.map((c) => `<li class="card"><div class="row"><div><p class="name">${esc(c.name)}</p><p class="meta">${esc(c.area || "")}${c.phone ? " · " + esc(c.phone) : ""}</p></div>
      <div style="text-align:right"><p class="num">${esc(rupees(c.spentPaise))}</p><p class="meta">${c.lastVisit ? esc(nice(c.lastVisit)) : ""}</p></div></div>
      ${c.phone ? `<label class="tick"><input type="checkbox" data-opt="${esc(c.id)}" ${c.opted_in_whatsapp ? "checked" : ""}>${esc(L("optIn"))}</label>` : ""}</li>`).join("")}</ul>`;
}

function billsView(v) {
  return `<section class="card stat" style="margin-top:16px"><span>${esc(L("unpaid"))}</span><span class="num">${esc(rupees(v.unpaidPaise))}</span></section>
    <h2>${esc(L("bills"))} · ${v.bills.length}</h2><ul class="list">${v.bills.map((b) => `<li class="card row"><div><p class="name">${esc(b.customer)}</p><p class="meta">${esc(b.number)} · ${esc(nice(b.issued_on))}</p></div>
      <div style="text-align:right"><p class="num">${esc(rupees(b.payable_paise))}</p><span class="tag ${b.paid ? "ok" : "late"}">${esc(b.paid ? L("paid") : L("notPaid"))}</span></div></li>`).join("")}</ul>`;
}

let rec = null;
function recordView(v) {
  return `<button class="mic ${rec ? "on" : ""}" id="mic" aria-label="${esc(rec ? L("stop") : L("hold"))}">${rec ? "■" : "●"}</button>
    <p class="center" style="font-weight:700">${esc(rec ? L("stop") : L("hold"))}</p>
    <p class="center meta">${esc(L("minutes", { used: Math.round(v.quota.usedSeconds / 60), limit: v.quota.limitSeconds / 60 }))}</p>
    <div id="heard"></div>`;
}

function showCard(text) {
  const c = parseTranscript(text); const sum = c.parts.reduce((s, p) => s + (p.rate || 0), 0);
  $("#heard").innerHTML = `<section class="card"><h2 style="margin-top:0">${esc(L("heard"))}</h2><p class="meta">${esc(text)}</p>
    <ul class="list" style="margin-top:8px">${c.parts.map((p) => `<li class="row"><span>${esc(p.desc)}</span><span class="num">${p.rate == null ? "₹ ?" : esc(rupees(p.rate * 100))}</span></li>`).join("")}
    <li class="row"><strong>Total</strong><span class="num">${esc(rupees(sum * 100))}</span></li></ul></section>`;
}

async function toggleRecord() {
  if (rec) { rec.stop(); return; }
  if (!navigator.mediaDevices || !window.MediaRecorder) { $("#heard").innerHTML = `<p class="err">${esc(L("noMic"))}</p>`; return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const chunks = [];
    rec = new MediaRecorder(stream); rec.ondataavailable = (e) => chunks.push(e.data);
    const cap = setTimeout(() => rec && rec.stop(), 120000); // 2-minute cap (PLAN §3)
    rec.onstop = async () => {
      clearTimeout(cap); stream.getTracks().forEach((tr) => tr.stop()); const blob = new Blob(chunks, { type: rec.mimeType }); rec = null; render();
      const b64 = await new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1]); r.onerror = no; r.readAsDataURL(blob); });
      try { const out = await api.transcribe(b64, blob.type, lang); showCard(out.text || ""); } catch { $("#heard").innerHTML = `<p class="err">${esc(navigator.onLine ? L("error") : L("offline"))}</p>`; }
    };
    rec.start(); render();
  } catch { rec = null; $("#heard").innerHTML = `<p class="err">${esc(L("noMic"))}</p>`; }
}

function render() {
  chrome(); if (!data) return;
  const v = views(data, istToday(), lang);
  $("#who").textContent = data.tech ? data.tech.business_name || data.tech.name : "";
  $("#tabs").hidden = false; $("#signout").hidden = !!config.demo; $("#signout").textContent = L("signOut");
  $("#main").innerHTML = tab === "customers" ? customersView(v) : tab === "bills" ? billsView(v) : tab === "record" ? recordView(v) : dueView(v);
  const q = $("#q"); if (q) q.addEventListener("input", () => { query = q.value; const pos = q.selectionStart; render(); const n = $("#q"); n.focus(); n.setSelectionRange(pos, pos); });
  for (const box of document.querySelectorAll("[data-opt]")) box.addEventListener("change", async () => {
    const c = data.customers.find((x) => x.id === box.dataset.opt); c.opted_in_whatsapp = box.checked;
    if (api) try { await api.setOptIn(c.id, box.checked); } catch { c.opted_in_whatsapp = !box.checked; box.checked = !box.checked; }
  });
  const mic = $("#mic"); if (mic) mic.addEventListener("click", config.demo ? () => showCard("Split AC gas refill 2500, capacitor 450, customer Sita 9000033333") : toggleRecord);
}

async function start() {
  chrome();
  if (config.demo) { data = demoData(istToday()); return render(); }
  if (!api.signedIn()) return signInView();
  try { data = await api.load(istToday()); if (data.tech && !params.get("lang") && !store.getItem("jc.lang")) lang = data.tech.language || lang; render(); }
  catch (e) { if (e.signedOut) return signInView(); $("#main").innerHTML = `<p class="card err">${esc(L("error"))}</p>`; }
}

$("#tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-tab]"); if (!b) return; tab = b.dataset.tab; history.replaceState(null, "", `?tab=${tab}`); render(); scrollTo(0, 0); });
$("#signout").addEventListener("click", () => { api && api.signOut(); data = null; signInView(); });
addEventListener("online", chrome); addEventListener("offline", chrome);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
start();
