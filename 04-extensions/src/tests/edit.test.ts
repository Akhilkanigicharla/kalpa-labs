// v0.3 Group B: edit saved sessions (remove / move / merge / rename) with atomic writes + Undo; popup search speed.
import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import { isEmpty, mergeSessions, moveTab, removeTab, tabAt } from "../lib/edit";
import type { Session } from "../lib/model";
import { _clearForTests, applyEdit, getSession, listSessions, listTrash, putSession, undoEdit } from "../lib/store";
import { searchTabs } from "../lib/tools";

const mk = (id: string, kind: Session["kind"] = "manual"): Session => ({
  id, name: id, kind, createdAt: 1,
  windows: [
    { tabs: [{ url: `https://${id}.test/1`, title: "🚀 one" }, { url: `https://${id}.test/2`, title: "తెలుగు", groupKey: "g" }, { url: `https://${id}.test/3`, title: "<b>3</b>", groupKey: "g" }],
      groups: [{ key: "g", title: "Work", color: "blue", collapsed: false }] },
    { tabs: [{ url: `https://${id}.test/4`, title: "four" }], groups: [] },
  ],
});

describe("edit functions never change their input", () => {
  it("removeTab drops the tab, then an empty window and an unused group", () => {
    const s = mk("a"); const before = structuredClone(s);
    let x = removeTab(s, 1, 0);
    expect(x.windows).toHaveLength(1); expect(s).toEqual(before);
    x = removeTab(removeTab(x, 0, 2), 0, 1);
    expect(x.windows[0]!.groups).toEqual([]);
    expect(isEmpty(removeTab(x, 0, 0))).toBe(true);
  });
  it("tabAt refuses a stale index or an address that changed", () => {
    const s = mk("a");
    expect(tabAt(s, 0, 1, "https://a.test/2")?.title).toBe("తెలుగు");
    expect(tabAt(s, 0, 1, "https://a.test/9")).toBeNull();
    expect(tabAt(s, 5, 0)).toBeNull(); expect(tabAt(s, 0, 99)).toBeNull();
  });
  it("moveTab carries the tab's group, joins a matching group, never clashes keys", () => {
    const a = mk("a"), b = mk("b");
    b.windows[1]!.groups.push({ key: "g", title: "Other", color: "red", collapsed: false }); b.windows[1]!.tabs[0]!.groupKey = "g";
    const [a2, b2] = moveTab(a, b, 0, 1);
    expect(a2.windows[0]!.tabs.map((t) => t.url)).toEqual(["https://a.test/1", "https://a.test/3"]);
    const w = b2.windows[1]!; const moved = w.tabs.at(-1)!;
    expect(moved.url).toBe("https://a.test/2");
    expect(w.groups.find((g) => g.key === moved.groupKey)).toMatchObject({ title: "Work", color: "blue" });
    expect(new Set(w.groups.map((g) => g.key)).size).toBe(w.groups.length);
    const [, b3] = moveTab(a2, b2, 0, 1);   // the second Work tab joins the same group
    expect(b3.windows[1]!.groups.filter((g) => g.title === "Work")).toHaveLength(1);
    expect(a.windows[0]!.tabs).toHaveLength(3);
  });
  it("an edited automatic snapshot becomes manual, so pruning can't eat it", () => {
    const [x, y] = moveTab(mk("a", "auto"), mk("b", "auto"), 0, 0);
    expect([x.kind, y.kind, mergeSessions(mk("c", "auto"), mk("d")).kind, mk("e", "import").kind]).toEqual(["manual", "manual", "manual", "import"]);
  });
  it("merge appends every window and keeps the target's name", () => {
    const m = mergeSessions(mk("a"), mk("b"));
    expect([m.name, m.windows.length, m.windows.flatMap((w) => w.tabs).length]).toEqual(["a", 4, 8]);
  });
});

describe("atomic writes + Undo (store)", () => {
  beforeEach(async () => { await _clearForTests(); });
  it("merge: target written and source moved to Recently deleted in one go; Undo puts both back exactly", async () => {
    const a = mk("a"), b = mk("b"); await putSession(a); await putSession(b);
    await applyEdit([mergeSessions(a, b)], ["b"], 5);
    expect((await listSessions()).map((s) => s.id)).toEqual(["a"]);
    expect((await getSession("a"))!.windows).toHaveLength(4);
    expect((await listTrash(5)).map((t) => t.id)).toEqual(["b"]);
    await undoEdit([a, b], ["b"]);
    expect(await getSession("a")).toEqual(a); expect(await getSession("b")).toEqual(b);
    expect(await listTrash(5)).toEqual([]);
  });
  it("a failing write changes nothing (the whole transaction aborts)", async () => {
    const a = mk("a"); await putSession(a);
    const bad = { ...removeTab(a, 0, 0), id: undefined } as unknown as Session;   // no key: IndexedDB throws
    await expect(applyEdit([removeTab(a, 1, 0), bad])).rejects.toThrow();
    expect(await getSession("a")).toEqual(a);
  });
  it("records that aren't sessions are ignored on read (hostile or corrupt storage)", async () => {
    await putSession(mk("ok"));
    await putSession({ id: "bad", windows: "nope" } as unknown as Session);
    await putSession({ id: "bad2", windows: [{ tabs: null }] } as unknown as Session);
    expect((await listSessions()).map((s) => s.id)).toEqual(["ok"]);
    expect(await getSession("bad")).toBeUndefined();
  });
});

describe("popup search", () => {
  it("is fast with 10,000 saved tabs across 20 sessions (emoji, Telugu, long titles)", () => {
    const sessions: Session[] = Array.from({ length: 20 }, (_, s) => ({ id: `s${s}`, name: `S${s}`, kind: "auto", createdAt: s,
      windows: [{ groups: [], tabs: Array.from({ length: 500 }, (_, i) => ({ url: `https://site${i % 997}.test/p/${s}-${i}`, title: `${i % 3 ? "తెలుగు వార్తలు" : "🚀 launch"} ${"x".repeat(i % 7 ? 20 : 2000)} ${i}` })) }] }));
    searchTabs(sessions, "warm up");
    const t0 = performance.now();
    const r = searchTabs(sessions, "తెలుగు 124");
    const r2 = searchTabs(sessions, "🚀");
    const ms = performance.now() - t0;
    expect(ms).toBeLessThan(250);
    expect(r.length).toBeGreaterThan(0); expect(r2).toHaveLength(100);
    expect(searchTabs(sessions, "zzz-no-such")).toEqual([]);
  });
});
