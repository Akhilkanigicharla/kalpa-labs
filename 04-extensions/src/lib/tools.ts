// Tab Lifeboat tools: search every saved tab (Free), cleanup + timeline + daily backup (Pro). Pure functions, tested.
import type { Session } from "./model";

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
