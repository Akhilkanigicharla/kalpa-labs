// Tab Lifeboat tools: search every saved tab (Free), cleanup + timeline + daily backup (Pro). Pure functions, tested.
import { restorable, type Session, sameKey } from "./model";

const TRACKING = /^(utm_\w+|fbclid|gclid|mc_eid|mc_cid|igshid|ref_src)$/i;

/** Same page = same normalised URL: no #hash, no tracking params, no trailing slash, lower-case host. */
export function normUrl(url: string): string {
  try {
    const u = new URL(url);
    u.hash = "";
    for (const k of [...u.searchParams.keys()]) if (TRACKING.test(k)) u.searchParams.delete(k);
    let s = u.toString();
    if (u.pathname === "/" && !u.search) s = s.replace(/\/$/, "");
    return s.replace(/\/(\?|$)/, "$1");
  } catch {
    return url;
  }
}

export interface Hit { sessionId: string; sessionName: string; createdAt: number; url: string; title: string; alsoIn: number }

/** Every word must appear in the title or URL. Newest session wins; alsoIn = how many older sessions hold it too. */
export function searchTabs(sessions: Session[], q: string, limit = 100): Hit[] {
  const words = q.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const byUrl = new Map<string, Hit>();
  for (const s of [...sessions].sort((a, b) => b.createdAt - a.createdAt)) {
    const seenHere = new Set<string>();
    for (const w of s.windows) for (const t of w.tabs) {
      const hay = `${t.title} ${t.url}`.toLowerCase();
      if (!words.every((x) => hay.includes(x))) continue;
      const key = normUrl(t.url);
      if (seenHere.has(key)) continue;
      seenHere.add(key);
      const old = byUrl.get(key);
      if (old) old.alsoIn++;
      else byUrl.set(key, { sessionId: s.id, sessionName: s.name, createdAt: s.createdAt, url: t.url, title: t.title, alsoIn: 0 });
    }
  }
  return [...byUrl.values()].slice(0, limit);
}

export interface OpenTab { id: number; url: string; pinned: boolean; active: boolean; audible: boolean; lastAccessed?: number }

/** Tab ids to close so each page is open once. A pinned copy is kept if there is one, else the first; pinned tabs never close. */
export function findDuplicates(tabs: OpenTab[]): number[] {
  const groups = new Map<string, OpenTab[]>();
  for (const t of tabs) { const k = normUrl(t.url); groups.set(k, [...(groups.get(k) ?? []), t]); }
  const close: number[] = [];
  for (const g of groups.values()) {
    if (g.length < 2) continue;
    const keep = g.find((t) => t.pinned) ?? g[0]!;
    for (const t of g) if (t !== keep && !t.pinned) close.push(t.id);
  }
  return close.sort((x, y) => x - y);
}

/** Tabs not looked at for `days` days. Skips pinned, active and playing tabs, and tabs without lastAccessed. */
export function findStale(tabs: OpenTab[], days: number, now = Date.now()): number[] {
  return tabs.filter((t) => !t.pinned && !t.active && !t.audible && typeof t.lastAccessed === "number" && now - t.lastAccessed > days * 864e5).map((t) => t.id);
}

export interface Timeline { firstSeen: number; lastSeen: number; snapshots: number; lastSessionId: string; goneSince: number | null }

/** When a page first and last appeared in your snapshots, and when it vanished (the next snapshot without it). */
export function tabTimeline(sessions: Session[], url: string): Timeline | null {
  const k = normUrl(url);
  const ordered = [...sessions].sort((a, b) => a.createdAt - b.createdAt);
  const has = ordered.map((s) => s.windows.some((w) => w.tabs.some((t) => normUrl(t.url) === k)));
  const idx = has.map((h, i) => (h ? i : -1)).filter((i) => i >= 0);
  if (!idx.length) return null;
  const last = idx[idx.length - 1]!;
  return { firstSeen: ordered[idx[0]!]!.createdAt, lastSeen: ordered[last]!.createdAt, snapshots: idx.length,
    lastSessionId: ordered[last]!.id, goneSince: last < ordered.length - 1 ? ordered[last + 1]!.createdAt : null };
}

/** Pro daily backup file: due if none yet or the last one is 20+ hours old. */
export function backupDue(lastAt: number | null, now = Date.now()): boolean {
  return lastAt === null || now - lastAt >= 20 * 36e5;
}

/** The one honest upgrade message (BUSINESS.md rule 2): after a big import, free users only, at most once a week. */
export function upgradeNudge(o: { plan: "free" | "pro"; importedTabs: number; lastNudge: number | null; now: number }): string | null {
  if (o.plan !== "free" || o.importedTabs < 100) return null;
  if (o.lastNudge !== null && o.now - o.lastNudge < 7 * 864e5) return null;
  return `You just moved ${o.importedTabs.toLocaleString("en-US")} tabs. Pro keeps a snapshot every 5 minutes for 90 days and a daily backup file, so they're never lost again.`;
}

/** Free reminder to download the backup file. Local data can be wiped when Chrome "repairs" or removes an extension
 *  (Session Buddy's own data-loss page describes this), so the file is the only copy outside the browser.
 *  Returns null when no reminder is needed. Daily Pro backups count as backups too. */
export function backupReminder(o: { lastFileAt: number | null; sessions: number; now?: number }): string | null {
  if (o.sessions < 1) return null;
  if (!o.lastFileAt) return "No backup file yet. It keeps a copy of your tabs outside Chrome.";
  const days = Math.floor(((o.now ?? Date.now()) - o.lastFileAt) / 86_400_000);
  return days >= 7 ? `Last backup file was ${days} days ago.` : null;
}

/** "today", "yesterday", "5 days ago": for the backup card. */
export function daysAgo(at: number, now = Date.now()): string {
  const d = Math.floor((now - at) / 86_400_000);
  return d <= 0 ? "today" : d === 1 ? "yesterday" : `${d.toLocaleString("en-US")} days ago`;
}

// ---- v0.3 Group A: safety

/** "21:10" today, "26 Nov 21:10" on another day: for the stale-snapshot warning and the restart banner. */
export function clock(at: number, now = Date.now()): string {
  const d = new Date(at), t = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return d.toDateString() === new Date(now).toDateString() ? t : `${d.getDate()} ${d.toLocaleString("en-GB", { month: "short" })} ${t}`;
}

/** Auto-save is stale when it has not run for 3 intervals while the browser has been running (time the browser was
 *  closed doesn't count: the clock starts again at bootAt). Returns the time it last ran (or bootAt), or null when fine. */
export function staleSince(o: { lastRun: number | null; bootAt: number; now: number; everyMin: number }): number | null {
  const ref = Math.max(o.lastRun ?? 0, o.bootAt);
  return o.now - ref > 3 * o.everyMin * 60_000 ? (o.lastRun ?? o.bootAt) : null;
}

export type BannerKind = "restart" | "update" | "chrome-update";
export interface Banner { kind: BannerKind; at: number; id: string }
export const BANNER_DAYS = 3;

/** The session the "your tabs are safe" banner points at: the newest automatic snapshot taken before the restart
 *  (else the newest session of any kind). null when there is nothing worth restoring. */
export function bannerSession(sessions: Session[], at: number): Session | null {
  const before = sessions.filter((s) => s.createdAt <= at && s.windows.some((w) => w.tabs.length)).sort((a, b) => b.createdAt - a.createdAt);
  return before.find((s) => s.kind === "auto") ?? before[0] ?? null;
}

/** Tabs of a session that are not open right now (exact address, trailing slash ignored). */
export function missingTabs(s: Session, openUrls: Iterable<string>): number {
  const open = new Set([...openUrls].map(sameKey));
  return s.windows.reduce((n, w) => n + w.tabs.filter((t) => restorable(t.url) && !open.has(sameKey(t.url))).length, 0);
}
