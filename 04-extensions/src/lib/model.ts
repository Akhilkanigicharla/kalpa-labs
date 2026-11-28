// Tab Lifeboat data model. A session is a snapshot of windows, tabs and tab groups.
export type GroupColor = "grey" | "blue" | "red" | "yellow" | "green" | "pink" | "purple" | "cyan" | "orange";
export interface SavedTab { url: string; title: string; pinned?: boolean; groupKey?: string | null; favIconUrl?: string }
export interface SavedGroup { key: string; title: string; color: GroupColor; collapsed: boolean }
export interface SavedWindow { tabs: SavedTab[]; groups: SavedGroup[]; focused?: boolean; incognito?: false }
export interface Session {
  id: string; name: string; createdAt: number; kind: "manual" | "auto" | "import";
  source?: string; windows: SavedWindow[];
  /** v0.3: set on every hand edit, so a second open page (or an old backup) can't silently overwrite it. */
  updatedAt?: number;
}
export const COLORS: GroupColor[] = ["grey", "blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];

/** Pages Chrome won't let an extension reopen, or that are pointless to save. */
export function restorable(url: string): boolean {
  // Web pages only. file:// is refused so an imported list can't make the browser open local files;
  // chrome://, about:, data:, javascript: and ftp (dropped by Chrome) are skipped on restore.
  return safeUrl(url) !== null;
}

/** Limits from 04-extensions/research/v03-hardening-2026-11-27.md rule 3. */
export const CAPS = { fileBytes: 20 * 1024 * 1024, tabs: 20_000, sessions: 1_000, depth: 32, url: 8192, title: 1000, name: 200, group: 100, askAbove: 100 };

/** The one URL gate (hardening rule 2): ≤ 8,192 chars, parses, and is http: or https:. Returns the address as the user
 *  saved it (not re-encoded, so Telugu paths and missing trailing slashes are kept), else null. */
export function safeUrl(s: unknown): string | null {
  if (typeof s !== "string" || s.length > CAPS.url || !/^https?:\/\//i.test(s)) return null;
  try { const u = new URL(s); return u.protocol === "http:" || u.protocol === "https:" ? s : null; } catch { return null; }
}
/** Single-line text, capped (titles 1,000, names 200, group titles 100). */
export const clip = (s: unknown, max: number) => (typeof s === "string" ? s.replace(/\s+/g, " ").trim().slice(0, max) : "");

/** "Already open" check: the exact address, only a trailing slash ignored. #hash counts (web apps route with it). */
export function sameKey(url: string): string {
  const h = url; const i = h.search(/[?#]/); const path = i < 0 ? h : h.slice(0, i);
  return path.replace(/\/$/, "") + (i < 0 ? "" : h.slice(i));
}

export function countTabs(s: Pick<Session, "windows">): { tabs: number; groups: number; windows: number } {
  return { tabs: s.windows.reduce((n, w) => n + w.tabs.length, 0), groups: s.windows.reduce((n, w) => n + w.groups.length, 0), windows: s.windows.length };
}

export const newId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
