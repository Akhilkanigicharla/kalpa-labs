// Free off-device backup (research gap 7): one JSON file with every saved session, which the user keeps
// wherever they like. Restoring the same file twice is safe because session ids are kept (put = upsert).
import { COLORS, type GroupColor, type SavedGroup, type SavedTab, type SavedWindow, type Session, restorable } from "./model";

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
  let tabs = 0, groups = 0, skipped = 0;
  const sessions: Session[] = [];
  for (const r of data.sessions as Record<string, unknown>[]) {
    if (!r || typeof r !== "object" || !str(r.id)) { skipped++; continue; }
    const windows: SavedWindow[] = [];
    for (const w of (Array.isArray(r.windows) ? r.windows : []) as Record<string, unknown>[]) {
      const ts: SavedTab[] = [];
      for (const t of (Array.isArray(w?.tabs) ? w.tabs : []) as Record<string, unknown>[]) {
        const url = str(t?.url);
        if (!restorable(url)) { skipped++; continue; }
        const tab: SavedTab = { url, title: str(t.title) || url };
        if (t.pinned === true) tab.pinned = true;
        if (typeof t.groupKey === "string") tab.groupKey = t.groupKey; else if (t.groupKey === null) tab.groupKey = null;
        ts.push(tab);
      }
      const gs: SavedGroup[] = ((Array.isArray(w?.groups) ? w.groups : []) as Record<string, unknown>[])
        .filter((g) => g && typeof g.key === "string")
        .map((g) => ({ key: g.key as string, title: str(g.title), color: (COLORS.includes(g.color as GroupColor) ? g.color : "grey") as GroupColor, collapsed: g.collapsed === true }));
      if (!ts.length) continue;
      tabs += ts.length; groups += gs.length;
      const win: SavedWindow = { tabs: ts, groups: gs };
      if (w.focused === true) win.focused = true;
      windows.push(win);
    }
    if (!windows.length) continue;
    const s: Session = { id: str(r.id), name: str(r.name) || "Restored session", createdAt: Number(r.createdAt) || Date.now(),
      kind: KINDS.includes(r.kind as Session["kind"]) ? (r.kind as Session["kind"]) : "import", windows };
    if (typeof r.source === "string") s.source = r.source;
    sessions.push(s);
  }
  return { sessions, tabs, groups, skipped };
}
