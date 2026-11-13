// A203: free X-ray intake (company, work email, usage export + DPDP consent).
// Web-standard fetch handler like ingest.js (Supabase Edge Function, Cloudflare Worker or Node 18+). No dependencies.
// `store.save(row)` keeps the row until `delete_after` (14 days, the landing page promise) and returns an id.
// Not deployed (rule 9): goes live only on Akhil's "go".
import { sha256Hex } from './ingest.js';

export const MAX_BYTES = 5 * 1024 * 1024;
export const KEEP_DAYS = 14;
const FREE_MAIL = new Set(['gmail.com', 'googlemail.com', 'yahoo.com', 'yahoo.co.in', 'outlook.com', 'hotmail.com',
  'live.com', 'icloud.com', 'rediffmail.com', 'proton.me', 'protonmail.com', 'aol.com', 'zoho.com', 'yandex.com']);
const BANNED = ['prompt', 'prompts', 'response', 'completion', 'messages', 'content', 'input_text', 'output_text',
  'gen_ai.prompt', 'gen_ai.completion', 'reply', 'question', 'answer'];
const EMAIL = /[\w.+-]+@[\w-]+(\.[\w-]+)+/;
const PHONE = /(?<![\d])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?![\d])/;

const json = (status, body, extra = {}) => new Response(JSON.stringify(body), {
  status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', ...extra } });

/** Field errors in the words the form shows; {} when all good. */
export function checkFields({ company = '', email = '', consent = '' }, file) {
  const e = {}, c = String(company).trim(), m = String(email).trim().toLowerCase();
  if (c.length < 2 || c.length > 120 || /[\u0000-\u001f\u007f<>]/.test(c)) e.company = 'Enter your company name (2 to 120 characters).';
  if (m.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(m)) e.email = 'Enter a valid email, like name@yourcompany.in.';
  else if (FREE_MAIL.has(m.split('@')[1])) e.email = 'Use your work email, not a personal Gmail or Yahoo address.';
  if (!file || typeof file === 'string') e.file = 'Choose your usage export file (CSV or JSON).';
  else if (!/\.(csv|json|jsonl)$/i.test(file.name || '')) e.file = 'Upload a CSV or JSON export (.csv, .json or .jsonl).';
  else if (!file.size) e.file = 'That file is empty. Export last month\'s usage and try again.';
  else if (file.size > MAX_BYTES) e.file = 'That file is over 5 MB. Export one month only.';
  if (consent !== 'yes') e.consent = 'Tick the box so we may use the file for your X-ray.';
  return e;
}

/** Refuse prompts, replies and raw personal data. Returns the error text or null. */
export function scanExport(text) {
  const head = text.slice(0, 2000).split(/\r?\n/, 1)[0].toLowerCase().split(/[,;\t]/).map((s) => s.trim().replace(/^"|"$/g, ''));
  const keys = [...text.matchAll(/"([\w.]+)"\s*:/g)].map((k) => k[1].toLowerCase());
  const hit = BANNED.find((b) => head.includes(b) || keys.includes(b));
  if (hit) return `Your file has a "${hit}" column. Remove prompt and reply columns, then upload again. We only need model, tokens, time, feature and a hashed customer id.`;
  if (EMAIL.test(text)) return 'Your file has customer email addresses. Hash customer ids first (our script does it), then upload again.';
  if (PHONE.test(text)) return 'Your file has phone numbers. Hash customer ids first (our script does it), then upload again.';
  return null;
}

/** Fixed-window limiter: `max` uploads per `windowMs` per key (in memory; one instance per worker). */
export function makeLimiter(max = 5, windowMs = 3600e3) {
  const hits = new Map();
  return (key, now) => {
    const h = hits.get(key);
    if (!h || now - h.start >= windowMs) { hits.set(key, { start: now, n: 1 }); return 0; }
    if (h.n >= max) return Math.ceil((h.start + windowMs - now) / 1000);
    h.n += 1; return 0;
  };
}
const shared = makeLimiter();

export async function handleIntake(request, store, { now = Date.now(), limiter = shared, timeoutMs = 8000 } = {}) {
  if (request.method !== 'POST') return json(405, { error: 'method' }, { allow: 'POST' });
  if (!(request.headers.get('content-type') || '').startsWith('multipart/form-data')) return json(415, { error: 'type' });
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTES + 64 * 1024) {
    return json(413, { errors: { file: 'That file is over 5 MB. Export one month only.' } });
  }
  const ip = (request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || 'unknown').split(',')[0].trim();
  const wait = limiter(ip, now);
  if (wait) return json(429, { error: 'Too many uploads from this network. Try again in an hour.' }, { 'retry-after': String(wait) });

  let f;
  try { f = await request.formData(); } catch { return json(400, { error: 'form' }); }
  if (f.get('website')) return json(400, { error: 'form' }); // honeypot: people never see this field
  const fields = { company: f.get('company') || '', email: f.get('email') || '', consent: f.get('consent') || '' };
  const file = f.get('file');
  const errors = checkFields(fields, file);
  if (Object.keys(errors).length) return json(400, { errors });

  const text = await file.text();
  const bad = scanExport(text);
  if (bad) return json(422, { errors: { file: bad } });

  const row = {
    company: String(fields.company).trim(), email: String(fields.email).trim().toLowerCase(),
    filename: String(file.name).slice(0, 120), bytes: file.size, sha256: await sha256Hex(text), text,
    consent_at: new Date(now).toISOString(), delete_after: new Date(now + KEEP_DAYS * 864e5).toISOString(),
  };
  try {
    let timer;
    const id = await Promise.race([store.save(row),
      new Promise((_, no) => { timer = setTimeout(() => no(new Error('timeout')), timeoutMs); })]).finally(() => clearTimeout(timer));
    return json(202, { ok: true, id });
  } catch (err) {
    console.error('xray-intake save failed', err && err.message); // no personal data in logs
    return json(503, { error: 'We could not save your file just now. Nothing was kept. Please try again.' });
  }
}
