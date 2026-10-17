// Ledger Peaks mockups (A12): shared helpers. Data comes from the <script id="lp-data"> block,
// which design/sample.py fills from the real price engine. All text goes in with textContent.
const LP = (() => {
  const data = JSON.parse(document.getElementById('lp-data').textContent);
  const rs = (paise, dp = 0) => '₹' + (paise / 100).toLocaleString('en-IN', { minimumFractionDigits: dp, maximumFractionDigits: dp });
  const pct = (a, b) => (b ? Math.round((a * 100) / b) : 0) + '%';
  const date = (iso) => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', timeZone: 'UTC' });
  const feat = (f) => ({ support_reply: 'Support replies', rag_search: 'Help-centre search', summarise: 'Chat summaries',
    classify: 'Ticket tagging', telugu_voice: 'Telugu voice' }[f] || f);
  function el(tag, attrs = {}, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') n.className = v; else if (k === 'style') n.style.cssText = v; else n.setAttribute(k, v);
    }
    for (const k of kids) n.append(k instanceof Node ? k : document.createTextNode(String(k)));
    return n;
  }
  function fill(root = document) {
    // <span data-lp="total_month"> → ₹ figure; data-lp-fmt="pct|int|raw"
    for (const n of root.querySelectorAll('[data-lp]')) {
      const v = n.dataset.lp.split('.').reduce((o, k) => (o == null ? o : o[k]), data);
      const f = n.dataset.lpFmt || 'rs';
      n.textContent = f === 'int' ? Number(v).toLocaleString('en-IN') : f === 'raw' ? v : f === 'date' ? date(v) : rs(v);
    }
  }
  function rows(list, obj, label = feat) {
    const max = Math.max(...Object.values(obj));
    const total = Object.values(obj).reduce((a, b) => a + b, 0);
    for (const [k, v] of Object.entries(obj)) {
      list.append(el('li', {}, el('span', {}, label(k)), el('span', { class: 'num' }, rs(v), ' ',
        el('span', { class: 'muted' }, pct(v, total))), el('div', { class: 'bar' }, el('i', { style: `width:${(v * 100) / max}%` }))));
    }
  }
  function dayChart(svgHost) {
    const days = Object.entries(data.by_day), max = Math.max(...days.map(([, v]) => v));
    const ns = 'http://www.w3.org/2000/svg', W = 320, H = 140, bw = W / days.length;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H + 22}`); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'AI cost per day: ' + days.map(([d, v]) => `${date(d)} ${rs(v)}`).join(', '));
    svg.style.cssText = 'width:100%;height:auto;display:block';
    days.forEach(([d, v], i) => {
      const h = Math.max(2, (v / max) * H), r = document.createElementNS(ns, 'rect');
      Object.entries({ x: i * bw + 6, y: H - h, width: bw - 12, height: h, rx: 6, fill: 'var(--world)' }).forEach(([k, x]) => r.setAttribute(k, x));
      const t = document.createElementNS(ns, 'text');
      Object.entries({ x: i * bw + bw / 2, y: H + 16, 'text-anchor': 'middle', fill: 'var(--muted)', 'font-size': 11, 'font-family': 'var(--f-mono)' }).forEach(([k, x]) => t.setAttribute(k, x));
      t.textContent = date(d).split(' ')[0];
      svg.append(r, t);
    });
    svgHost.append(svg);
  }
  const LOGO = '<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><path d="M2 25 11 9l5 8 4-6 8 14Z" fill="var(--world)"/><path d="M11 9l2.5 4.5h-5Z" fill="var(--gold)"/><path d="M2 27h26" stroke="var(--gold)" stroke-width="2"/></svg>';
  return { data, rs, pct, date, feat, el, fill, rows, dayChart, LOGO };
})();
