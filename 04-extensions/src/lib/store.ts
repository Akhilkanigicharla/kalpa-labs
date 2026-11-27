// Sessions live in IndexedDB (not chrome.storage, whose quota and wipe-on-update stories sank OneTab users).
import { openDB, type IDBPDatabase } from "idb";
import type { Session } from "./model";

export const LIMITS = { freeAutoSnapshots: 3, proAutoDays: 90 }; // pending CEO approval (E7)
export const TRASH_DAYS = 7;   // A231: "Delete" moves a session to Recently deleted for this long
export type Trashed = Session & { deletedAt: number };

let dbp: Promise<IDBPDatabase> | null = null;
function db() {
  dbp ??= openDB("tab-lifeboat", 2, { upgrade(d, old) {
    if (old < 1) { const s = d.createObjectStore("sessions", { keyPath: "id" }); s.createIndex("createdAt", "createdAt"); s.createIndex("kind", "kind"); }
    if (old < 2) d.createObjectStore("trash", { keyPath: "id" });   // v2 (A231): sessions kept 7 days after Delete
  } });
  return dbp;
}
export async function _clearForTests() { const d = await db(); await d.clear("sessions"); await d.clear("trash"); }

/** Data read back from IndexedDB is checked before use: a record without an id or a windows list (old bug, manual edit) is ignored. */
const valid = (s: unknown): s is Session => !!s && typeof (s as Session).id === "string" && Array.isArray((s as Session).windows)
  && (s as Session).windows.every((w) => !!w && Array.isArray(w.tabs) && Array.isArray(w.groups ?? []));
export async function putSession(s: Session) { await (await db()).put("sessions", s); return s; }
export async function getSession(id: string): Promise<Session | undefined> { const s = await (await db()).get("sessions", id); return valid(s) ? s : undefined; }
export async function listSessions(): Promise<Session[]> {
  const all = (await (await db()).getAllFromIndex("sessions", "createdAt")) as unknown[];
  return all.filter(valid).reverse(); // newest first
}

/** v0.3 edits: one transaction writes every changed session first, then moves emptied/merged ones to Recently deleted.
 *  Either all of it happens or none of it (IndexedDB aborts the whole transaction on any error). */
export async function applyEdit(puts: Session[], trashIds: string[] = [], now = Date.now()) {
  const tx = (await db()).transaction(["sessions", "trash"], "readwrite");
  const ss = tx.objectStore("sessions"), tr = tx.objectStore("trash");
  await all(tx, async () => {
    for (const s of puts) await ss.put(s);
    for (const id of trashIds) { const s = (await ss.get(id)) as Session | undefined; if (s) { await tr.put({ ...s, deletedAt: now }); await ss.delete(id); } }
  });
}
/** A request can throw before IndexedDB sees it (bad key, uncloneable value); that does NOT abort the transaction by
 *  itself, so abort it here: none of the earlier writes are kept. */
async function all(tx: { abort(): void; done: Promise<void> }, work: () => Promise<void>) {
  try { await work(); } catch (e) { try { tx.abort(); } catch { /* already finished */ } await tx.done.catch(() => {}); throw e; }
  await tx.done;
}
/** Undo of applyEdit: put the old copies back and take the trashed ones out of Recently deleted, in one transaction. */
export async function undoEdit(prev: Session[], trashIds: string[] = []) {
  const tx = (await db()).transaction(["sessions", "trash"], "readwrite");
  const ss = tx.objectStore("sessions"), tr = tx.objectStore("trash");
  await all(tx, async () => { for (const s of prev) await ss.put(s); for (const id of trashIds) await tr.delete(id); });
}
export async function deleteSession(id: string) { await (await db()).delete("sessions", id); }

/** Keep manual and imported sessions forever; prune automatic snapshots by plan. */
export async function pruneAuto(plan: "free" | "pro", now = Date.now(), keep: string[] = []) {
  // keep = the snapshot the restart banner points at: it must outlive the new snapshots taken after a crash
  const autos = (await listSessions()).filter((s) => s.kind === "auto" && !keep.includes(s.id));
  const drop = plan === "free" ? autos.slice(LIMITS.freeAutoSnapshots) : autos.filter((s) => now - s.createdAt > LIMITS.proAutoDays * 864e5);
  for (const s of drop) await deleteSession(s.id);
  return drop.length;
}

/** A231: Delete moves the session to "trash" in one transaction, so it is never in both lists or in neither. */
export async function trashSession(id: string, now = Date.now()) {
  const tx = (await db()).transaction(["sessions", "trash"], "readwrite");
  const s = (await tx.objectStore("sessions").get(id)) as Session | undefined;
  if (s) { await tx.objectStore("trash").put({ ...s, deletedAt: now }); await tx.objectStore("sessions").delete(id); }
  await tx.done; return !!s;
}
export async function undeleteSession(id: string) {
  const tx = (await db()).transaction(["sessions", "trash"], "readwrite");
  const t = (await tx.objectStore("trash").get(id)) as Trashed | undefined;
  if (t) { const { deletedAt: _, ...s } = t; await tx.objectStore("sessions").put(s); await tx.objectStore("trash").delete(id); }
  await tx.done; return !!t;
}
export async function deleteForever(id: string) {
  const d = await db(); const had = !!(await d.get("trash", id)); await d.delete("trash", id); return had;
}
/** Drops sessions deleted more than TRASH_DAYS ago; returns how many went. */
export async function purgeTrash(now = Date.now()) {
  const d = await db(); let n = 0;
  for (const t of (await d.getAll("trash")) as Trashed[]) if (now - t.deletedAt > TRASH_DAYS * 864e5) { await d.delete("trash", t.id); n++; }
  return n;
}
/** Recently deleted, newest first (expired ones are purged first). */
export async function listTrash(now = Date.now()): Promise<Trashed[]> {
  await purgeTrash(now);
  return ((await (await db()).getAll("trash")) as Trashed[]).sort((a, b) => b.deletedAt - a.deletedAt);
}
