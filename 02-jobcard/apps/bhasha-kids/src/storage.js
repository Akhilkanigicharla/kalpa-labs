// Device-only storage. localStorage can throw (private mode, quota, disabled
// cookies), so every call is wrapped and falls back to memory for the session.
const KEY = 'kalpa-bhasha-kids-v1';

export function makeStore(backend) {
  const mem = new Map();
  let ok = true;
  const get = () => { try { return backend?.getItem(KEY) ?? null; } catch { ok = false; return null; } };
  return {
    load() {
      const raw = mem.get(KEY) ?? get() ?? null;
      if (!raw) return null;
      try { return JSON.parse(raw); } catch { return null; }
    },
    save(obj) {
      const s = JSON.stringify(obj);
      mem.set(KEY, s);
      try { backend?.setItem(KEY, s); return true; } catch { ok = false; return false; }
    },
    clear() {
      mem.delete(KEY);
      try { backend?.removeItem(KEY); } catch { ok = false; }
    },
    get persistent() { return ok && !!backend; },
  };
}

export function browserBackend() {
  try { return globalThis.localStorage || null; } catch { return null; }
}
