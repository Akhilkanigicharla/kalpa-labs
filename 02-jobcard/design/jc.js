// JobCard screens (A13): fills the page from <script id="jc-data"> (made by sample.mjs from the real core). No network.
(() => {
  const D = JSON.parse(document.getElementById("jc-data").textContent);
  const $ = (s) => document.querySelector(s);
  const set = (k, v) => document.querySelectorAll(`[data-jc="${k}"]`).forEach((n) => { n.textContent = v; });
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const rs = (n) => "₹" + Number(n).toLocaleString("en-IN");
  const phone = (p) => `${p.slice(0, 5)} ${p.slice(5)}`;
  const c = D.job.card;

  set("supplier", `${D.supplier.name} · ${D.supplier.area}`);
  set("today", D.todayNice);
  set("timer", `0:${String(D.job.seconds).padStart(2, "0")} / 2:00`);

  // waveform: fixed heights so the screenshot is stable
  const wave = $("#wave");
  [8, 14, 22, 12, 26, 18, 10, 24, 16, 28, 12, 20, 9, 17, 25, 11, 19, 7].forEach((h) => { const i = el("i"); i.style.height = h + "px"; wave.append(i); });

  // transcript with every number highlighted (that's what becomes money on the bill)
  const heard = $("#heard");
  D.job.transcript.split(/(\d[\d,. ]*\d|\d)/).forEach((part, i) => heard.append(i % 2 ? el("mark", null, part) : document.createTextNode(part)));

  const SAY = [["customer", "Customer", "పేరు"], ["phone", "Phone", "ఫోన్"], ["appliance", "AC / fridge", "మెషిన్"], ["problem", "Problem", "సమస్య"],
    ["parts", "Parts + price", "ధర"], ["next", "Next service", "మళ్ళీ ఎప్పుడు"]];
  for (const [k, en, te] of SAY) { const li = el("li", D.job.heard[k] ? "ok" : "no"); li.append(document.createTextNode(en + " · "), el("span", "te", te)); $("#say").append(li); }

  for (const r of D.recent) {
    const li = el("li"); const who = el("div", "who"); who.append(el("b", null, `${r.name} garu`), el("span", null, `${r.appliance} · ${r.area} · ${r.date}`));
    li.append(who, el("span", "amt", rs(r.amount))); $("#recent").append(li);
  }

  // job card
  set("cname", `${c.customer.name} garu`);
  set("carea", `${c.customer.area}, Hyderabad`);
  const tel = $('[data-jc="cphone"]'); tel.textContent = "+91 " + phone(c.customer.phone); tel.href = "tel:+91" + c.customer.phone;
  set("machine", [c.brand, D.job.appliance[0], c.capacity_tons ? `${c.capacity_tons} ton` : null].filter(Boolean).join(" · "));
  for (const i of D.job.issues) $("#issues").append(el("span", "tag", i));
  set("next", D.job.nextNice || "Not said");
  const tb = $("#parts");
  for (const p of c.parts) { const tr = el("tr"); tr.append(el("td", null, p.desc), el("td", "n", p.rate == null ? "₹ ?" : rs(p.rate))); tb.append(tr); }
  const sum = c.parts.reduce((s, p) => s + (p.rate || 0), 0);
  const tot = el("tr", "tot"); tot.append(el("td", null, "Total · మొత్తం"), el("td", "n", rs(sum))); tb.append(tot);
  const ok = c.total_check === "matches parts";
  $("#tcheck").className = "check" + (ok ? "" : " warn");
  $("#tcheck").textContent = ok ? `✓ Matches the total you said (${rs(c.total)})` : c.total_check === "no spoken total" ? "Total worked out from the parts" : `Check: you said ${rs(c.total)}, parts add to ${rs(sum)}`;
  if (c.missing.length) $("#missing").append(el("p", "chips", `Not heard: ${c.missing.join(", ")}. Tap to type it.`));

  // bill: the real invoice HTML (lib/invoice.mjs) in a sandboxed frame, with our self-hosted fonts
  set("payable", D.invoice.payableText.replace(/\.00$/, ""));
  set("words", D.invoice.words);
  set("invno", D.invoice.number); set("invdate", D.invoice.date);
  const fonts = `<style>@font-face{font-family:"Rozha One";src:url(${new URL("../../00-hq/design/fonts/rozha-one-latin-400-normal.woff", location.href)}) format("woff")}
@font-face{font-family:"Anek Latin";font-weight:400 600;src:url(${new URL("../../00-hq/design/fonts/anek-latin-latin-600-normal.woff", location.href)}) format("woff")}
@font-face{font-family:"Anek Latin";font-weight:700;src:url(${new URL("../../00-hq/design/fonts/anek-latin-latin-700-normal.woff", location.href)}) format("woff")}
@font-face{font-family:"Anek Telugu";font-weight:400 600;src:url(${new URL("../../00-hq/design/fonts/anek-telugu-telugu-400-normal.woff", location.href)}) format("woff")}
@font-face{font-family:"Anek Telugu";font-weight:700;src:url(${new URL("../../00-hq/design/fonts/anek-telugu-telugu-700-normal.woff", location.href)}) format("woff")}
body{margin:14px!important}</style>`;
  $("#inv").srcdoc = D.invoice.html.replace("</head>", fonts + "</head>");
  const billMsg = `Namaste ${c.customer.name} garu, your bill ${D.invoice.number} for ${D.invoice.payableText} from ${D.supplier.name}. Thank you! / ధన్యవాదాలు!`;
  $("#wa-bill").href = `https://wa.me/91${c.customer.phone}?text=${encodeURIComponent(billMsg)}`;

  // reminders
  set("ndue", D.reminders.length);
  set("duesum", rs(D.reminders.reduce((s, r) => s + r.lastBill, 0)));
  const fill = (r) => D.reminderText.replace("{name}", r.name).replace("{applianceTe}", r.applianceTe).replace("{due}", r.dueNice).replace("{supplier}", D.supplier.name);
  D.reminders.forEach((r, i) => {
    const box = el("div", "rem"); if (i) box.style.cssText = "border-top:1px solid var(--rule);padding-top:12px;margin-top:8px";
    const top = el("div", "top-line"); const who = el("div", "who");
    who.append(el("b", null, `${r.name} garu`), el("div", "muted", `${[r.brand, r.appliance].filter(Boolean).join(" ")} · ${r.area}`), el("div", "muted", `Last service ${r.last} · ${rs(r.lastBill)}`));
    const due = el("span", "due " + (r.inDays < 0 ? "late" : r.inDays <= 7 ? "soon" : "later"), r.inDays < 0 ? `${-r.inDays} days late` : r.inDays === 0 ? "today" : `in ${r.inDays} days`);
    top.append(who, due);
    const row = el("div", "row");
    const call = el("a", "btn", "Call"); call.href = "tel:+91" + r.phone; call.setAttribute("aria-label", `Call ${r.name}`);
    const wa = el("a", "btn wa", "WhatsApp"); wa.href = `https://wa.me/91${r.phone}?text=${encodeURIComponent(fill(r))}`; wa.setAttribute("aria-label", `WhatsApp ${r.name}`);
    row.append(call, wa); box.append(top, row); $("#reminders").append(box);
  });
  if (D.reminders[0]) $("#bubble").textContent = fill(D.reminders[0]);
  set("pro", D.plan.pro); set("proyear", D.plan.proYear.toLocaleString("en-IN")); set("freecards", D.plan.freeCards);

  // tabs (+ deep link #card, #bill, #remind for screenshots)
  const show = (v) => {
    document.querySelectorAll(".view").forEach((s) => s.classList.toggle("on", s.id === "v-" + v));
    document.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.v === v)));
    window.scrollTo(0, 0);
  };
  document.querySelectorAll("[data-v],[data-go]").forEach((b) => b.addEventListener("click", () => { const v = b.dataset.v || b.dataset.go; history.replaceState(null, "", "#" + v); show(v); }));
  document.querySelectorAll('[aria-pressed]').forEach((b) => b.addEventListener("click", () => {
    b.parentElement.querySelectorAll("[aria-pressed]").forEach((x) => { x.setAttribute("aria-pressed", String(x === b)); if (x.classList.contains("btn")) x.classList.toggle("primary", x === b); });
  }));
  if (/^#(record|card|bill|remind)$/.test(location.hash)) show(location.hash.slice(1));
})();
