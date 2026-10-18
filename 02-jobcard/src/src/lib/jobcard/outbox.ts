// Outbox: every change is written locally first, then sent when there is signal.
// Items go out strictly in order (a customer before its job card before its invoice). The first failure
// stops the run and is retried later with backoff, so nothing is sent out of order or twice in parallel.
import type { LocalDb } from './db';

export type OutboxKind = 'customer' | 'job_card' | 'invoice' | 'voice';
export type OutboxItem = { id: number; kind: OutboxKind; row_id: string; payload: string; attempts: number; next_at: number; last_error: string | null };
export type Sender = (item: { kind: OutboxKind; rowId: string; payload: Record<string, unknown> }) => Promise<void>;

/** Error that will never succeed on retry (e.g. 400 from the server); the item is parked, not retried forever. */
export class PermanentError extends Error {}

const BASE_MS = 30_000;
const MAX_MS = 60 * 60_000;
export const MAX_ATTEMPTS = 20;
export const backoffMs = (attempts: number) => Math.min(BASE_MS * 2 ** Math.max(0, attempts - 1), MAX_MS);

export async function enqueue(db: LocalDb, kind: OutboxKind, rowId: string, payload: Record<string, unknown>, now = Date.now()) {
  await db.runAsync('insert into outbox (kind, row_id, payload, created_at) values (?, ?, ?, ?)', kind, rowId, JSON.stringify(payload), now);
}

export async function pendingCount(db: LocalDb): Promise<number> {
  const r = await db.getFirstAsync<{ n: number }>('select count(*) as n from outbox where attempts < ?', MAX_ATTEMPTS);
  return r ? r.n : 0;
}

export async function flush(db: LocalDb, send: Sender, { now = Date.now(), online = true } = {}) {
  const result = { sent: 0, failed: 0, parked: 0, left: 0 };
  if (online) {
    const items = await db.getAllAsync<OutboxItem>('select * from outbox where attempts < ? order by id', MAX_ATTEMPTS);
    for (const it of items) {
      if (it.next_at > now)
        break; // the head is waiting out its backoff: keep order
      try {
        await send({ kind: it.kind, rowId: it.row_id, payload: JSON.parse(it.payload) });
        await db.runAsync('delete from outbox where id = ?', it.id);
        result.sent++;
      }
      catch (e) {
        const permanent = e instanceof PermanentError;
        const attempts = permanent ? MAX_ATTEMPTS : it.attempts + 1;
        await db.runAsync('update outbox set attempts = ?, next_at = ?, last_error = ? where id = ?', attempts, now + backoffMs(attempts), String((e as Error).message).slice(0, 300), it.id);
        if (permanent) { result.parked++; continue; } // a bad row must not block the rest forever
        result.failed++;
        break;
      }
    }
  }
  result.left = await pendingCount(db);
  return result;
}
