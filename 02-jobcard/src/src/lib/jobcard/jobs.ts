import type { InvoiceMeta, Kind, Totals } from '@core/invoice.mjs';
// Saving a job and making its bill, fully offline. Every write lands in SQLite and the outbox together.
import type { Card } from '@core/parse.mjs';
import type { LocalDb } from './db';
import { computeInvoice, invoiceNo, SAC } from '@core/invoice.mjs';
import { enqueue } from './outbox';

export type Technician = { id: string; name: string; business_name?: string; address?: string; phone: string; gst_kind: Kind; gstin?: string; udyam?: string; state?: string; upi_vpa?: string };
type Ids = () => string;

/** IST calendar date, YYYY-MM-DD (bills are dated in India's time zone). */
export const istDate = (now: number) => new Date(now + 330 * 60_000).toISOString().slice(0, 10);

export async function saveJob(db: LocalDb, card: Card, { techId, newId, now = Date.now(), audioUri = null }: { techId: string; newId: Ids; now?: number; audioUri?: string | null }) {
  const jobId = newId(); const c = card.customer || {};
  let customerId: string | null = null;
  await db.execAsync('begin');
  try {
    if (c.phone || c.name) {
      customerId = newId();
      await enqueue(db, 'customer', customerId, { id: customerId, technician_id: techId, name: c.name || 'Customer', phone: c.phone || null, area: c.area || null }, now);
    }
    await db.runAsync('insert into jobs (id, card, audio_uri, created_at) values (?, ?, ?, ?)', jobId, JSON.stringify({ ...card, customer_id: customerId }), audioUri, now);
    await enqueue(db, 'job_card', jobId, { id: jobId, technician_id: techId, customer_id: customerId, status: 'done', appliance: card.appliance, brand: card.brand, capacity_tons: card.capacity_tons ?? null, issues: card.issues, parts: card.parts, transcript: card.notes, next_service: card.next_service, visited_at: new Date(now).toISOString() }, now);
    if (audioUri)
      await enqueue(db, 'voice', jobId, { job_card_id: jobId, uri: audioUri }, now);
    await db.execAsync('commit');
  }
  catch (e) { await db.execAsync('rollback'); throw e; }
  return { jobId, customerId };
}

/** Next number in this phone's FY series (JC/26-27/0001). The server's unique(technician_id, number) is the backstop. */
export async function nextInvoiceNo(db: LocalDb, date: string): Promise<string> {
  const probe = invoiceNo(1, date); const fy = probe.split('/')[1];
  await db.runAsync('insert into counters (fy, last_seq) values (?, 1) on conflict (fy) do update set last_seq = last_seq + 1', fy);
  const row = await db.getFirstAsync<{ last_seq: number }>('select last_seq from counters where fy = ?', fy);
  return invoiceNo(row!.last_seq, date);
}

export async function makeBill(db: LocalDb, jobId: string, tech: Technician, { now = Date.now(), newId }: { now?: number; newId: Ids }): Promise<{ meta: InvoiceMeta; totals: Totals }> {
  const job = await db.getFirstAsync<{ card: string; invoice_no: string | null }>('select card, invoice_no from jobs where id = ?', jobId);
  if (!job)
    throw new Error('job not found');
  if (job.invoice_no)
    throw new Error(`already billed as ${job.invoice_no}`); // GST: one bill per job, never re-numbered
  const card = JSON.parse(job.card) as Card & { customer_id: string | null };
  const unpriced = card.parts.filter(p => p.rate == null);
  if (!card.parts.length || unpriced.length)
    throw new Error(`needs a price: ${unpriced.map(p => p.desc).join(', ') || 'no work'}`);
  const sac = card.issues.includes('installation') ? SAC.install : SAC.home;
  const totals = computeInvoice({ kind: tech.gst_kind, lines: card.parts.map(p => ({ desc: p.desc, sac, qty: p.qty || 1, rate: p.rate as number })), supplierState: tech.state || 'Telangana', placeOfSupply: tech.state || 'Telangana' });
  const date = istDate(now);
  await db.execAsync('begin');
  let number: string;
  try {
    number = await nextInvoiceNo(db, date);
    await db.runAsync('update jobs set invoice_no = ? where id = ?', number, jobId);
    const invId = newId();
    await enqueue(db, 'invoice', invId, { id: invId, technician_id: tech.id, job_card_id: jobId, customer_id: card.customer_id, number, fy: number.split('/')[1], kind: totals.kind, issued_on: date, lines: card.parts, taxable_paise: totals.taxable, cgst_paise: totals.cgst, sgst_paise: totals.sgst, igst_paise: totals.igst, payable_paise: totals.payable, place_of_supply: totals.placeOfSupply }, now);
    await db.execAsync('commit');
  }
  catch (e) { await db.execAsync('rollback'); throw e; }
  const c = card.customer || {};
  return { totals, meta: { number, date, customer: { name: c.name || 'Customer', phone: c.phone || '', address: c.area || '' }, supplier: { name: tech.business_name || tech.name, address: tech.address || '', phone: `+91 ${tech.phone}`, gstin: tech.gstin, udyam: tech.udyam } } };
}
