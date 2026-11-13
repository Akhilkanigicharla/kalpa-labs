// dashboard.html page script (moved out of the page so the CSP can forbid inline scripts; live check 14 Nov 2026).
(function () {
  "use strict";
  var API = "/.netlify/functions/leads", KEY = "botbhai.inbox.key"; // same key as the inbox: one sign-in for both
  var params = new URLSearchParams(location.search), DEMO = params.get("demo") === "1";
  var $ = function (id) { return document.getElementById(id); };
  var store = { get: function () { try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; } },
                set: function (v) { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} } };
  var frag = /(?:^|[#&])key=([a-f0-9-]{36})/i.exec(location.hash);
  if (frag) { store.set(frag[1]); history.replaceState(null, "", location.pathname + location.search); }
  var S = { key: store.get(), data: null, tab: params.get("tab") || "today", filter: "hot", q: "", timer: null };

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) { if (k === "text") n.textContent = attrs[k]; else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), attrs[k]); else if (attrs[k] != null) n.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], DAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  function istIso(ms) { return new Date((ms == null ? Date.now() : ms) + 330 * 60000).toISOString().slice(0, 10); }
  function addDays(iso, n) { return new Date(Date.parse(iso) + n * 864e5).toISOString().slice(0, 10); }
  function nice(iso) { var d = new Date(iso + "T00:00:00Z"); return DAY[d.getUTCDay()] + ", " + d.getUTCDate() + " " + MON[d.getUTCMonth()]; }
  function mins(slot) { var m = /^(\d{1,2}):(\d{2})\s*([AP]M)$/i.exec(slot || ""); if (!m) return 9999; var h = +m[1] % 12 + (/p/i.test(m[3]) ? 12 : 0); return h * 60 + +m[2]; }
  function nowMins() { var d = new Date(Date.now() + 330 * 60000); return d.getUTCHours() * 60 + d.getUTCMinutes(); }
  function phone(c) { var d = String(c || "").replace(/\D/g, ""); return /^91\d{10}$/.test(d) ? "+91 " + d.slice(2, 7) + " " + d.slice(7) : (d ? "+" + d : ""); }
  function ago(iso) { if (!iso) return ""; var s = (Date.now() - Date.parse(iso)) / 1000; if (s < 3600) return Math.max(1, Math.round(s / 60)) + " min ago"; if (s < 86400) return Math.round(s / 3600) + " h ago"; return Math.round(s / 86400) + " d ago"; }
  function toast(m) { var t = $("toast"); t.textContent = m; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { t.hidden = true; }, 3600); }
  var STATUS = { confirmed: ["booked", "Booked"], completed: ["came", "Came"], no_show: ["noshow", "Didn't come"], cancelled: ["cancelled", "Cancelled"], rescheduled: ["cancelled", "Moved"] };
  var LEAD = { new: "New", booked: "Booked", callback: "Call back", quiz_done: "Quiz done", opted_out: "Said STOP", won: "Won", lost: "Lost", cancelled: "Cancelled" };
  var SRC = { whatsapp: "WhatsApp", web: "Website", voice: "Voice", meta_ads: "Facebook ad" };
  function statusOf(b) { if (b.status === "confirmed" && b.confirmed_at) return ["sure", "Confirmed"]; return STATUS[b.status] || ["came", b.status]; }

  // ---------- data
  function load() {
    var p = DEMO ? Promise.resolve({ status: 200, data: Demo() }) :
      fetch(API, { headers: { Authorization: "Bearer " + S.key } }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { status: r.status, data: d }; }); });
    return p.then(function (r) {
      if (r.status === 401) { store.set(""); S.key = ""; return showSignin("That key didn't work. Check it and paste again."); }
      if (r.status !== 200) return toast("Couldn't load. Retrying soon.");
      S.data = r.data; render();
    }, function () { toast(S.data ? "You're offline: showing the last data." : "You're offline. Retrying soon."); });
  }

  // ---------- render
  function render() {
    var d = S.data, today = d.today || istIso();
    $("biz").textContent = (d.client && d.client.name) || "Your salon"; if (DEMO) $("biz").appendChild(el("span", { class: "demo-flag", text: "Demo" }));
    $("today-label").textContent = nice(today) + " · updated " + new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" });
    var w = $("waiting"); w.hidden = !d.waiting; w.textContent = d.waiting || "";
    $("inbox-tab").href = "inbox.html" + (DEMO ? "?demo=1" : "");
    var todays = (d.bookings || []).filter(function (b) { return b.date_iso === today; }).sort(function (a, b) { return mins(a.slot) - mins(b.slot); });
    var live = todays.filter(function (b) { return b.status !== "cancelled" && b.status !== "rescheduled"; });
    var sure = live.filter(function (b) { return b.confirmed_at || b.status === "completed"; }).length;
    var k = $("kpis"); k.textContent = "";
    [[live.length, "Bookings today", function () { $("timeline").scrollIntoView({ behavior: "smooth" }); }, false],
     [sure, "Confirmed", function () { $("timeline").scrollIntoView({ behavior: "smooth" }); }, false],
     [d.waiting || 0, "Need you", function () { location.href = $("inbox-tab").href; }, !!d.waiting]].forEach(function (x) {
      k.appendChild(el("button", { class: "kpi" + (x[3] ? " alert" : ""), onclick: x[2] }, [el("b", { text: String(x[0]) }), el("span", { text: x[1] })]));
    });
    var tl = $("timeline"); tl.textContent = "";
    if (!todays.length) tl.appendChild(el("li", { class: "empty", text: "No bookings today yet. Share your WhatsApp link on Instagram and Google so customers can book." }));
    var nm = nowMins();
    todays.forEach(function (b) {
      var st = statusOf(b), m = mins(b.slot), cls = "slot" + (m + 45 < nm ? " past" : m <= nm && nm < m + 45 ? " now" : "");
      tl.appendChild(el("li", { class: cls }, [el("time", { text: b.slot }), el("div", { style: "min-width:0" }, [el("div", { class: "who", text: b.name || phone(b.contact) || "Customer" }), el("div", { class: "what", text: (b.service || "Visit") + (b.name && b.contact && b.contact.indexOf("web:") !== 0 ? " · " + phone(b.contact) : "") })]), el("span", { class: "pill " + st[0], text: st[1] })]));
    });
    var tom = (d.bookings || []).filter(function (b) { return b.date_iso === addDays(today, 1) && b.status === "confirmed"; }).length;
    $("tomorrow").textContent = tom ? "Tomorrow: " + tom : "";
    renderLeads(); renderReport(today); show(S.tab);
  }
  function renderLeads() {
    var ul = $("leads"); ul.textContent = "";
    var q = S.q.trim().toLowerCase();
    var rows = (S.data.leads || []).filter(function (l) {
      var f = S.filter === "all" || (S.filter === "hot" && l.score === "hot") || l.status === S.filter;
      var hay = [l.name, l.contact, l.details && (l.details.service || l.details.goal)].join(" ").toLowerCase();
      return f && (!q || hay.indexOf(q) >= 0);
    }).slice(0, 100);
    if (!rows.length) { ul.appendChild(el("li", { class: "empty", text: q ? "No lead matches that search." : "No leads here yet." })); return; }
    rows.forEach(function (l) {
      var dt = l.details || {}, tel = phone(l.contact), web = String(l.contact || "").indexOf("web:") === 0;
      ul.appendChild(el("li", { class: "lead" }, [
        el("div", { class: "top" }, [el("b", { text: l.name || dt.customer_name || (web ? "Website visitor" : tel) }), el("span", { class: "pill " + (l.score || "cold"), text: l.score || "cold" })]),
        el("div", { class: "muted small", text: [dt.service || dt.goal, dt.date ? dt.date + (dt.slot ? " " + dt.slot : "") : "", LEAD[l.status] || l.status, SRC[l.source] || l.source].filter(Boolean).join(" · ") }),
        el("div", { class: "row" }, [web ? el("span", { class: "muted small", text: "Website chat" }) : el("a", { class: "tel", href: "tel:" + tel.replace(/\s/g, ""), text: tel }), el("span", { class: "muted small", text: ago(l.updated_at) })]),
      ]));
    });
  }
  function renderReport(today) {
    var from = addDays(today, -30), bs = (S.data.bookings || []).filter(function (b) { return b.date_iso >= from && b.date_iso <= today; });
    var n = function (s) { return bs.filter(function (b) { return b.status === s; }).length; };
    var came = n("completed"), no = n("no_show"), marked = came + no;
    var st = $("stats"); st.textContent = "";
    [[bs.filter(function (b) { return b.status !== "rescheduled"; }).length, "Bookings"], [came, "Came"], [no, "Didn't come"], [marked ? Math.round(no / marked * 100) + "%" : "–", "No-show rate"]].forEach(function (x) {
      st.appendChild(el("div", { class: "kpi", style: "cursor:default" }, [el("b", { text: String(x[0]) }), el("span", { text: x[1] })]));
    });
    var bars = $("bars"); bars.textContent = ""; var days = [], max = 1;
    for (var i = 13; i >= 0; i--) { var iso = addDays(today, -i), c = (S.data.bookings || []).filter(function (b) { return b.date_iso === iso && b.status !== "cancelled" && b.status !== "rescheduled"; }).length; days.push([iso, c]); max = Math.max(max, c); }
    days.forEach(function (x) { bars.appendChild(el("div", { class: "bar" + (x[0] === today ? " today" : ""), title: nice(x[0]) + ": " + x[1] }, [el("i", { style: "height:" + Math.max(2, Math.round(x[1] / max * 88)) + "px" }), el("span", { text: String(+x[0].slice(8)) })])); });
    bars.setAttribute("aria-label", "Bookings per day for the last 14 days: " + days.map(function (x) { return nice(x[0]) + " " + x[1]; }).join(", "));
    var src = {}; (S.data.leads || []).forEach(function (l) { src[l.source || "whatsapp"] = (src[l.source || "whatsapp"] || 0) + 1; });
    $("sources").textContent = "Where leads came from: " + Object.keys(src).map(function (k) { return (SRC[k] || k) + " " + src[k]; }).join(" · ");
  }
  function show(tab) {
    S.tab = tab;
    ["today", "leads", "report"].forEach(function (t) { $("pane-" + t).hidden = t !== tab; });
    Array.prototype.forEach.call(document.querySelectorAll(".tab[data-tab]"), function (b) { b.setAttribute("aria-selected", String(b.getAttribute("data-tab") === tab)); });
  }

  // ---------- Excel download (CSV with BOM so Excel reads Telugu and ₹; cells that start with = + - @ are neutralised)
  function csv(rows) { return "﻿" + rows.map(function (r) { return r.map(function (v) { v = v == null ? "" : String(v); if (/^[=+\-@\t\r]/.test(v)) v = "'" + v; return '"' + v.replace(/"/g, '""') + '"'; }).join(","); }).join("\r\n"); }
  function download(name, rows) { var a = el("a", { href: URL.createObjectURL(new Blob([csv(rows)], { type: "text/csv;charset=utf-8" })), download: name }); document.body.appendChild(a); a.click(); a.remove(); }
  $("dl-leads").addEventListener("click", function () {
    download("botbhai-leads-" + istIso() + ".csv", [["Name", "Phone", "Score", "Status", "Service", "Date", "Slot", "Source", "Updated"]].concat((S.data.leads || []).map(function (l) { var d = l.details || {}; return [l.name || d.customer_name, phone(l.contact), l.score, l.status, d.service || d.goal, d.date, d.slot, l.source, l.updated_at]; })));
  });
  $("dl-bookings").addEventListener("click", function () {
    download("botbhai-bookings-" + istIso() + ".csv", [["Date", "Time", "Name", "Phone", "Service", "Status"]].concat((S.data.bookings || []).map(function (b) { return [b.date_iso, b.slot, b.name, phone(b.contact), b.service, statusOf(b)[1]]; })));
  });

  Array.prototype.forEach.call(document.querySelectorAll(".tab[data-tab]"), function (b) { b.addEventListener("click", function () { show(b.getAttribute("data-tab")); }); });
  Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (b) {
    b.addEventListener("click", function () { S.filter = b.getAttribute("data-f"); Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (x) { x.setAttribute("aria-pressed", String(x === b)); }); renderLeads(); });
  });
  $("q").addEventListener("input", function (e) { clearTimeout(S.qt); S.qt = setTimeout(function () { S.q = e.target.value; renderLeads(); }, 250); });  // wait for a pause in typing
  function showSignin(err) { $("signin").hidden = false; $("main").hidden = true; $("tabs").hidden = true; $("signin-err").textContent = err || ""; if (S.timer) clearInterval(S.timer); }
  function start() {
    $("signin").hidden = true; $("main").hidden = false; $("tabs").hidden = false;
    $("foot").textContent = DEMO ? "Demo: sample data, nothing is sent." : "Updates every minute while open.";
    load(); if (!DEMO) S.timer = setInterval(function () { if (document.visibilityState === "visible") load(); }, 60000);
  }
  (function () {  // check the key when they leave the field, clear the error as soon as it is right
    var k = $("key"), bad = function () { var v = k.value.trim(); return !(/^[a-f0-9-]{36}$/i.test(v)); };
    k.addEventListener("blur", function () { if (k.value.trim() && bad()) { k.setAttribute("aria-invalid", "true"); $("signin-err").textContent = "The key is 36 letters and numbers. Copy it again from your setup message."; } });
    k.addEventListener("input", function () { if (k.getAttribute("aria-invalid") === "true" && !bad()) { k.removeAttribute("aria-invalid"); $("signin-err").textContent = ""; } });
  })();
  $("signin-form").addEventListener("submit", function (e) {
    e.preventDefault(); var v = $("key").value.trim();
    if (!/^[a-f0-9-]{36}$/i.test(v)) { $("signin-err").textContent = "The key is 36 letters and numbers. Copy it again from your setup message."; return; }
    S.key = v; store.set(v); $("key").value = ""; start();
  });

  // ---------- demo data, built around today so it always looks live
  function Demo() {
    var t = istIso(), b = [], names = ["Ravi Teja", "Sravani", "Priya", "Anil", "Lakshmi", "Kiran", "Deepika", "Suresh", "Meena", "Rahul"], svc = ["Haircut", "Hair spa", "Facial", "Threading", "Beard trim", "Keratin", "Bridal trial"];
    var slots = ["10:00 AM", "11:00 AM", "12:30 PM", "2:00 PM", "4:00 PM", "5:30 PM", "7:00 PM"];
    slots.forEach(function (s, i) { b.push({ contact: "9198480" + String(10000 + i * 37), name: names[i], service: svc[i % svc.length], date_iso: t, slot: s, status: i === 5 ? "cancelled" : "confirmed", confirmed_at: i % 3 !== 2 ? t + "T03:00:00Z" : null }); });
    for (var dd = 1; dd <= 30; dd++) for (var j = 0; j < (dd * 7) % 5 + 2; j++) b.push({ contact: "9198481" + String(20000 + dd * 10 + j), name: names[(dd + j) % names.length], service: svc[(dd + j) % svc.length], date_iso: addDays(t, -dd), slot: slots[j % slots.length], status: (dd + j) % 9 === 0 ? "no_show" : (dd + j) % 11 === 0 ? "cancelled" : "completed", confirmed_at: null });
    b.push({ contact: "919848012345", name: "Sita", service: "Hair spa", date_iso: addDays(t, 1), slot: "11:00 AM", status: "confirmed", confirmed_at: null });
    var leads = names.map(function (n, i) { return { contact: i === 9 ? "web:visitor" + i : "9198480" + String(30000 + i * 41), name: n, score: ["hot", "warm", "cold"][i % 3], status: ["booked", "callback", "new"][i % 3], details: { service: svc[i % svc.length], date: i % 3 === 0 ? nice(t) : "", slot: i % 3 === 0 ? slots[i % slots.length] : "" }, source: ["whatsapp", "web", "meta_ads", "voice"][i % 4], updated_at: new Date(Date.now() - i * 5400e3).toISOString() }; });
    return { client: { name: "Glow Studio", niche: "salon" }, today: t, leads: leads, messages: [], bookings: b, waiting: 2 };
  }

  if (DEMO || S.key) start(); else showSignin();
})();
