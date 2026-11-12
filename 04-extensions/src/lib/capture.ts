// Capture and restore through the browser APIs (chrome.tabs / chrome.tabGroups / chrome.windows).
import { type GroupColor, type SavedWindow, type Session, newId, restorable } from "./model";

import type { browser } from "wxt/browser";

export type Br = typeof browser;

export async function captureAll(br: Br, kind: Session["kind"] = "manual", name?: string): Promise<Session> {
  const wins = await br.windows.getAll({ populate: true, windowTypes: ["normal"] });
  const windows: SavedWindow[] = [];
  for (const w of wins) {
    if (w.incognito) continue; // never store private browsing
    const wt = w.tabs ?? [];
    const groupIds = [...new Set(wt.map((t) => t.groupId).filter((g): g is number => g !== undefined && g >= 0))];
    const groups = br.tabGroups ? await Promise.all(groupIds.map((id) => br.tabGroups.get(id))) : [];
    windows.push({
      focused: w.focused,
      groups: groups.map((g: { id: number; title?: string; color: string; collapsed?: boolean }) => ({ key: String(g.id), title: g.title ?? "", color: g.color as GroupColor, collapsed: !!g.collapsed })),
      tabs: wt.filter((t) => t.url).map((t) => ({ url: t.url!, title: t.title ?? t.url!, pinned: !!t.pinned, groupKey: t.groupId !== undefined && t.groupId >= 0 ? String(t.groupId) : null })),
    });
  }
  const d = new Date();
  return { id: newId(), kind, createdAt: d.getTime(), windows, name: name ?? `${kind === "auto" ? "Auto snapshot" : "Saved"} ${stamp(d)}` };
}

/** Reopens every window of a session with pinned tabs and tab groups (title, colour, collapsed). Never closes anything.
 *  Big sessions (more than LAZY_AT tabs) open "asleep": at most LOADING tabs load at once, and each one is put to sleep
 *  (chrome.tabs.discard) after it finishes loading, so it keeps its address and title but frees memory until clicked.
 *  Reopening hundreds of tabs at once freezes or crashes the browser (a common complaint in tab-saver reviews).
 *  Tested in real Chrome: discarding a tab that is still loading crashed the browser, and discarding gives the tab a new id. */
export async function restore(br: Br, s: Session, wait = 250, canSleep = chromeMajor() >= SLEEP_FROM): Promise<{ windows: number; tabs: number; skipped: number; asleep: number }> {
  let tabs = 0, skipped = 0, asleep = 0;
  const lazy = s.windows.reduce((n, w) => n + w.tabs.filter((t) => restorable(t.url)).length, 0) > LAZY_AT;
  for (const w of s.windows) {
    const ok = w.tabs.filter((t) => restorable(t.url)); skipped += w.tabs.length - ok.length;
    const head = ok[0];
    if (!head) continue;
    const win = await br.windows.create({ url: head.url, focused: !!w.focused });
    const first = win?.tabs?.[0];
    const created: { id: number; groupKey?: string | null }[] = [];
    if (first?.id !== undefined) { created.push({ id: first.id, groupKey: head.groupKey }); if (head.pinned) await br.tabs.update(first.id, { pinned: true }); }
    const loading = new Set<Promise<void>>();
    for (const t of ok.slice(1)) {
      while (lazy && loading.size >= LOADING) await Promise.race(loading);
      const nt = await br.tabs.create({ windowId: win?.id, url: t.url, pinned: !!t.pinned, active: false });
      if (nt.id === undefined) continue;
      const c = { id: nt.id, groupKey: t.groupKey }; created.push(c);
      if (!lazy) continue;
      const job: Promise<void> = (canSleep ? sleepWhenLoaded(br, c.id, wait) : waitLoaded(br, c.id, wait)).then((newId) => { if (newId !== null) { c.id = newId; asleep++; } }).finally(() => loading.delete(job));
      loading.add(job);
    }
    await Promise.all(loading);
    tabs += created.length;
    if (br.tabGroups) for (const g of w.groups) {
      const ids = created.filter((c) => c.groupKey === g.key).map((c) => c.id);
      if (!ids.length) continue;
      const gid = await br.tabs.group({ tabIds: ids as [number, ...number[]], createProperties: { windowId: win?.id } });
      await br.tabGroups.update(gid, { title: g.title, color: g.color, collapsed: g.collapsed });
    }
  }
  return { windows: s.windows.length, tabs, skipped, asleep };
}

/** Tested 12 Nov 2026: discarding a second tab crashed Chrome 153 (SIGSEGV, same machine) and worked on Chrome 156
 *  (here and on GitHub Actions). Older Chrome still gets the gentle restore (6 loading at a time), just without sleep. */
export const SLEEP_FROM = 156;
export function chromeMajor(ua = globalThis.navigator?.userAgent ?? ""): number {
  const m = /Chrom(?:e|ium)\/(\d+)/.exec(ua);
  return m ? Number(m[1]) : 0;
}

export const LAZY_AT = 15;   // sessions with more tabs than this open asleep
export const LOADING = 6;    // tabs loading at the same time during a big restore

/** Gentle restore without sleep: wait until the tab has loaded (up to ~15 s) so only a few load at once. Always null. */
async function waitLoaded(br: Br, id: number, wait: number): Promise<null> {
  try { for (let i = 0; i < 60; i++) { if ((await br.tabs.get(id)).status === "complete") break; await new Promise((r) => setTimeout(r, wait)); } } catch { /* closed */ }
  return null;
}

/** Wait until the tab has finished loading (up to ~15 s), then discard it. Returns its new id, or null if it stays awake
 *  (still loading, closed or clicked by the user, or the browser refused). Never discards a loading tab: that crashed Chrome. */
async function sleepWhenLoaded(br: Br, id: number, wait: number): Promise<number | null> {
  try {
    for (let i = 0; i < 60; i++) {
      const t = await br.tabs.get(id);
      if (t.active) return null;
      if (t.status === "complete") { const d = await br.tabs.discard(id); return d?.id ?? null; }
      await new Promise((r) => setTimeout(r, wait));
    }
  } catch { /* tab closed by the user or discard refused: it simply stays loaded */ }
  return null;
}

/** "17 Oct, 8:46 pm": short, unambiguous for Indian and UK/US readers alike (no 10/17 vs 17/10 confusion). */
export function stamp(d: Date) {
  return `${d.getDate()} ${d.toLocaleString("en-GB", { month: "short" })}, ${d.toLocaleString("en-US", { hour: "numeric", minute: "2-digit", hour12: true }).toLowerCase().replace(/\s+/g, " ")}`;
}
