// A203: free X-ray intake form on the landing page. Checks each field on blur (UX pattern 15), then posts to the
// intake API (06-finops/src/api/intake.js, same rules). Success or failure always says what happened, with Retry.
(() => {
  const form = document.getElementById('xray-form');
  if (!form) return;
  const status = document.getElementById('xf-status'), send = document.getElementById('xf-send');
  const FREE = /@(gmail|googlemail|yahoo|outlook|hotmail|live|icloud|rediffmail|proton|protonmail|aol|zoho|yandex)\.(com|co\.in|me)$/i;
  const rules = {
    company: (i) => { const v = i.value.trim(); return v.length < 2 || v.length > 120 || /[<>]/.test(v) ? 'Enter your company name (2 to 120 characters).' : ''; },
    email: (i) => { const v = i.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return 'Enter a valid email, like name@yourcompany.in.';
      return FREE.test(v) ? 'Use your work email, not a personal Gmail or Yahoo address.' : ''; },
    file: (i) => { const f = i.files && i.files[0];
      if (!f) return 'Choose your usage export file (CSV or JSON).';
      if (!/\.(csv|json|jsonl)$/i.test(f.name)) return 'Upload a CSV or JSON export (.csv, .json or .jsonl).';
      if (!f.size) return "That file is empty. Export last month's usage and try again.";
      return f.size > 5 * 1024 * 1024 ? 'That file is over 5 MB. Export one month only.' : ''; },
    consent: (i) => (i.checked ? '' : 'Tick the box so we may use the file for your X-ray.'),
  };
  const input = (name) => form.elements[name];
  function show(name, msg) {
    const i = input(name), e = document.getElementById(`xf-${name}-err`);
    e.textContent = msg; i.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }
  const check = (name) => { const m = rules[name](input(name)); show(name, m); return !m; };
  for (const name of Object.keys(rules)) {
    const i = input(name);
    i.addEventListener(i.type === 'checkbox' || i.type === 'file' ? 'change' : 'blur', () => check(name));
    i.addEventListener('input', () => { if (i.getAttribute('aria-invalid') === 'true') check(name); });
  }
  function say(text, bad, retry) {
    status.className = bad ? 'bad' : 'ok';
    status.replaceChildren(Object.assign(document.createElement('p'), { textContent: text }));
    status.firstChild.style.margin = '0';
    if (retry) {
      const b = Object.assign(document.createElement('button'), { type: 'button', className: 'btn btn-primary', textContent: 'Retry' });
      b.onclick = () => form.requestSubmit();
      status.append(b);
    }
  }
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const okAll = Object.keys(rules).map(check).every(Boolean);
    if (!okAll) { form.querySelector('[aria-invalid=true]').focus(); return; }
    if (!navigator.onLine) return say('You are offline. Nothing was sent. Connect to the internet and tap Retry.', true, true);
    send.disabled = true; send.textContent = 'Sending…'; say('Uploading your file…', false);
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 30000);
    try {
      const r = await fetch(form.dataset.endpoint, { method: 'POST', body: new FormData(form), signal: ctl.signal });
      const body = await r.json().catch(() => ({}));
      if (r.status === 202) {
        const to = input('email').value.trim();
        form.replaceChildren(Object.assign(document.createElement('p'), { role: 'status', id: 'xf-done',
          textContent: `Got it. Your X-ray will reach ${to} within 48 hours. Your file is deleted 14 days after that unless you sign up.` }));
        return;
      }
      if (body.errors) {
        for (const [k, m] of Object.entries(body.errors)) if (rules[k]) show(k, m);
        say('Please fix the marked field and send again.', true);
        const first = form.querySelector('[aria-invalid=true]'); if (first) first.focus();
      } else if (r.status === 429) say(body.error || 'Too many uploads from this network. Try again in an hour.', true);
      else say("We couldn't save your file just now. Nothing was kept. Please try again.", true, true);
    } catch (e) {
      say(e.name === 'AbortError' ? 'The upload took too long. Nothing was kept. Check your connection and tap Retry.'
        : "We couldn't reach our server. Nothing was kept. Check your connection and tap Retry.", true, true);
    } finally {
      clearTimeout(t); if (send.isConnected) { send.disabled = false; send.textContent = 'Send my export'; }
    }
  });
})();
