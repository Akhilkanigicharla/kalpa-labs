import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import { captureAll, restore, type Br } from "../lib/capture";
import { detectAndParse, parseOneTab, parseSessionBuddy } from "../lib/importers";
import { countTabs, restorable, type Session } from "../lib/model";
import { _clearForTests, listSessions, pruneAuto, putSession } from "../lib/store";
// @ts-expect-error plain .mjs helper
import { onetabText, sessionBuddyV3, sessionBuddyV4 } from "./fixtures/make-fixtures.mjs";

describe("importers (E6)", () => {
  it("OneTab text: 1,000 tabs in 10 groups, titles with ' | ' kept, preview counts", () => {
    const t0 = performance.now();
    const p = parseOneTab(onetabText());
    expect(performance.now() - t0).toBeLessThan(200);
    expect([p.tabs, p.groups, p.skipped, p.format]).toEqual([1000, 10, 0, "onetab-text"]);
    expect(p.session.windows[3]!.tabs[0]).toMatchObject({ url: "https://example.com/g3/page-0?q=300", title: "Page 300 – grupo 3 | test", groupKey: "onetab-4" });
  });
  it("OneTab: junk lines skipped, URL-only lines titled by URL, CRLF ok", () => {
    const p = parseOneTab("https://a.test | A\r\nnot a url\r\nhttps://b.test\r\n\r\nhttps://c.test | C");
    expect([p.tabs, p.groups, p.skipped]).toEqual([3, 2, 1]);
    expect(p.session.windows[0]!.tabs[1]!.title).toBe("https://b.test");
  });
  it("Session Buddy v3: 1,000 tabs across 10 windows, pinned kept", () => {
    const p = parseSessionBuddy(JSON.stringify(sessionBuddyV3()));
    expect([p.tabs, p.session.windows.length, p.format]).toEqual([1000, 10, "sessionbuddy-v3"]);
    expect(p.session.windows[0]!.tabs[0]!.pinned).toBe(true);
  });
  it("Session Buddy v4 collections: folders become named groups; missing URLs skipped", () => {
    const p = parseSessionBuddy(sessionBuddyV4());
    expect(p.format).toBe("sessionbuddy-v4");
    expect(p.session.windows.map((w) => w.groups[0]?.title)).toEqual(["Articles", "Video"]);
    expect([p.tabs, p.skipped]).toEqual([4, 1]);   // chrome:// kept in the archive, skipped only at restore
  });
  it("auto-detects the format", () => {
    expect(detectAndParse(onetabText(20, 2)).format).toBe("onetab-text");
    expect(detectAndParse(JSON.stringify(sessionBuddyV4())).format).toBe("sessionbuddy-v4");
  });
});

describe("store + auto-snapshot limits (E7)", () => {
  beforeEach(async () => { await _clearForTests(); });
  const mk = (kind: Session["kind"], createdAt: number): Session => ({ id: `${kind}-${createdAt}`, kind, createdAt, name: kind, windows: [{ tabs: [{ url: "https://x.test", title: "x" }], groups: [] }] });
  it("free plan keeps the last 3 auto snapshots and every manual/import session", async () => {
    for (let i = 1; i <= 6; i++) await putSession(mk("auto", i));
    await putSession(mk("manual", 0)); await putSession(mk("import", 7));
    expect(await pruneAuto("free")).toBe(3);
    const left = await listSessions();
    expect(left.filter((s) => s.kind === "auto").map((s) => s.createdAt)).toEqual([6, 5, 4]);
    expect(left.map((s) => s.kind)).toContain("manual");
  });
  it("pro keeps 90 days", async () => {
    const day = 864e5, now = 200 * day;
    await putSession(mk("auto", now - 91 * day)); await putSession(mk("auto", now - 10 * day));
    expect(await pruneAuto("pro", now)).toBe(1);
  });
});

// ---- fake browser API: enough of tabs / windows / tabGroups to test capture and restore
function fakeBrowser(seed: { incognito?: boolean; tabs: { url: string; title?: string; pinned?: boolean; groupId?: number }[] }[], groups: Record<number, { title: string; color: string; collapsed: boolean }>) {
  let nextTab = 100, nextGroup = 900; const discarded: number[] = []; let failDiscard = false; const alias: Record<number, number> = {}; const created: { windowId: number; url: string; pinned: boolean; group?: number; asleep?: boolean }[] = []; const madeGroups: Record<number, unknown> = {};
  const at = (id: number) => created[(alias[id] ?? id) - 100]!;
  const br = {
    windows: {
      getAll: async () => seed.map((w, i) => ({ id: i + 1, incognito: !!w.incognito, focused: i === 0, tabs: w.tabs.map((t, j) => ({ id: i * 50 + j, url: t.url, title: t.title, pinned: !!t.pinned, groupId: t.groupId ?? -1 })) })),
      create: async ({ url }: { url: string }) => { const id = 500 + created.length; const tid = nextTab++; created.push({ windowId: id, url, pinned: false }); return { id, tabs: [{ id: tid }] }; },
    },
    tabs: {
      create: async ({ windowId, url, pinned }: { windowId: number; url: string; pinned: boolean }) => { created.push({ windowId, url, pinned }); return { id: nextTab++ }; },
      update: async (id: number, p: { pinned: boolean }) => { at(id).pinned = p.pinned; return {}; },
      group: async ({ tabIds }: { tabIds: number[] }) => { const g = nextGroup++; for (const t of tabIds) at(t).group = g; return g; },
      get: async (id: number) => ({ id, url: at(id).url, status: "complete", active: false }),
      // real Chrome gives a discarded tab a new id (checked 12 Nov 2026)
      discard: async (id: number) => { if (failDiscard) throw new Error("cannot discard"); const nid = id + 1000; alias[nid] = alias[id] ?? id; at(nid).asleep = true; discarded.push(id); return { id: nid }; },
    },
    tabGroups: {
      get: async (id: number) => ({ id, ...groups[id] }),
      update: async (id: number, p: unknown) => { madeGroups[id] = p; return {}; },
    },
  };
  return { br: br as unknown as Br, created, madeGroups, discarded, setFailDiscard: (v: boolean) => { failDiscard = v; } };
}

describe("capture and restore (E3)", () => {
  it("round-trips windows, pinned tabs and tab groups (title, colour, collapsed); skips incognito and chrome://", async () => {
    const { br, created, madeGroups } = fakeBrowser([
      { tabs: [{ url: "https://mail.test", pinned: true }, { url: "https://a.test", groupId: 7 }, { url: "https://b.test", groupId: 7 }, { url: "chrome://settings" }] },
      { incognito: true, tabs: [{ url: "https://secret.test" }] },
      { tabs: [{ url: "https://c.test", groupId: 8 }] },
    ], { 7: { title: "Research", color: "purple", collapsed: true }, 8: { title: "Bills", color: "red", collapsed: false } });
    const s = await captureAll(br, "manual", "Test");
    expect(countTabs(s)).toEqual({ tabs: 5, groups: 2, windows: 2 });
    expect(JSON.stringify(s)).not.toContain("secret.test");
    const r = await restore(br, s);
    expect(r).toEqual({ windows: 2, tabs: 4, skipped: 1, asleep: 0 });
    expect(created.map((c) => c.url)).toEqual(["https://mail.test", "https://a.test", "https://b.test", "https://c.test"]);
    expect(created[0]!.pinned).toBe(true);
    expect(created[1]!.group).toBe(created[2]!.group);
    expect(Object.values(madeGroups)).toEqual([{ title: "Research", color: "purple", collapsed: true }, { title: "Bills", color: "red", collapsed: false }]);
  });
  it("big sessions restore asleep: tabs after the first load only when clicked (stops the browser freezing)", async () => {
    const urls = Array.from({ length: 20 }, (_, i) => ({ url: `https://site${i}.test` }));
    const { br, created, discarded } = fakeBrowser([{ tabs: urls }], {});
    const r = await restore(br, await captureAll(br, "manual", "Big"), 0);
    expect(r).toEqual({ windows: 1, tabs: 20, skipped: 0, asleep: 19 });
    expect(created.map((c) => c.url)).toEqual(urls.map((u) => u.url));   // every tab keeps its address
    expect(discarded).not.toContain(100);                                 // the first tab stays awake
  });
  it("small sessions load normally, and a failed discard never stops a restore", async () => {
    const small = fakeBrowser([{ tabs: [{ url: "https://a.test" }, { url: "https://b.test" }] }], {});
    expect((await restore(small.br, await captureAll(small.br))).asleep).toBe(0);
    expect(small.discarded).toEqual([]);
    const big = fakeBrowser([{ tabs: Array.from({ length: 18 }, (_, i) => ({ url: `https://x${i}.test` })) }], {});
    big.setFailDiscard(true);
    expect(await restore(big.br, await captureAll(big.br), 0)).toEqual({ windows: 1, tabs: 18, skipped: 0, asleep: 0 });
  });
  it("a big session keeps its tab groups even though sleeping tabs get new ids", async () => {
    const tabs = Array.from({ length: 20 }, (_, i) => ({ url: `https://g${i}.test`, groupId: i < 10 ? 7 : undefined }));
    const { br, created, madeGroups } = fakeBrowser([{ tabs }], { 7: { title: "Work", color: "blue", collapsed: false } });
    const r = await restore(br, await captureAll(br), 0);
    expect(r.asleep).toBe(19);
    const grouped = created.filter((c) => c.group !== undefined);
    expect(grouped.map((c) => c.url)).toEqual(tabs.slice(0, 10).map((t) => t.url));
    expect(Object.values(madeGroups)).toEqual([{ title: "Work", color: "blue", collapsed: false }]);
  });
  it("restorable() only reopens web URLs (no local files from an imported list)", () => {
    expect(["https://x.test", "http://x.test"].every(restorable)).toBe(true);
    expect(["file:///C:/Users/a.pdf", "ftp://x.test", "chrome://settings", "about:blank", "javascript:alert(1)", "data:text/html,x", ""].some(restorable)).toBe(false);
  });
});
