// Supabase store for ingest.js, over PostgREST. Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
// as secrets (Akhil sets them in the Supabase/Netlify dashboard; never in the repo).
export function supabaseStore({ url, serviceKey, fetchFn = fetch, cacheMs = 60_000 }) {
  if (!url || !serviceKey) throw new Error('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set');
  const base = url.replace(/\/$/, '') + '/rest/v1';
  const headers = { apikey: serviceKey, authorization: `Bearer ${serviceKey}`, 'content-type': 'application/json' };
  const cache = new Map();   // key hash -> {tenant, until}; short so a revoked key stops within a minute
  return {
    async tenantForKeyHash(hex) {
      if (!/^[0-9a-f]{64}$/.test(hex)) return null;
      const hit = cache.get(hex);
      if (hit && hit.until > Date.now()) return hit.tenant;
      const r = await fetchFn(`${base}/api_key?select=tenant_id&key_hash=eq.${hex}&revoked_at=is.null&limit=1`, { headers, signal: AbortSignal.timeout(5000) });
      if (!r.ok) throw new Error(`key lookup ${r.status}`);
      const tenant = (await r.json())[0]?.tenant_id ?? null;
      cache.set(hex, { tenant, until: Date.now() + cacheMs });
      return tenant;
    },
    async insertEvents(rows) {
      // event_id is unique per tenant: a client's retry of the same events is ignored, never counted twice
      const r = await fetchFn(`${base}/usage_event?on_conflict=tenant_id,event_id`, {
        method: 'POST', headers: { ...headers, prefer: 'resolution=ignore-duplicates,return=minimal' }, body: JSON.stringify(rows),
        signal: AbortSignal.timeout(8000) });
      if (!r.ok) throw new Error(`insert ${r.status}`);
    },
  };
}
