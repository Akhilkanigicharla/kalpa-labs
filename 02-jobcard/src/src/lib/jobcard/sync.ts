// Sends outbox items to Supabase (REST + Storage) as the signed-in technician; RLS on auth.uid() guards every row.
// Upserts by the phone-made id, so a retry after a lost reply never makes a duplicate.
import type { Sender } from './outbox';
import { PermanentError } from './outbox';

const TABLE = { customer: 'customers', job_card: 'job_cards', invoice: 'invoices' } as const;

export function supabaseSender({ url, anonKey, getToken, fetchFn = fetch }: { url: string; anonKey: string; getToken: () => Promise<string | null>; fetchFn?: typeof fetch }): Sender {
  return async ({ kind, rowId, payload }) => {
    const token = await getToken();
    if (!token)
      throw new Error('not signed in');
    const headers = { apikey: anonKey, Authorization: `Bearer ${token}` };
    let res: Response;
    if (kind === 'voice') { // the saved note goes to the private "voice" bucket: <technician>/<job>.wav
      const audio = await (await fetchFn(String(payload.uri))).blob();
      const tech = JSON.parse(atob(token.split('.')[1] || 'e30=')).sub;
      res = await fetchFn(`${url}/storage/v1/object/voice/${tech}/${rowId}.wav`, { method: 'POST', headers: { ...headers, 'Content-Type': 'audio/wav', 'x-upsert': 'true' }, body: audio });
    }
    else {
      res = await fetchFn(`${url}/rest/v1/${TABLE[kind]}?on_conflict=id`, { method: 'POST', body: JSON.stringify(payload), headers: { ...headers, 'Content-Type': 'application/json', 'Prefer': kind === 'invoice' ? 'resolution=ignore-duplicates,return=minimal' : 'resolution=merge-duplicates,return=minimal' } });
    }
    if (res.ok)
      return;
    if (res.status >= 400 && res.status < 500 && res.status !== 401 && res.status !== 408 && res.status !== 429)
      throw new PermanentError(`${kind} ${res.status}`);
    throw new Error(`${kind} ${res.status}`);
  };
}
