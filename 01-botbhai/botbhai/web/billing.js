// billing.html page script (moved out of the page so the CSP can forbid inline scripts; live check 14 Nov 2026).
(function () {
  "use strict";
  var API = "/.netlify/functions/billing", KEY = "kalpa.billing.key";
  var params = new URLSearchParams(location.search), DEMO = params.get("demo") === "1";
  var $ = function (id) { return document.getElementById(id); };
  var store = { get: function () { try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; } },
                set: function (v) { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} } };
  var frag = /(?:^|[#&])key=([^&]{32,200})/.exec(location.hash);
  if (frag) { store.set(decodeURIComponent(frag[1])); history.replaceState(null, "", location.pathname + location.search); }
  var S = { key: store.get(), filter: "open", data: null, armed: null, paying: null, busy: false };

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) { if (k === "text") n.textContent = attrs[k]; else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), attrs[k]); else if (attrs[k] != null) n.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function money(p) { return "₹" + (p / 100).toLocaleString("en-IN", { minimumFractionDigits: p % 100 ? 2 : 0, maximumFractionDigits: 2 }); }
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function nice(iso) { if (!iso) return ""; var p = String(iso).slice(0, 10).split("-"); return +p[2] + " " + MON[+p[1] - 1]; }
  function istNow() { return new Date(Date.now() + 330 * 60000); }
  function monthLabel(offset) { var d = istNow(); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() + offset); return MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function toast(m) { var t = $("toast"); t.textContent = m; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { t.hidden = true; }, 4200); }
  function state(i) { return i.status === "due" ? (i.overdue_days > 0 ? "late" : "due") : i.status; }

  function call(method, body) {
    if (DEMO) return Demo.call(method, body);
    return fetch(API, { method: method, headers: Object.assign({ Authorization: "Bearer " + S.key }, body ? { "Content-Type": "application/json" } : {}), body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { status: r.status, data: d }; }); });
  }
  function load() {
    return call("GET").then(function (r) {
      if (r.status === 401) { store.set(""); S.key = ""; return showSignin("That key didn't work. Check it and paste again."); }
      if (r.status === 503) return showSignin((r.data && r.data.error) || "Billing is switched off.");
      if (r.status !== 200) return toast("Couldn't load invoices. Try again.");
      S.data = r.data; render();
    }, function () { toast("You're offline."); });
  }
  function act(body, done) {
    if (S.busy) return Promise.resolve(); S.busy = true;
    return call("POST", body).then(function (r) {
      S.busy = false;
      if (r.status !== 200) { toast((r.data && r.data.error) || "That didn't work."); return; }
      S.armed = null; S.paying = null; if (done) toast(done);
      return load().then(function () { return r.data; });
    }, function () { S.busy = false; toast("You're offline. Nothing changed."); });
  }

  // ---------- render
  function render() {
    var d = S.data; if (DEMO) { $("title").textContent = "Invoices"; $("title").appendChild(el("span", { class: "demo-flag", text: "Demo" })); }
    $("upi-warn").hidden = d.seller.upi_ready;
    var due = 0, late = 0, nLate = 0, paidMonth = 0, ym = istNow().toISOString().slice(0, 7);
    d.invoices.forEach(function (i) {
      if (i.status === "due") { due += i.total_paise; if (i.overdue_days > 0) { late += i.total_paise; nLate++; } }
      if (i.status === "paid" && String(i.paid_on || "").slice(0, 7) === ym) paidMonth += i.total_paise;
    });
    var k = $("kpis"); k.textContent = "";
    [[money(due), "To collect"], [nLate ? money(late) : "0", "Overdue" + (nLate ? " · " + nLate : "")], [money(paidMonth), "Paid in " + MON[+ym.slice(5) - 1]]].forEach(function (x) {
      k.appendChild(el("div", { class: "kpi" }, [el("b", { text: x[0] }), el("span", { text: x[1] })]));
    });
    var sel = $("client"), keep = sel.value; sel.textContent = "";
    sel.appendChild(el("option", { value: "", text: d.clients.length ? "Choose a salon" : "No clients yet" }));
    d.clients.forEach(function (c) { sel.appendChild(el("option", { value: c.id, text: c.name + (c.active ? "" : " (paused)") })); });
    sel.value = keep;
    renderList();
  }
  function renderList() {
    var ul = $("invs"); ul.textContent = ""; ul.removeAttribute("aria-busy");
    var names = {}; S.data.clients.forEach(function (c) { names[c.id] = c.name; });
    var rows = S.data.invoices.filter(function (i) {
      var s = state(i); return S.filter === "all" || (S.filter === "open" && (s === "due" || s === "late")) || S.filter === s;
    });
    if (!rows.length) { ul.appendChild(el("li", { class: "empty", text: S.filter === "late" ? "Nothing overdue." : "No invoices here yet." })); return; }
    rows.forEach(function (i) {
      var s = state(i), label = { due: "Due " + nice(i.due_on), late: i.overdue_days + "d overdue", paid: "Paid " + nice(i.paid_on), void: "Void" }[s];
      var acts = el("div", { class: "acts" });
      acts.appendChild(el("a", { class: "btn ghost", href: i.link, target: "_blank", rel: "noopener", text: "Open" }));
      if (i.status === "due") {
        acts.appendChild(el("button", { class: "btn", text: s === "late" ? "Send reminder" : i.sent_at ? "Send again" : "Send on WhatsApp",
          onclick: function () { act({ action: s === "late" ? "remind" : "send", number: i.number }, "Sent to the salon on WhatsApp."); } }));
        acts.appendChild(el("button", { class: "btn ok", text: "Mark paid", onclick: function () { S.paying = S.paying === i.number ? null : i.number; renderList(); } }));
        acts.appendChild(el("button", { class: "btn danger", text: S.armed === i.number ? "Tap again to void" : "Void",
          onclick: function () { if (S.armed === i.number) act({ action: "void", number: i.number }, "Voided. The number stays in the series."); else { S.armed = i.number; renderList(); } } }));
      }
      var li = el("li", { class: "inv " + s }, [
        el("div", { class: "top" }, [el("span", { class: "who", text: names[i.client_id] || (i.bill_to && i.bill_to.name) || "Client" }), el("span", { class: "amt", text: money(i.total_paise) })]),
        el("div", { class: "top" }, [el("span", { class: "num", text: i.number + (i.period ? " · " + i.period : "") }), el("span", { class: "pill " + s, text: label })]),
        el("div", { class: "meta", text: "Issued " + nice(i.issued_on) + (i.sent_at ? " · sent " + nice(i.sent_at) : " · not sent yet") + (i.paid_ref ? " · UPI ref " + i.paid_ref : "") }),
        acts,
      ]);
      if (S.paying === i.number) {
        var ref = el("input", { id: "ref", inputmode: "numeric", maxlength: "35", placeholder: "12-digit UPI ref (optional)", autocomplete: "off" });
        li.appendChild(el("div", { class: "paybox" }, [el("div", { class: "field" }, [el("label", { for: "ref", text: "UPI reference (from your UPI app)" }), ref]),
          el("button", { class: "btn ok", text: "Save as paid", onclick: function () { act({ action: "paid", number: i.number, ref: ref.value.replace(/\s+/g, "") }, "Marked paid."); } })]));
      }
      ul.appendChild(li);
    });
  }

  // ---------- new invoice form
  var PRESETS = [
    { t: "Monthly plan", d: function () { return "BotBhai monthly plan · " + monthLabel(0); }, a: 1499, p: function () { return monthLabel(0); } },
    { t: "Setup fee", d: function () { return "BotBhai setup (Founding)"; }, a: 2999, p: function () { return ""; } },
    { t: "Next month", d: function () { return "BotBhai monthly plan · " + monthLabel(1); }, a: 1499, p: function () { return monthLabel(1); } },
  ];
  PRESETS.forEach(function (p) {
    $("presets").appendChild(el("button", { type: "button", class: "chip", "aria-pressed": "false", text: p.t, onclick: function (e) {
      $("desc").value = p.d(); $("amount").value = p.a; $("period").value = p.p(); preview();
      Array.prototype.forEach.call($("presets").children, function (b) { b.setAttribute("aria-pressed", String(b === e.currentTarget)); });
    } }));
  });
  function preview() { var a = Math.round(parseFloat($("amount").value || "0") * 100); $("preview").textContent = money(a > 0 ? a : 0); }
  $("amount").addEventListener("input", preview);
  $("new-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var body = { action: "create", client_id: $("client").value, items: [{ desc: $("desc").value.trim(), amount: parseFloat($("amount").value) }], period: $("period").value.trim(), due_days: parseInt($("due").value, 10) };
    if (!body.client_id) return toast("Choose a salon first.");
    act(body, "Invoice created. Tap Send on WhatsApp when ready.").then(function (d) { if (d) { $("desc").value = ""; $("amount").value = ""; $("period").value = ""; preview(); S.filter = "open"; syncChips(); renderList(); } });
  });
  function syncChips() { Array.prototype.forEach.call(document.querySelectorAll(".chips .chip"), function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-f") === S.filter)); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".chips .chip"), function (b) {
    b.addEventListener("click", function () { S.filter = b.getAttribute("data-f"); S.armed = null; syncChips(); renderList(); });
  });

  function showSignin(err) { $("signin").hidden = false; $("main").hidden = true; $("signin-err").textContent = err || ""; }
  function start() { $("signin").hidden = true; $("main").hidden = false; $("foot").textContent = DEMO ? "Demo: nothing is sent. Sample invoices only." : "Kalpa Labs · Udyam UDYAM-TS-02-0382711"; load(); }
  $("makekey").addEventListener("click", function () {
    var a = new Uint8Array(24); crypto.getRandomValues(a);
    var k = Array.prototype.map.call(a, function (x) { return ("0" + x.toString(16)).slice(-2); }).join("");
    $("newkey").value = k; $("newkey").select();
    if (navigator.clipboard) navigator.clipboard.writeText(k).then(function () { toast("Copied. Paste it into Netlify now."); }, function () {});
  });
  (function () {  // check the key when they leave the field, clear the error as soon as it is right
    var k = $("key"), bad = function () { var v = k.value.trim(); return !(v.length >= 32); };
    k.addEventListener("blur", function () { if (k.value.trim() && bad()) { k.setAttribute("aria-invalid", "true"); $("signin-err").textContent = "The billing key is at least 32 characters. Copy it again from Netlify."; } });
    k.addEventListener("input", function () { if (k.getAttribute("aria-invalid") === "true" && !bad()) { k.removeAttribute("aria-invalid"); $("signin-err").textContent = ""; } });
  })();
  $("signin-form").addEventListener("submit", function (e) {
    e.preventDefault(); var v = $("key").value.trim();
    if (v.length < 32) { $("signin-err").textContent = "The billing key is at least 32 characters. Copy it again from Netlify."; return; }
    S.key = v; store.set(v); $("key").value = ""; start();
  });

  // ---------- demo: same API shape, in memory, nothing sent
  var Demo = (function () {
    var today = istNow().toISOString().slice(0, 10), seq = 4;
    function add(days) { var d = istNow(); d.setUTCDate(d.getUTCDate() + days); return d.toISOString().slice(0, 10); }
    var clients = [{ id: "c1", name: "Glow Studio", active: true }, { id: "c2", name: "Shine Unisex Salon", active: true }, { id: "c3", name: "Mirror Mirror", active: true }];
    var invs = [
      { number: "KL/26-27/001", client_id: "c1", period: "", issued_on: add(-20), due_on: add(-13), status: "paid", paid_on: today, paid_ref: "629812345678", total_paise: 299900, sent_at: add(-20) },
      { number: "KL/26-27/002", client_id: "c2", period: monthLabel(0), issued_on: add(-12), due_on: add(-5), status: "due", total_paise: 149900, sent_at: add(-12) },
      { number: "KL/26-27/003", client_id: "c3", period: monthLabel(0), issued_on: add(-1), due_on: add(6), status: "due", total_paise: 149900, sent_at: null },
    ];
    function view(i) { var late = i.status === "due" && i.due_on < today ? Math.round((Date.parse(today) - Date.parse(i.due_on)) / 864e5) : 0;
      return Object.assign({}, i, { link: "#demo-" + i.number, overdue_days: late, created_at: i.issued_on }); }
    function ok(x) { return Promise.resolve({ status: 200, data: x }); }
    return { call: function (m, b) {
      if (m === "GET") return ok({ seller: { name: "Kalpa Labs", upi_ready: true }, clients: clients, invoices: invs.map(view).slice().reverse() });
      if (b.action === "create") { var a = Math.round(b.items[0].amount * 100);
        if (!(a > 0) || !b.items[0].desc) return Promise.resolve({ status: 400, data: { error: "Fill in what for and the amount." } });
        var n = { number: "KL/26-27/" + String(seq++).padStart(3, "0"), client_id: b.client_id, period: b.period, issued_on: today, due_on: add(b.due_days || 0), status: "due", total_paise: a, sent_at: null };
        invs.push(n); return ok({ ok: true, invoice: view(n) }); }
      var i = invs.filter(function (x) { return x.number === b.number; })[0];
      if (b.action === "send" || b.action === "remind") i.sent_at = today;
      if (b.action === "paid") { i.status = "paid"; i.paid_on = today; i.paid_ref = b.ref || null; }
      if (b.action === "void") i.status = "void";
      return ok({ ok: true });
    } };
  })();

  if (DEMO || S.key) start(); else showSignin();
})();
