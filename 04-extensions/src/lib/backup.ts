// Free off-device backup (research gap 7): one JSON file with every saved session, which the user keeps
// wherever they like. Restoring the same file twice is safe because session ids are kept (put = upsert).
import { CAPS, COLORS, clip, type GroupColor, type SavedGroup, type SavedTab, type SavedWindow, type Session, safeUrl } from "./model";

export const BACKUP_FORMAT = "tab-lifeboat-backup";
export const BACKUP_VERSION = 1;
export interface Backup { format: typeof BACKUP_FORMAT; version: number; exportedAt: string; sessions: Session[] }
export interface BackupPreview { sessions: Session[]; tabs: number; groups: number; skipped: number }

export function toBackup(sessions: Session[], now = Date.now()): Backup {
  return { format: BACKUP_FORMAT, version: BACKUP_VERSION, exportedAt: new Date(now).toISOString(), sessions };
}

/** tab-lifeboat-backup-2026-10-17.json, dated in IST (the founder's and first users' zone). */
export function backupFileName(now = Date.now()) {
  return `${BACKUP_FORMAT}-${new Date(now + 330 * 60_000).toISOString().slice(0, 10)}.json`;
}

const str = (v: unknown, d = "") => (typeof v === "string" ? v : d);
const KINDS: Session["kind"][] = ["manual", "auto", "import"];

/** Read a backup file. Throws a plain-English error for anything that isn't ours. */
export function parseBackup(text: string): BackupPreview {
  let data: { format?: unknown; version?: unknown; sessions?: unknown };
  try { data = JSON.parse(text); } catch { throw new Error("This file is not a Tab Lifeboat backup."); }
  if (!data || data.format !== BACKUP_FORMAT || !Array.isArray(data.sessions)) throw new Error("This file is not a Tab Lifeboat backup.");
  if (typeof data.version !== "number" || data.version > BACKUP_VERSION) throw new Error("This backup was made by a newer version of Tab Lifeboat. Update the extension first.");
  if (data.sessions.length > CAPS.sessions) throw new Error(`This backup has ${data.sessions.length.toLocaleString("en-US")} sessions; Tab Lifeboat restores up to ${CAPS.sessions.toLocaleString("en-US")} at a time.`);
  let tabs = 0, groups = 0, skipped = 0;
  const sessions: Session[] = [];
  for (const r of data.sessions as Record<string, unknown>[]) {
    if (!r || typeof r !== "object" || !str(r.id)) { skipped++; continue; }
    const windows: SavedWindow[] = [];
    for (const w of (Array.isArray(r.windows) ? r.windows : []) as Record<string, unknown>[]) {
      const ts: SavedTab[] = [];
      for (const t of (Array.isArray(w?.tabs) ? w.tabs : []) as Record<string, unknown>[]) {
        const url = safeUrl(t?.url);
        if (!url) { skipped++; continue; }
        if (++tabs > CAPS.tabs) throw new Error(`This backup has more than ${CAPS.tabs.toLocaleString("en-US")} tabs; Tab Lifeboat restores up to that many at a time.`);
        const tab: SavedTab = { url, title: clip(t.title, CAPS.title) || url };
        if (t.pinned === true) tab.pinned = true;
        if (typeof t.groupKey === "string") tab.groupKey = t.groupKey; else if (t.groupKey === null) tab.groupKey = null;
        ts.push(tab);
      }
      const gs: SavedGroup[] = ((Array.isArray(w?.groups) ? w.groups : []) as Record<string, unknown>[])
        .filter((g) => g && typeof g.key === "string")
        .map((g) => ({ key: g.key as string, title: clip(g.title, CAPS.group), color: (COLORS.includes(g.color as GroupColor) ? g.color : "grey") as GroupColor, collapsed: g.collapsed === true }));
      if (!ts.length) continue;
      groups += gs.length;
      const win: SavedWindow = { tabs: ts, groups: gs };
      if (w.focused === true) win.focused = true;
      windows.push(win);
    }
    if (!windows.length) continue;
    const s: Session = { id: str(r.id), name: clip(r.name, CAPS.name) || "Restored session", createdAt: Number(r.createdAt) || Date.now(),
      kind: KINDS.includes(r.kind as Session["kind"]) ? (r.kind as Session["kind"]) : "import", windows };
    if (typeof r.source === "string") s.source = r.source;
    if (Number.isSafeInteger(r.updatedAt) && (r.updatedAt as number) > 0) s.updatedAt = r.updatedAt as number;
    sessions.push(s);
  }
  return { sessions, tabs, groups, skipped };
}

// Compare what a person sees (name, windows, tabs, groups), not key order or extra fields from older versions.
const shape = (x: Session) => JSON.stringify([x.name, x.windows.map((w) => [w.tabs.map((t) => [t.url, t.title, !!t.pinned, t.groupKey ?? null]),
  (w.groups ?? []).map((g) => [g.key, g.title, g.color, !!g.collapsed])])]);
// The stored copy goes through the same cleaning a backup file does (skipped chrome:// tabs, empty titles), so an
// unchanged session always matches its own backup.
const clean = (x: Session) => parseBackup(JSON.stringify(toBackup([x]))).sessions[0];
const sameTabs = (stored: Session, b: Session) => { const c = clean(stored); return !!c && shape(c) === shape(b); };
const when = (s: Session) => s.updatedAt ?? s.createdAt;

/** What to write when restoring one backup session next to what is already stored (A357: a restore never eats an edit).
 *  Same id and same tabs: nothing. Backup strictly newer: it replaces the stored copy. Otherwise both are kept:
 *  the backup copy gets a new id and a "(from backup 12 Nov)" name. */
export function restorePlan(stored: Session | undefined, b: Session, newId: () => string): Session[] {
  if (!stored) return [b];
  if (sameTabs(stored, b)) return [];
  if (when(b) > when(stored)) return [b];
  const day = new Date(when(b) + 330 * 60_000).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  return [{ ...b, id: newId(), name: `${b.name} (from backup ${day})`.slice(0, CAPS.name) }];
}
