import { describe, expect, it } from "vitest";
import type { Session } from "../lib/model";
import { backupDue, findDuplicates, findStale, normUrl, searchTabs, tabTimeline, upgradeNudge } from "../lib/tools";

const DAY = 864e5;
const sess = (id: string, createdAt: number, tabs: [string, string][], kind: Session["kind"] = "auto"): Session => ({
  id, name: `S ${id}`, createdAt, kind, windows: [{ tabs: tabs.map(([url, title]) => ({ url, title })), groups: [] }],
});

describe("normUrl", () => {
  it("drops #hash, tracking params and a trailing slash; keeps real query", () => {
    expect(normUrl("https://Ex.com/a/?utm_source=x&id=7&fbclid=1#top")).toBe("https://ex.com/a?id=7");
    expect(normUrl("https://ex.com/")).toBe("https://ex.com");
    expect(normUrl("not a url")).toBe("not a url");
  });
});

describe("searchTabs (Free: find any saved tab)", () => {
  const all = [sess("b", 2000, [["https://docs.rust-lang.org/book", "The Rust Book"], ["https://news.ycombinator.com", "Hacker News"]]),
    sess("a", 1000, [["https://docs.rust-lang.org/book", "The Rust Book"], ["https://youtube.com/watch?v=1", "Lo-fi beats"]])];
  it("matches every word in title or URL, newest first, one hit per URL", () => {
    const r = searchTabs(all, "rust BOOK");
    expect(r.map((h) => [h.sessionId, h.title])).toEqual([["b", "The Rust Book"]]);
    expect(r[0]!.alsoIn).toBe(1);
  });
  it("empty query gives nothing; limit is respected", () => {
    expect(searchTabs(all, "  ")).toEqual([]);
    expect(searchTabs(all, "https", 2)).toHaveLength(2);
  });
});

describe("findDuplicates / findStale (Pro cleanup)", () => {
  const open = [
    { id: 1, url: "https://a.com/x#one", pinned: false, active: false, audible: false, lastAccessed: 0 },
    { id: 2, url: "https://a.com/x", pinned: false, active: false, audible: false, lastAccessed: 0 },
    { id: 3, url: "https://a.com/x?utm_source=t", pinned: true, active: false, audible: false, lastAccessed: 0 },
    { id: 4, url: "https://b.com", pinned: false, active: true, audible: false, lastAccessed: 0 },
    { id: 5, url: "https://c.com", pinned: false, active: false, audible: true, lastAccessed: 0 },
    { id: 6, url: "https://d.com", pinned: false, active: false, audible: false, lastAccessed: 10 * DAY },
  ];
  it("keeps the pinned copy (else the first), never closes pinned tabs", () => {
    expect(findDuplicates(open)).toEqual([1, 2]);
    expect(findDuplicates(open.filter((t) => t.id !== 3))).toEqual([2]);
  });
  it("stale = not opened for N days; skips pinned, active, playing and tabs with no lastAccessed info", () => {
    expect(findStale(open, 7, 12 * DAY)).toEqual([1, 2]);
    expect(findStale([{ id: 9, url: "https://e.com", pinned: false, active: false, audible: false }], 7, 12 * DAY)).toEqual([]);
  });
});

describe("tabTimeline (Pro: where did this tab go?)", () => {
  const hist = [sess("3", 3 * DAY, [["https://b.com", "B"]]), sess("2", 2 * DAY, [["https://a.com/#x", "A"]]), sess("1", 1 * DAY, [["https://a.com", "A"]])];
  it("first and last seen, and that it is gone from the newest snapshot", () => {
    expect(tabTimeline(hist, "https://a.com/")).toEqual({ firstSeen: DAY, lastSeen: 2 * DAY, snapshots: 2, lastSessionId: "2", goneSince: 3 * DAY });
  });
  it("never seen → null; still open in the newest snapshot → goneSince null", () => {
    expect(tabTimeline(hist, "https://zzz.com")).toBeNull();
    expect(tabTimeline(hist, "https://b.com")!.goneSince).toBeNull();
  });
});

describe("backupDue / upgradeNudge", () => {
  it("daily backup is due after 20 hours, or if never made", () => {
    expect(backupDue(null, 5)).toBe(true);
    expect(backupDue(0, 19 * 36e5)).toBe(false);
    expect(backupDue(0, 21 * 36e5)).toBe(true);
  });
  it("honest nudge only for free users after a big import, at most once a week", () => {
    expect(upgradeNudge({ plan: "free", importedTabs: 1240, lastNudge: null, now: 10 * DAY })).toMatch(/You just moved 1,240 tabs/);
    expect(upgradeNudge({ plan: "free", importedTabs: 20, lastNudge: null, now: 10 * DAY })).toBeNull();
    expect(upgradeNudge({ plan: "pro", importedTabs: 1240, lastNudge: null, now: 10 * DAY })).toBeNull();
    expect(upgradeNudge({ plan: "free", importedTabs: 1240, lastNudge: 8 * DAY, now: 10 * DAY })).toBeNull();
  });
});
