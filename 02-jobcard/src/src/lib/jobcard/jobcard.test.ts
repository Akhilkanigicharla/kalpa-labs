// A36 (b2.q19 + b2.q20): offline job → SQLite + outbox → sync later; bill numbering; dictation; share.
import type { Technician } from './jobs';
import { parseTranscript } from '@core/parse.mjs';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { ExpoSpeechRecognitionModule as Speech } from 'expo-speech-recognition';
import { migrate } from './db';
import { istDate, makeBill, nextInvoiceNo, saveJob } from './jobs';
import { backoffMs, enqueue, flush, MAX_ATTEMPTS, pendingCount, PermanentError } from './outbox';
import { shareBill } from './share';
import { supabaseSender } from './sync';
import { memoryDb } from './test-db';
import { dictationOptions, startDictation } from './voice';

const tech: Technician = { id: 't1', name: 'Ravi', business_name: 'Ravi Cooling Services', phone: '9000022222', gst_kind: 'unregistered', state: 'Telangana' };
let n = 0;
const newId = () => `id-${++n}`;
const NOW = Date.parse('2026-10-18T06:00:00Z');

async function freshDb() { const db = memoryDb(); await migrate(db); return db; }

describe('offline save and outbox', () => {
  it('saves the job and queues customer → job card → voice, in order', async () => {
    const db = await freshDb();
    const card = parseTranscript('Split AC gas refill 2500, capacitor 450, customer Sita 9000033333');
    const { jobId, customerId } = await saveJob(db, card, { techId: 't1', newId, now: NOW, audioUri: 'file:///note.wav' });
    const rows = await db.getAllAsync<{ kind: string; row_id: string; payload: string }>('select kind, row_id, payload from outbox order by id');
    expect(rows.map(r => r.kind)).toEqual(['customer', 'job_card', 'voice']);
    expect(JSON.parse(rows[1].payload)).toMatchObject({ id: jobId, customer_id: customerId, technician_id: 't1' });
    expect(await pendingCount(db)).toBe(3);
  });

  it('airplane mode: nothing is sent, nothing is lost; later it syncs in order', async () => {
    const db = await freshDb();
    await saveJob(db, parseTranscript('gas refill 2500, customer Sita 9000033333'), { techId: 't1', newId, now: NOW });
    const sent: string[] = [];
    const send = jest.fn(async (it: { kind: string }) => { sent.push(it.kind); });
    expect(await flush(db, send, { now: NOW, online: false })).toMatchObject({ sent: 0, left: 2 });
    expect(send).not.toHaveBeenCalled();
    expect(await flush(db, send, { now: NOW + 1000, online: true })).toMatchObject({ sent: 2, left: 0 });
    expect(sent).toEqual(['customer', 'job_card']);
  });

  it('a failure stops the run (order kept) and backs off; a permanent error is parked', async () => {
    const db = await freshDb();
    for (const k of ['customer', 'job_card', 'invoice'] as const) await enqueue(db, k, k, { k }, NOW);
    const failOnce = jest.fn().mockRejectedValueOnce(new Error('network')).mockResolvedValue(undefined);
    expect(await flush(db, failOnce, { now: NOW })).toMatchObject({ sent: 0, failed: 1, left: 3 });
    expect(await flush(db, failOnce, { now: NOW + 1000 })).toMatchObject({ sent: 0, left: 3 }); // still in backoff
    expect(await flush(db, failOnce, { now: NOW + backoffMs(1) })).toMatchObject({ sent: 3, left: 0 });
    expect(backoffMs(1)).toBe(30_000); expect(backoffMs(30)).toBe(3_600_000);

    await enqueue(db, 'job_card', 'bad', {}, NOW); await enqueue(db, 'invoice', 'good', {}, NOW);
    const send = jest.fn(async (it: { rowId: string }) => {
      if (it.rowId === 'bad')
        throw new PermanentError('400');
    });
    expect(await flush(db, send, { now: NOW })).toMatchObject({ sent: 1, parked: 1, left: 0 });
    const parked = await db.getFirstAsync<{ attempts: number; last_error: string }>('select attempts, last_error from outbox');
    expect(parked).toEqual({ attempts: MAX_ATTEMPTS, last_error: '400' });
  });
});

describe('bills', () => {
  it('fY series on the phone, bill = sum of items, one bill per job, queued for sync', async () => {
    const db = await freshDb();
    const card = parseTranscript('split AC gas refill 2500, capacitor 450, total 3000, customer Hari 9100099999');
    const { jobId } = await saveJob(db, card, { techId: 't1', newId, now: NOW });
    const { meta, totals } = await makeBill(db, jobId, tech, { now: NOW, newId });
    expect(meta.number).toBe('JC/26-27/0001'); expect(totals.payable).toBe(295000); // not the spoken 3000
    expect(meta.customer).toMatchObject({ name: 'Hari', phone: '9100099999' });
    await expect(makeBill(db, jobId, tech, { now: NOW, newId })).rejects.toThrow(/already billed as JC\/26-27\/0001/);
    const inv = await db.getFirstAsync<{ payload: string }>(`select payload from outbox where kind = 'invoice'`);
    expect(JSON.parse(inv!.payload)).toMatchObject({ number: 'JC/26-27/0001', fy: '26-27', payable_paise: 295000, kind: 'unregistered', cgst_paise: 0 });
  });

  it('refuses a bill with an unpriced item', async () => {
    const db = await freshDb();
    const { jobId } = await saveJob(db, parseTranscript('capacitor, gas refill 2500'), { techId: 't1', newId, now: NOW });
    await expect(makeBill(db, jobId, tech, { now: NOW, newId })).rejects.toThrow(/needs a price: Capacitor/);
  });

  it('new series on 1 April (IST)', async () => {
    const db = await freshDb();
    expect(await nextInvoiceNo(db, '2027-03-31')).toBe('JC/26-27/0001');
    expect(await nextInvoiceNo(db, '2027-03-31')).toBe('JC/26-27/0002');
    expect(await nextInvoiceNo(db, istDate(Date.parse('2027-03-31T19:00:00Z')))).toBe('JC/27-28/0001');
  });

  it('shares the bilingual bill as a PDF', async () => {
    const db = await freshDb();
    const { jobId } = await saveJob(db, parseTranscript('gas refill 2500, customer Sita 9000033333'), { techId: 't1', newId, now: NOW });
    const { meta, totals } = await makeBill(db, jobId, tech, { now: NOW, newId });
    expect(await shareBill(meta, totals)).toEqual({ uri: 'file:///cache/bill.pdf', shared: true });
    const html = (Print.printToFileAsync as jest.Mock).mock.calls[0][0].html as string;
    expect(html).toMatch(/Bill of Supply/); expect(html).toMatch(/మొత్తం/); expect(html).not.toMatch(/CGST/);
    expect(Sharing.shareAsync).toHaveBeenCalledWith('file:///cache/bill.pdf', expect.objectContaining({ mimeType: 'application/pdf' }));
  });
});

describe('dictation', () => {
  it('telugu by default, on-device when offline, audio always kept', async () => {
    expect(dictationOptions('te', false)).toMatchObject({ lang: 'te-IN', requiresOnDeviceRecognition: true, recordingOptions: { persist: true } });
    expect(dictationOptions('hi', true)).toMatchObject({ lang: 'hi-IN', requiresOnDeviceRecognition: false });
    expect(await startDictation('te', false)).toBe(true);
    expect(Speech.start).toHaveBeenCalledWith(expect.objectContaining({ lang: 'te-IN' }));
    (Speech.requestPermissionsAsync as jest.Mock).mockResolvedValueOnce({ granted: false });
    expect(await startDictation('te', true)).toBe(false);
  });
});

describe('sync to Supabase', () => {
  const jwt = `x.${btoa(JSON.stringify({ sub: 't1' }))}.y`;
  it('upserts rows by id with the user token; 4xx is permanent, 5xx retries', async () => {
    const calls: Array<{ url: string; init: any }> = [];
    let status = 201;
    const fetchFn = jest.fn(async (url: string, init?: any) => { calls.push({ url, init }); return { ok: status < 300, status, blob: async () => 'AUDIO' } as any; }) as unknown as typeof fetch;
    const send = supabaseSender({ url: 'https://p.supabase.co', anonKey: 'anon', getToken: async () => jwt, fetchFn });
    await send({ kind: 'job_card', rowId: 'j1', payload: { id: 'j1' } });
    expect(calls[0].url).toBe('https://p.supabase.co/rest/v1/job_cards?on_conflict=id');
    expect(calls[0].init.headers).toMatchObject({ Authorization: `Bearer ${jwt}`, Prefer: 'resolution=merge-duplicates,return=minimal' });
    await send({ kind: 'invoice', rowId: 'i1', payload: { id: 'i1' } });
    expect(calls[1].init.headers.Prefer).toMatch(/ignore-duplicates/); // issued invoices are never overwritten
    await send({ kind: 'voice', rowId: 'j1', payload: { uri: 'file:///n.wav' } });
    expect(calls[3].url).toBe('https://p.supabase.co/storage/v1/object/voice/t1/j1.wav');
    status = 400; await expect(send({ kind: 'customer', rowId: 'c', payload: {} })).rejects.toBeInstanceOf(PermanentError);
    status = 503; await expect(send({ kind: 'customer', rowId: 'c', payload: {} })).rejects.not.toBeInstanceOf(PermanentError);
    const out = supabaseSender({ url: 'u', anonKey: 'a', getToken: async () => null, fetchFn });
    await expect(out({ kind: 'customer', rowId: 'c', payload: {} })).rejects.toThrow(/not signed in/);
  });
});
