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

/** Reopens every window of a session with pinned tabs and tab groups (title, colour, collapsed). Never closes anything. */
export async function restore(br: Br, s: Session): Promise<{ windows: number; tabs: number; skipped: number }> {
  let tabs = 0, skipped = 0;
  for (const w of s.windows) {
    const ok = w.tabs.filter((t) => restorable(t.url)); skipped += w.tabs.length - ok.length;
    const head = ok[0];
    if (!head) continue;
    const win = await br.windows.create({ url: head.url, focused: !!w.focused });
    const first = win?.tabs?.[0];
    const created: { id: number; groupKey?: string | null }[] = [];
    if (first?.id !== undefined) { created.push({ id: first.id, groupKey: head.groupKey }); if (head.pinned) await br.tabs.update(first.id, { pinned: true }); }
    for (const t of ok.slice(1)) {
      const nt = await br.tabs.create({ windowId: win?.id, url: t.url, pinned: !!t.pinned, active: false });
      if (nt.id !== undefined) created.push({ id: nt.id, groupKey: t.groupKey });
    }
    tabs += created.length;
    if (br.tabGroups) for (const g of w.groups) {
      const ids = created.filter((c) => c.groupKey === g.key).map((c) => c.id);
      if (!ids.length) continue;
      const gid = await br.tabs.group({ tabIds: ids as [number, ...number[]], createProperties: { windowId: win?.id } });
      await br.tabGroups.update(gid, { title: g.title, color: g.color, collapsed: g.collapsed });
    }
  }
  return { windows: s.windows.length, tabs, skipped };
}

/** "17 Oct, 8:46 pm": short, unambiguous for Indian and UK/US readers alike (no 10/17 vs 17/10 confusion). */
export function stamp(d: Date) {
  return `${d.getDate()} ${d.toLocaleString("en-GB", { month: "short" })}, ${d.toLocaleString("en-US", { hour: "numeric", minute: "2-digit", hour12: true }).toLowerCase().replace(/\s+/g, " ")}`;
}
