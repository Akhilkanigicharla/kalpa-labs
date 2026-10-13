// Sessions live in IndexedDB (not chrome.storage, whose quota and wipe-on-update stories sank OneTab users).
import { openDB, type IDBPDatabase } from "idb";
import type { Session } from "./model";

export const LIMITS = { freeAutoSnapshots: 3, proAutoDays: 90 }; // pending CEO approval (E7)

let dbp: Promise<IDBPDatabase> | null = null;
function db() {
  dbp ??= openDB("tab-lifeboat", 1, { upgrade(d) { const s = d.createObjectStore("sessions", { keyPath: "id" }); s.createIndex("createdAt", "createdAt"); s.createIndex("kind", "kind"); } });
  return dbp;
}
export async function _clearForTests() { await (await db()).clear("sessions"); }

export async function putSession(s: Session) { await (await db()).put("sessions", s); return s; }
export async function getSession(id: string) { return (await db()).get("sessions", id) as Promise<Session | undefined>; }
export async function listSessions(): Promise<Session[]> {
  const all = (await (await db()).getAllFromIndex("sessions", "createdAt")) as Session[];
  return all.reverse(); // newest first
}
export async function deleteSession(id: string) { await (await db()).delete("sessions", id); }

/** Keep manual and imported sessions forever; prune automatic snapshots by plan. */
export async function pruneAuto(plan: "free" | "pro", now = Date.now()) {
  const autos = (await listSessions()).filter((s) => s.kind === "auto");
  const drop = plan === "free" ? autos.slice(LIMITS.freeAutoSnapshots) : autos.filter((s) => now - s.createdAt > LIMITS.proAutoDays * 864e5);
  for (const s of drop) await deleteSession(s.id);
  return drop.length;
}
