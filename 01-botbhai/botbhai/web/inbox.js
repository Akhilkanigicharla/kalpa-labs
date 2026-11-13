// inbox.html page script (moved out of the page so the CSP can forbid inline scripts; live check 14 Nov 2026).
(function () {
  "use strict";
  var API = "/.netlify/functions/inbox", KEY = "botbhai.inbox.key", POLL_MS = 15000;
  var params = new URLSearchParams(location.search);
  var DEMO = params.get("demo") === "1";
  var $ = function (id) { return document.getElementById(id); };
  var store = { get: function () { try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; } },
                set: function (v) { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} } };
  // A setup link can carry the key in the #fragment (never sent to any server); save it and wipe it from the address bar.
  var frag = /(?:^|[#&])key=([a-f0-9-]{36})/i.exec(location.hash);
  if (frag) { store.set(frag[1]); history.replaceState(null, "", location.pathname + location.search); }

  var S = { key: store.get(), filter: "human", list: [], open: null, thread: null, client: null, timer: null, busy: false };

  // ---------- helpers
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) { if (k === "text") n.textContent = attrs[k]; else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), attrs[k]); else if (attrs[k] != null) n.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  var tz = { timeZone: "Asia/Kolkata" };
  function when(iso) {
    if (!iso) return "";
    var d = new Date(iso), now = new Date();
    var sameDay = d.toLocaleDateString("en-IN", tz) === now.toLocaleDateString("en-IN", tz);
    return sameDay ? d.toLocaleTimeString("en-IN", Object.assign({ hour: "numeric", minute: "2-digit" }, tz)) : d.toLocaleDateString("en-IN", Object.assign({ day: "numeric", month: "short" }, tz));
  }
  function clock(iso) {
    if (!iso) return "";
    var d = new Date(iso), day = function (x) { return x.toLocaleDateString("en-IN", tz); };
    var t = d.toLocaleTimeString("en-IN", Object.assign({ hour: "numeric", minute: "2-digit" }, tz));
    return day(d) === day(new Date()) ? t : (day(d) === day(new Date(Date.now() + 864e5)) ? "tomorrow " : day(d) + " ") + t;  // 12 h hold often ends tomorrow
  }
  function label(c) { return c.name || (c.channel === "web" ? "Website visitor" : "+" + c.contact.replace(/^(\d{2})(\d{5})(\d+)$/, "$1 $2 $3")); }
  function initial(c) { return (c.name || (c.channel === "web" ? "W" : "#")).trim().charAt(0).toUpperCase(); }
  var STATUS = { human: "Needs you", bot: "Bot", resolved: "Done" };
  function toast(msg) { var t = $("toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { t.hidden = true; }, 4200); }

  // ---------- data
  function call(method, body, query) {
    if (DEMO) return Demo.call(method, body, query);
    var url = API + (query ? "?" + new URLSearchParams(query) : "");
    return fetch(url, { method: method, headers: Object.assign({ Authorization: "Bearer " + S.key }, body ? { "Content-Type": "application/json" } : {}), body: body ? JSON.stringify(body) : undefined, credentials: "same-origin" })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { status: r.status, data: d }; }); });
  }
  function load() {
    return call("GET").then(function (r) {
      if (r.status === 401) { store.set(""); S.key = ""; showSignin("That key didn't work. Check it and paste again."); return; }
      if (r.status !== 200) { toast("Couldn't load chats. Retrying soon."); return; }
      S.client = r.data.client; S.list = r.data.conversations || []; renderHead(); renderList();
      if (S.open) return openChat(S.open, true);
    }).catch(function () { toast("You're offline. Retrying soon."); });
  }
  function openChat(contact, quiet) {
    S.open = contact; $("split").classList.add("open"); renderList();
    return call("GET", null, { contact: contact }).then(function (r) {
      if (r.status !== 200) { if (!quiet) toast("Couldn't open that chat."); return; }
      S.thread = r.data; renderThread(quiet);
    });
  }
  function act(action, extra) {
    if (S.busy || !S.open) return Promise.resolve();
    S.busy = true;
    return call("POST", Object.assign({ action: action, contact: S.open }, extra || {})).then(function (r) {
      S.busy = false;
      if (r.status !== 200) { toast((r.data && r.data.message) || "That didn't work. Try again."); return false; }
      var done = { take_over: "You've taken over. The bot is quiet for this chat.", resume: "The bot is back on this chat.", resolve: "Marked done. The bot answers new messages.", assign: "Saved.", note: "Note saved." }[action];
      if (done) toast(done);
      return load().then(function () { return true; });
    }, function () { S.busy = false; toast("You're offline. Nothing was sent."); return false; });
  }

  // ---------- render
  function renderHead() {
    var c = S.client || {}; $("biz").textContent = c.name || "Inbox";
    if (DEMO) $("biz").appendChild(el("span", { class: "demo-flag", text: "Demo" }));
    var n = { human: 0, bot: 0, resolved: 0 }; S.list.forEach(function (x) { n[x.status] = (n[x.status] || 0) + 1; });
    var counts = $("counts"); counts.textContent = "";
    counts.appendChild(el("span", { class: "count" }, [el("b", { text: String(n.human) }), " need you"]));
    counts.appendChild(el("span", { class: "count" }, [el("b", { text: String(n.bot) }), " with bot"]));
    document.title = (n.human ? "(" + n.human + ") " : "") + "BotBhai Inbox";
  }
  function renderList() {
    var ul = $("convos"); ul.textContent = ""; ul.removeAttribute("aria-busy");
    var rows = S.list.filter(function (c) { return S.filter === "all" || c.status === S.filter; });
    if (!rows.length) { ul.appendChild(el("li", { class: "empty", text: S.filter === "human" ? "Nobody is waiting for you. The bot has it." : "No chats here yet." })); return; }
    rows.forEach(function (c) {
      var prev = c.last ? (c.last.author === "staff" ? "You: " : c.last.author === "bot" ? "Bot: " : "") + c.last.body : "";
      ul.appendChild(el("li", null, [el("button", { class: "convo", "aria-current": String(S.open === c.contact), onclick: function () { openChat(c.contact); } }, [
        el("span", { class: "av", "aria-hidden": "true", text: initial(c) }),
        el("span", { style: "min-width:0" }, [el("span", { class: "who" }, [el("b", { text: label(c) }), c.assigned_to ? el("span", { class: "tag", text: "· " + c.assigned_to }) : null]), el("span", { class: "prev", text: prev })]),
        el("span", { class: "side" }, [el("time", { text: when(c.last ? c.last.created_at : c.updated_at) }), el("span", { class: "pill " + c.status, text: STATUS[c.status] })]),
      ])]));
    });
  }
  function renderThread(quiet) {
    var box = $("thread"), t = S.thread, c = t.conversation;
    var keepDraft = $("reply") ? $("reply").value : "";
    var keepNote = $("notes") && document.activeElement === $("notes") ? $("notes").value : null;
    box.textContent = "";
    box.appendChild(el("div", { class: "thead" }, [
      el("button", { class: "iconbtn back", "aria-label": "Back to chats", text: "←", onclick: function () { S.open = null; S.thread = null; $("split").classList.remove("open"); renderList(); } }),
      el("span", { class: "av", "aria-hidden": "true", text: initial(c) }),
      el("div", { class: "title" }, [el("b", { text: label(c) }), c.channel === "whatsapp" ? el("a", { href: "tel:+" + c.contact, text: "+" + c.contact }) : el("span", { class: "tag", text: "Website chat" })]),
      el("span", { class: "pill " + c.status, text: STATUS[c.status] }),
    ]));
    if (c.status === "human") box.appendChild(el("p", { class: "banner human", text: "You're handling this chat. The bot stays quiet until " + clock(c.human_until) + ", or until you tap Resume bot." }));
    if (c.opted_out) box.appendChild(el("p", { class: "banner warn", text: "This customer replied STOP. WhatsApp rules: don't message them unless they write START." }));
    else if (c.channel === "web") box.appendChild(el("p", { class: "banner warn", text: "Website visitors have no WhatsApp number, so you can't reply from here. Their details are in the dashboard." }));
    else if (!c.window_open) box.appendChild(el("p", { class: "banner warn", text: "Their last message was over 24 hours ago. WhatsApp only allows approved templates now, so call them instead." }));

    box.appendChild(el("div", { class: "actions" }, [
      c.status !== "human" ? el("button", { class: "btn warmth", onclick: function () { act("take_over"); }, text: "Take over" }) : el("button", { class: "btn", onclick: function () { act("resume"); }, text: "Resume bot" }),
      c.status !== "resolved" ? el("button", { class: "btn ghost", text: S.armed === c.contact ? "Tap again: bot takes over" : "Mark done", onclick: function () {
        if (S.armed === c.contact) { S.armed = null; act("resolve"); return; }  // two taps: a slip never hands a customer back to the bot
        S.armed = c.contact; renderThread(true);
        setTimeout(function () { if (S.armed === c.contact) { S.armed = null; if (S.thread && S.open === c.contact) renderThread(true); } }, 4000);
      } }) : null,
    ]));

    var msgs = el("div", { class: "msgs", id: "msgs", role: "log", "aria-label": "Messages" });
    (t.messages || []).forEach(function (m) {
      var who = m.author === "staff" ? "You" : m.author === "bot" ? "Bot" : null;
      msgs.appendChild(el("div", { class: "b " + m.author }, [who ? el("span", { class: "by", text: who }) : null, m.body || "", el("time", { text: clock(m.created_at) })]));
    });
    if (!(t.messages || []).length) msgs.appendChild(el("p", { class: "empty", text: "No messages yet." }));
    box.appendChild(msgs);

    var canReply = c.channel === "whatsapp" && !c.opted_out && c.window_open;
    var ta = el("textarea", { id: "reply", rows: "1", placeholder: canReply ? "Reply as " + ((S.client && S.client.name) || "the salon") + "…" : "Replying is off for this chat", "aria-label": "Your reply", maxlength: "4096" });
    ta.value = keepDraft; ta.disabled = !canReply;
    ta.addEventListener("input", function () { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 140) + "px"; });
    ta.addEventListener("keydown", function (e) { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(); });
    var btn = el("button", { class: "send", "aria-label": "Send", text: "➤", onclick: function () { send(); } }); btn.disabled = !canReply;
    function send() {  // optimistic: show the bubble now; a failed send says so and gives the words back
      var v = ta.value.trim(); if (!v || !canReply || S.busy) return;
      btn.disabled = true; ta.value = "";
      var empty = msgs.querySelector(".empty"); if (empty) empty.remove();
      var stamp = el("time", { text: "Sending…" });
      var pend = el("div", { class: "b staff pending" }, [el("span", { class: "by", text: "You" }), v, stamp]);
      msgs.appendChild(pend); msgs.scrollTop = msgs.scrollHeight;
      act("reply", { text: v }).then(function (ok) {
        if (ok) return;
        pend.className = "b staff failed"; stamp.textContent = "Not sent";
        if (!ta.value) ta.value = v; btn.disabled = false; ta.focus({ preventScroll: true });
      });
    }
    box.appendChild(el("div", { class: "compose" }, [ta, btn]));
    if (canReply) box.appendChild(el("p", { class: "hint", text: "Sent from your WhatsApp Business number. Replying pauses the bot for this chat." }));

    var who = el("input", { id: "assign", value: c.assigned_to || "", placeholder: "Staff name", maxlength: "40" });
    var notes = el("textarea", { id: "notes", maxlength: "2000", placeholder: "Only your team sees this" }); notes.value = keepNote != null ? keepNote : c.notes || "";
    box.appendChild(el("details", { class: "more" }, [el("summary", { text: "Assign & notes" + (c.assigned_to ? " · " + c.assigned_to : "") }),
      el("div", { class: "field" }, [el("label", { for: "assign", text: "Who's handling it" }), el("div", { class: "inline" }, [who, el("button", { class: "btn ghost", text: "Save", onclick: function () { act("assign", { assigned_to: who.value }); } })])]),
      el("div", { class: "field" }, [el("label", { for: "notes", text: "Private notes" }), notes, el("div", null, [el("button", { class: "btn ghost", text: "Save note", onclick: function () { act("note", { notes: notes.value }); } })])]),
    ]));
    msgs.scrollTop = msgs.scrollHeight;
    if (!quiet && keepNote == null && innerWidth >= 900 && canReply) ta.focus({ preventScroll: true });
  }
  function showSignin(err) { $("signin").hidden = false; $("split").hidden = true; $("signin-err").textContent = err || ""; stop(); }
  function start() {
    $("signin").hidden = true; $("split").hidden = false;
    $("foot").textContent = DEMO ? "Demo: nothing is sent. Sample chats only." : "Updates every 15 seconds while this page is open.";
    load(); stop(); S.timer = setInterval(function () { if (document.visibilityState === "visible") load(); }, POLL_MS);
  }
  function stop() { if (S.timer) clearInterval(S.timer); S.timer = null; }
  document.addEventListener("visibilitychange", function () { if (document.visibilityState === "visible" && S.timer) load(); });

  Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (b) {
    b.addEventListener("click", function () {
      S.filter = b.getAttribute("data-f");
      Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      renderList();
    });
  });
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

  // ---------- demo: the same API shape, in memory, nothing sent
  var Demo = (function () {
    var t0 = Date.now(), m = function (min) { return new Date(t0 - min * 60000).toISOString(); };
    var data = [
      { contact: "919812345678", name: "Ravi Teja", status: "human", human_until: new Date(t0 + 95 * 60000).toISOString(), assigned_to: "Lakshmi", notes: "Waited 30 min on Saturday. Offer 20% on next visit.", last_inbound_at: m(3), msgs: [
        ["in", "customer", "hi", 42], ["out", "bot", "Hi Ravi! 😊 Welcome back to Glow Studio. Same *Hair spa* again?", 42],
        ["in", "customer", "worst service last time, waited 30 min, no one picked phone", 6],
        ["out", "bot", "I'm really sorry about that, Ravi 🙏 I've told the owner right now; someone will reply to you personally.", 6],
        ["in", "customer", "ok waiting", 3] ] },
      { contact: "919800000002", name: "Sravani", status: "human", human_until: new Date(t0 + 50 * 60000).toISOString(), last_inbound_at: m(12), msgs: [
        ["in", "customer", "bridal makeup ki rate entha? 14 Dec", 15], ["out", "bot", "Congratulations! 💐 Bridal packages start at ₹15,000. 14 Dec is marked full, so I've asked the owner to call you.", 15],
        ["in", "customer", "talk to owner please", 12] ] },
      { contact: "919700000003", name: "Priya", status: "bot", last_inbound_at: m(25), msgs: [
        ["in", "customer", "book facial tomorrow 4pm", 26], ["out", "bot", "Booking confirmed ✅ Facial · Sat, 17 Oct · 4:00 PM. See you!", 25] ] },
      { contact: "web:visitor8842", name: null, status: "bot", last_inbound_at: m(60), msgs: [
        ["in", "customer", "do you do keratin?", 61], ["out", "bot", "Yes! Keratin is ₹3,500 and takes about 90 minutes. Want me to book it?", 60] ] },
      { contact: "919600000005", name: "Anil", status: "resolved", last_inbound_at: m(60 * 30), msgs: [
        ["in", "customer", "parking undha?", 60 * 30], ["out", "staff", "Yes Anil, 2 bike spots in front and car parking at the mall basement.", 60 * 30 - 5] ] },
    ];
    function view(d) {
      var last = d.msgs[d.msgs.length - 1];
      return { contact: d.contact, name: d.name, status: d.status === "human" && new Date(d.human_until) < new Date() ? "bot" : d.status, human_until: d.human_until || null,
        assigned_to: d.assigned_to || null, notes: d.notes || "", opted_out: false, channel: d.contact.indexOf("web:") === 0 ? "web" : "whatsapp",
        window_open: Date.now() - new Date(d.last_inbound_at).getTime() < 864e5, updated_at: m(last[3]),
        last: { direction: last[0], author: last[1], body: last[2], created_at: m(last[3]) } };
    }
    var rank = { human: 0, bot: 1, resolved: 2 };
    function ok(x) { return Promise.resolve({ status: 200, data: x }); }
    function call(method, body, query) {
      if (method === "GET" && !query) return ok({ client: { name: "Glow Studio", niche: "salon", hold_hours: 12 }, conversations: data.map(view).sort(function (a, b) { return rank[a.status] - rank[b.status]; }) });
      var d = data.filter(function (x) { return x.contact === ((query && query.contact) || (body && body.contact)); })[0];
      if (!d) return Promise.resolve({ status: 404, data: { error: "no such conversation" } });
      if (method === "GET") return ok({ conversation: view(d), messages: d.msgs.map(function (x) { return { direction: x[0], author: x[1], body: x[2], created_at: m(x[3]) }; }) });
      var hold = function () { d.status = "human"; d.human_until = new Date(Date.now() + 12 * 3.6e6).toISOString(); };
      if (body.action === "reply") {
        if (d.contact.indexOf("web:") === 0) return Promise.resolve({ status: 400, data: { message: "Website visitors have no WhatsApp number." } });
        d.msgs.push(["out", "staff", body.text, 0]); hold();
      } else if (body.action === "take_over") hold();
      else if (body.action === "resume") { d.status = "bot"; d.human_until = null; }
      else if (body.action === "resolve") { d.status = "resolved"; d.human_until = null; }
      else if (body.action === "assign") d.assigned_to = body.assigned_to || null;
      else if (body.action === "note") d.notes = body.notes;
      return ok({ ok: true });
    }
    return { call: call };
  })();

  if (DEMO) start(); else if (S.key) start(); else showSignin();
  if (DEMO && params.get("open")) openChat(params.get("open"));
})();
