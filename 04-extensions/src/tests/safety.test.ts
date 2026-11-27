// v0.3 Group A: stale-snapshot warning, restore skips open tabs, restart/update banner, message checks.
import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import { type Br, restore } from "../lib/capture";
import { checkMsg, fromUs, MAX_TEXT } from "../lib/messages";
import type { Session } from "../lib/model";
import { _clearForTests, listSessions, pruneAuto, putSession } from "../lib/store";
import { bannerSession, clock, missingTabs, staleSince } from "../lib/tools";

const MIN = 60_000;
describe("stale-snapshot warning", () => {
  const now = Date.UTC(2026, 10, 27, 12, 0);
  it("fine while auto-save runs; stale after 3 missed intervals", () => {
    expect(staleSince({ lastRun: now - 14 * MIN, bootAt: now - 600 * MIN, now, everyMin: 5 })).toBeNull();
    expect(staleSince({ lastRun: now - 16 * MIN, bootAt: now - 600 * MIN, now, everyMin: 5 })).toBe(now - 16 * MIN);
  });
  it("time the browser was closed doesn't count: the clock restarts at boot", () => {
    expect(staleSince({ lastRun: now - 3 * 864e5, bootAt: now - 2 * MIN, now, everyMin: 5 })).toBeNull();
    expect(staleSince({ lastRun: now - 3 * 864e5, bootAt: now - 20 * MIN, now, everyMin: 5 })).toBe(now - 3 * 864e5);
  });
  it("never ran: measured from boot", () => {
    expect(staleSince({ lastRun: null, bootAt: now - 10 * MIN, now, everyMin: 5 })).toBeNull();
    expect(staleSince({ lastRun: null, bootAt: now - 30 * MIN, now, everyMin: 5 })).toBe(now - 30 * MIN);
  });
  it("clock: HH:MM today, date + HH:MM on another day", () => {
    const t = new Date(2026, 10, 27, 9, 5).getTime();
    expect(clock(t, new Date(2026, 10, 27, 23, 0).getTime())).toBe("09:05");
    expect(clock(t, new Date(2026, 10, 28, 1, 0).getTime())).toBe("27 Nov 09:05");
  });
});

// minimal fake: records created tabs and groups
function fake() {
  let tab = 1, win = 1, grp = 1; const created: { url: string; windowId: number }[] = []; const groups: { ids: number[]; title?: string }[] = [];
  const byId = new Map<number, string>();
  const br = {
    windows: { create: async ({ url }: { url: string }) => { const id = win++; const t = tab++; byId.set(t, url); created.push({ url, windowId: id }); return { id, tabs: [{ id: t }] }; } },
    tabs: {
      create: async ({ url, windowId }: { url: string; windowId: number }) => { const t = tab++; byId.set(t, url); created.push({ url, windowId }); return { id: t }; },
      update: async () => ({}), group: async ({ tabIds }: { tabIds: number[] }) => { groups.push({ ids: tabIds }); return grp++; },
      get: async (id: number) => ({ id, status: "complete", active: false }), discard: async (id: number) => ({ id }),
    },
    tabGroups: { update: async (id: number, p: { title: string }) => { groups[id - 1]!.title = p.title; return {}; } },
  };
  return { br: br as unknown as Br, created, groups, byId };
}
const S = (tabs: { url: string; groupKey?: string }[][], groups: { key: string; title: string }[][] = []): Session => ({
  id: "s", name: "S", kind: "manual", createdAt: 1,
  windows: tabs.map((t, i) => ({ tabs: t.map((x) => ({ title: x.url, ...x })), groups: (groups[i] ?? []).map((g) => ({ ...g, color: "blue" as const, collapsed: false })) })),
});

describe("restore skips tabs already open", () => {
  it("exact address match, only a trailing slash ignored; groups kept for the rest", async () => {
    const { br, created, groups, byId } = fake();
    const s = S([[{ url: "https://a.test/x/" }, { url: "https://b.test/?q=1#top", groupKey: "g" }, { url: "https://c.test/?utm_source=m", groupKey: "g" }, { url: "https://d.test", groupKey: "g" }]], [[{ key: "g", title: "Work" }]]);
    const r = await restore(br, s, 0, false, ["https://a.test/x", "https://b.test?q=1#top", "https://c.test/"]);
    expect([r.tabs, r.alreadyOpen, r.skipped]).toEqual([2, 2, 0]);   // c differs by its query, so it opens
    expect(created.map((c) => c.url)).toEqual(["https://c.test/?utm_source=m", "https://d.test"]);
    expect(groups.map((g) => [g.title, g.ids.map((i) => byId.get(i))])).toEqual([["Work", ["https://c.test/?utm_source=m", "https://d.test"]]]);
  });
  it("hash-routed web app pages are different pages: both restore; the same address is skipped once", async () => {
    const { br, created } = fake();
    const s = S([[{ url: "https://app.test/#/doc/1" }, { url: "https://app.test/#/doc/2" }]]);
    const r = await restore(br, s, 0, false, ["https://app.test/#/doc/1"]);
    expect([r.tabs, r.alreadyOpen]).toEqual([1, 1]);
    expect(created.map((c) => c.url)).toEqual(["https://app.test/#/doc/2"]);
  });
  it("a window whose tabs are all open is not opened at all; query strings that differ are different pages", async () => {
    const { br, created } = fake();
    const s = S([[{ url: "https://a.test" }], [{ url: "https://q.test/?id=1" }, { url: "https://q.test/?id=2" }]]);
    const r = await restore(br, s, 0, false, ["https://a.test/", "https://q.test/?id=1"]);
    expect([r.tabs, r.alreadyOpen]).toEqual([1, 2]);
    expect(created).toEqual([{ url: "https://q.test/?id=2", windowId: 1 }]);
  });
  it("no open list (setting \"Open duplicates anyway\") opens everything", async () => {
    const { br, created } = fake();
    expect((await restore(br, S([[{ url: "https://a.test" }, { url: "https://a.test" }]]), 0, false)).alreadyOpen).toBe(0);
    expect(created).toHaveLength(2);
  });
  it("emoji, Telugu and very long URLs don't break matching", async () => {
    const long = `https://x.test/${"ఆ".repeat(4000)}🚀`;
    const { br } = fake();
    const r = await restore(br, S([[{ url: long }, { url: "https://y.test/తెలుగు" }]]), 0, false, [long, "not a url", ""]);
    expect([r.tabs, r.alreadyOpen]).toEqual([1, 1]);
  });
});

describe("restart/update banner", () => {
  const mk = (id: string, kind: Session["kind"], createdAt: number, urls = ["https://a.test"]): Session => ({ id, kind, createdAt, name: id, windows: [{ tabs: urls.map((url) => ({ url, title: url })), groups: [] }] });
  it("points at the newest auto snapshot before the restart, else the newest session", () => {
    const all = [mk("m", "manual", 50), mk("a1", "auto", 10), mk("a2", "auto", 40), mk("late", "auto", 200)];
    expect(bannerSession(all, 100)?.id).toBe("a2");
    expect(bannerSession([mk("m", "manual", 50)], 100)?.id).toBe("m");
    expect(bannerSession([mk("late", "auto", 200)], 100)).toBeNull();
    expect(bannerSession([{ ...mk("e", "auto", 5), windows: [{ tabs: [], groups: [] }] }], 100)).toBeNull();
  });
  it("counts only pages that are not open now", () => {
    const s = mk("x", "auto", 1, ["https://a.test/", "https://b.test#x", "chrome://settings"]);
    expect(missingTabs(s, ["https://a.test"])).toBe(1);
    expect(missingTabs(s, ["https://a.test", "https://b.test"])).toBe(1);   // #x is a different page
    expect(missingTabs(s, ["https://a.test", "https://b.test/#x"])).toBe(0);
  });
  beforeEach(async () => { await _clearForTests(); });
  it("the banner's snapshot survives free-plan pruning after the crash", async () => {
    for (let i = 1; i <= 6; i++) await putSession(mk(`a${i}`, "auto", i));
    await pruneAuto("free", 100, ["a1"]);
    expect((await listSessions()).map((s) => s.id).sort()).toEqual(["a1", "a4", "a5", "a6"]);
  });
});

describe("background message checks", () => {
  it("accepts known messages and copies only known fields", () => {
    const m = checkMsg(JSON.parse('{"type":"restore","id":"abc","__proto__":{"polluted":1},"evil":"x"}'));
    expect(m).toEqual({ type: "restore", id: "abc" });
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
  });
  it("refuses unknown types, wrong field types, huge or negative values", () => {
    for (const bad of [null, "save", [], { type: "rm -rf" }, { type: "restore", id: 5 }, { type: "rename", name: "x".repeat(501) },
      { type: "import", text: "x".repeat(MAX_TEXT + 1) }, { type: "edit-remove-tab", wi: -1 }, { type: "edit-remove-tab", ti: 1.5 }, { type: "constructor" }, { type: "toString" }])
      expect(checkMsg(bad)).toBeNull();
  });
  it("only our own pages may send", () => {
    const base = "chrome-extension://me/";
    expect(fromUs({ id: "me", url: `${base}popup.html` }, "me", base)).toBe(true);
    expect(fromUs({ id: "other", url: "chrome-extension://other/x.html" }, "me", base)).toBe(false);
    expect(fromUs({ id: "me", url: "https://evil.test/" }, "me", base)).toBe(false);
    expect(fromUs(undefined, "me", base)).toBe(false);
  });
});
