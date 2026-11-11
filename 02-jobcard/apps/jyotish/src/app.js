/* Kalpa Jyotish UI. No network calls; birth data is kept only in this page, and in localStorage
   only when the user ticks "Remember on this phone". */
(function () {
  'use strict';
  const J = window.Jyotish, D = window.JyotishData, N = window.JyotishNames, I = window.JyotishI18n;
  const $ = (id) => document.getElementById(id);
  const KEY = { birth: 'kj.birth', lang: 'kj.lang', theme: 'kj.theme' };
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode: ignore */ } },
    del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } },
  };
  let lang = I.LANGS.includes(store.get(KEY.lang)) ? store.get(KEY.lang) : 'en';
  const t = (k, v) => I.t(lang, k, v);
  const L = (obj) => obj[lang] || obj.en; // pick a label from a {en,te,hi} object

  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === 'class') el.className = v; else if (k === 'lang') el.lang = v; else el.setAttribute(k, v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : String(kid));
    return el;
  }
  const fmtTime = (date, tz) => {
    const opts = { hour: 'numeric', minute: '2-digit', day: 'numeric', month: 'short' };
    if (!/^[+-]|^(UTC|GMT)/i.test(tz)) opts.timeZone = tz;
    else return date.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
    return new Intl.DateTimeFormat(lang + '-IN', opts).format(date);
  };
  const todayISO = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };

  /* ---------- static labels ---------- */
  function applyLabels() {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-t]').forEach((el) => { el.textContent = t(el.dataset.t); });
    document.querySelectorAll('[data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === lang)));
    fillCities($('b-city'), true);
    fillCities($('d-city'), false);
    fillNameControls();
  }

  function fillCities(sel, withOther) {
    const keep = sel.value;
    sel.replaceChildren(...D.CITIES.map((c, i) => h('option', { value: String(i) }, c.name)));
    if (withOther) sel.append(h('option', { value: 'other' }, t('otherPlace')));
    if (keep) sel.value = keep;
  }

  /* ---------- views ---------- */
  function show(view) {
    document.querySelectorAll('.view').forEach((v) => { v.hidden = v.id !== 'view-' + view; });
    document.querySelectorAll('.tab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.view === view)));
    const v = $('view-' + view);
    v.classList.remove('rise'); void v.offsetWidth; v.classList.add('rise');
  }

  /* ---------- birth star ---------- */
  function placeFrom(selId, latId, lonId, tzId) {
    const v = $(selId).value;
    if (v !== 'other') { const c = D.CITIES[Number(v)]; return { lat: c.lat, lon: c.lon, tz: c.tz }; }
    return { lat: parseFloat($(latId).value), lon: parseFloat($(lonId).value), tz: $(tzId).value.trim() };
  }
  let lastChart = null;
  function onStar(e) {
    e.preventDefault();
    $('star-err').textContent = '';
    try {
      const place = placeFrom('b-city', 'b-lat', 'b-lon', 'b-tz');
      const input = { date: $('b-date').value, time: $('b-time').value, ...place };
      lastChart = { input, chart: J.birthChart(input) };
      if ($('b-remember').checked) store.set(KEY.birth, JSON.stringify({ ...input, city: $('b-city').value }));
      else store.del(KEY.birth);
      renderStar();
    } catch (err) {
      $('star-err').textContent = t('errPrefix', { e: err.message });
    }
  }
  function kv(label, ...value) { return h('div', { class: 'kv' }, h('dt', null, label), h('dd', null, ...value)); }
  function renderStar() {
    const out = $('star-out');
    if (!lastChart) { out.replaceChildren(); return; }
    const c = lastChart.chart;
    const n = c.nakshatra;
    const syl = h('div', { class: 'syl card' },
      h('p', { class: 'muted' }, t('akshara')),
      h('p', { class: 'syl-big' }, h('span', { lang: 'te' }, n.akshara.te), h('span', { lang: 'hi' }, n.akshara.dev), h('span', { lang: 'en' }, n.akshara.ro)),
      h('button', { type: 'button', class: 'btn gold', id: 'go-names' }, t('seeNames')));
    const list = h('dl', { class: 'card kvs' },
      kv(t('rasi'), L(c.rasi.name)),
      kv(t('nakshatra'), L(n.name), ', ', t('pada', { p: n.pada })),
      kv(t('tithi'), L(c.tithi.pakshaName), ' ', L(c.tithi.name)),
      kv(t('vara'), L(c.vara.name)),
      kv(t('moonLon'), h('span', { class: 'mono' }, c.moonSidereal.toFixed(2) + '°')));
    const notes = [];
    if (c.minutesFromPadaEdge < 20) notes.push(h('p', { class: 'warn' }, t('edgeWarn', { m: Math.max(1, c.minutesFromPadaEdge) })));
    if (c.vara.beforeSunrise) notes.push(h('p', { class: 'muted' }, t('beforeSunrise')));
    if (c.sunrise.estimated) notes.push(h('p', { class: 'muted' }, t('estimated')));
    out.replaceChildren(syl, list, ...notes);
    $('go-names').addEventListener('click', () => {
      $('n-syl').value = n.index + ':' + (n.pada - 1);
      renderNames();
      show('names');
    });
  }

  /* ---------- names ---------- */
  function fillNameControls() {
    const syl = $('n-syl'), keep = syl.value;
    syl.replaceChildren(h('option', { value: '' }, t('anySyllable')),
      ...D.NAKSHATRAS.map((nk, i) => h('optgroup', { label: L(nk) },
        ...nk.ak.map((a, p) => h('option', { value: i + ':' + p }, `${nk.ro[p]} · ${J.devToTelugu(a)} · ${a}`)))));
    syl.value = keep;
    const g = $('n-gender'), gk = g.value;
    g.replaceChildren(h('option', { value: '' }, t('any')), h('option', { value: 'm' }, t('boy')), h('option', { value: 'f' }, t('girl')));
    g.value = gk;
    const nu = $('n-num'), nk2 = nu.value;
    nu.replaceChildren(h('option', { value: '' }, t('any')), ...[1, 2, 3, 4, 5, 6, 7, 8, 9].map((x) => h('option', { value: String(x) }, String(x))));
    nu.value = nk2;
    renderNames();
    renderCheck();
  }
  function nameCard(r) {
    return h('li', { class: 'name' },
      h('p', { class: 'nm' }, h('strong', null, r.en), h('span', { lang: 'te' }, r.te), h('span', { lang: 'hi' }, r.hi)),
      h('p', { class: 'muted' }, r.meaning),
      h('p', { class: 'meta' }, `${r.g === 'm' ? t('boy') : r.g === 'f' ? t('girl') : t('any')} · ${r.numerology.total} → ${r.numerology.single}`));
  }
  function renderNames() {
    const v = $('n-syl').value;
    const [ni, pi] = v ? v.split(':').map(Number) : [null, null];
    const akshara = v ? D.NAKSHATRAS[ni].ak[pi] : '';
    const opts = { gender: $('n-gender').value, letter: $('n-letter').value, number: $('n-num').value };
    const rows = J.suggestNames(N, akshara, opts);
    const list = $('n-list');
    $('n-count').textContent = t('countNames', { n: rows.length });
    if (rows.length) { list.replaceChildren(h('ul', { class: 'name-list' }, rows.map(nameCard))); return; }
    if (!v) { list.replaceChildren(h('p', { class: 'card muted' }, t('noMatch'))); return; }
    // Fall back to the other padas of the same nakshatra.
    const nk = D.NAKSHATRAS[ni];
    const other = nk.ak.filter((_, p) => p !== pi).flatMap((a) => J.suggestNames(N, a, opts));
    list.replaceChildren(h('p', { class: 'card muted' }, J.suggestNames(N, akshara).length ? t('noMatch') : t('noNames')),
      other.length ? h('h3', null, t('otherSyl', { n: L(nk) })) : null,
      other.length ? h('ul', { class: 'name-list' }, other.map(nameCard)) : null);
  }
  function renderCheck() {
    const name = $('n-check').value.trim();
    if (!/[a-z]/i.test(name)) { $('n-check-out').textContent = ''; return; }
    const c = J.chaldean(name);
    $('n-check-out').textContent = t('total', { t: c.total, s: c.single });
  }

  /* ---------- good days ---------- */
  function onDays(e) {
    e.preventDefault();
    $('days-err').textContent = '';
    try {
      const c = D.CITIES[Number($('d-city').value)];
      const days = J.muhuratDays($('d-from').value, Number($('d-days').value), c.lat, c.lon, c.tz);
      const hide = $('d-clear').checked;
      const shown = days.filter((d) => !hide || !d.flags.length);
      const items = shown.map((d) => {
        const flags = d.flags.map((f) => h('span', { class: 'flag' }, t(f === 'amavasya' ? 'avoidAmavasya' : 'avoidRikta')));
        const date = new Intl.DateTimeFormat(lang + '-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(d.date + 'T00:00Z'));
        return h('li', { class: 'day card' + (d.flags.length ? ' avoid' : '') },
          h('p', { class: 'day-h' }, h('strong', null, date), h('span', null, L(d.vara.name))),
          h('p', null, L(d.tithi.pakshaName), ' ', L(d.tithi.name), ' ', h('span', { class: 'muted' }, d.tithi.endsAt ? t('until', { t: fmtTime(d.tithi.endsAt, c.tz) }) : '')),
          h('p', null, L(d.nakshatra.name), ' ', h('span', { class: 'muted' }, d.nakshatra.endsAt ? t('until', { t: fmtTime(d.nakshatra.endsAt, c.tz) }) : '')),
          h('p', { class: 'meta' }, t('sunrise', { t: fmtTime(d.sunrise.at, c.tz) }), d.sunrise.estimated ? ' ' + t('estimated') : ''),
          flags.length ? h('p', null, flags) : null);
      });
      $('d-list').replaceChildren(...(items.length ? items : [h('li', { class: 'card muted' }, t('noDays'))]));
    } catch (err) {
      $('days-err').textContent = t('errPrefix', { e: err.message });
    }
  }

  /* ---------- theme ---------- */
  function applyTheme(th) {
    if (th === 'light' || th === 'dark') document.documentElement.dataset.theme = th;
    else delete document.documentElement.dataset.theme;
  }
  function toggleTheme() {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    const next = dark ? 'light' : 'dark';
    applyTheme(next);
    store.set(KEY.theme, next);
  }

  /* ---------- start ---------- */
  function init() {
    applyTheme(store.get(KEY.theme));
    $('d-from').value = todayISO();
    applyLabels();
    const saved = (() => { try { return JSON.parse(store.get(KEY.birth) || 'null'); } catch { return null; } })();
    if (saved) {
      $('b-date').value = saved.date || '';
      $('b-time').value = saved.time || '';
      $('b-city').value = saved.city || '0';
      if (saved.city === 'other') { $('b-lat').value = saved.lat; $('b-lon').value = saved.lon; $('b-tz').value = saved.tz; }
      $('b-remember').checked = true;
    }
    $('b-other').classList.toggle('hidden', $('b-city').value !== 'other');
    $('b-city').addEventListener('change', () => $('b-other').classList.toggle('hidden', $('b-city').value !== 'other'));
    $('star-form').addEventListener('submit', onStar);
    $('days-form').addEventListener('submit', onDays);
    ['n-syl', 'n-gender', 'n-num'].forEach((id) => $(id).addEventListener('change', renderNames));
    $('n-letter').addEventListener('input', renderNames);
    $('n-check').addEventListener('input', renderCheck);
    document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => show(b.dataset.view)));
    document.querySelectorAll('[data-lang]').forEach((b) => b.addEventListener('click', () => {
      lang = b.dataset.lang; store.set(KEY.lang, lang); applyLabels(); renderStar();
    }));
    $('theme').addEventListener('click', toggleTheme);
    $('clear').addEventListener('click', () => {
      store.del(KEY.birth); $('b-remember').checked = false; $('cleared').textContent = t('cleared');
    });
    show('star');
  }
  init();
})();
