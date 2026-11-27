// v0.3 Group C: importers (Pocket CSV/HTML, Edge Collections CSV, Toby JSON, bookmarks HTML) and exports.
import { readFileSync } from "node:fs";
import { DOMParser as LinkeDOM } from "linkedom";
import { describe, expect, it } from "vitest";
import { csvCell, exportName, mdText, toCsv, toMarkdown, toUrlList } from "../lib/export";
import { htmlToLists, looksHtml, prepareImport } from "../lib/html-import";
import { csvRows, detectAndParse, fromLists, sessionsOf } from "../lib/importers";
import { restorable, type Session } from "../lib/model";

const sample = (f: string) => readFileSync(new URL(`./fixtures/samples/${f}`, import.meta.url), "utf8");
const parse = (t: string) => new LinkeDOM().parseFromString(t, "text/html") as unknown as Document;
const names = (t: string) => sessionsOf(detectAndParse(prepareImport(t, parse))).map((s) => [s.name, s.windows[0]!.tabs.length]);

describe("v0.3 importers", () => {
  it("Pocket CSV: one session per status, quoted commas, Japanese titles, javascript: left out and counted", () => {
    const p = detectAndParse(sample("pocket-list.csv"));
    expect([p.format, p.tabs, p.skipped]).toEqual(["pocket-csv", 3, 1]);
    expect(sessionsOf(p).map((s) => [s.name, s.windows[0]!.tabs.map((t) => t.title)])).toEqual([
      ["Pocket: Unread", ["とほほのＷＷＷ入門", '=HYPERLINK("https://evil.test")']], ["Pocket: Archive", ["Rust, the book"]]]);
    expect(detectAndParse(sample("pocket-old-cursor.csv"))).toMatchObject({ format: "pocket-csv", tabs: 1 });
  });
  it("Pocket HTML: Unread and Read Archive become two sessions; entities decoded as text", () => {
    expect(looksHtml(sample("pocket-ril_export.html"))).toBe(true);
    const r = htmlToLists(parse(sample("pocket-ril_export.html")));
    expect(r.kind).toBe("pocket-html");
    expect(r.lists.map((l) => [l.name, l.tabs.length])).toEqual([["Pocket: Unread", 2], ["Pocket: Archive", 1]]);
    expect(r.lists[1]!.tabs[0]!.title).toBe("Log Structured Merge Trees <img src=x onerror=alert(1)>");
    expect(r.lists[0]!.tabs[0]!.title).toBe("The Hardest Program I've Ever Written");
  });
  it("bookmarks HTML: each folder (with its path) becomes a session; bookmarklets left out", () => {
    expect(names(sample("bookmarks.html"))).toEqual([["Bookmarks bar", 1], ["Bookmarks bar / Recipes & food", 1], ["Other bookmarks", 1]]);
    const p = detectAndParse(prepareImport(sample("bookmarks.html"), parse));
    expect([p.format, p.tabs, p.skipped]).toEqual(["bookmarks-html", 3, 1]);
  });
  it("Toby JSON: lists become sessions, customTitle wins, data: links and empty lists left out", () => {
    const p = detectAndParse(sample("toby.json"));
    expect([p.format, p.tabs, p.skipped]).toEqual(["toby-json", 3, 1]);
    expect(sessionsOf(p).map((s) => s.name)).toEqual(["Work 🚀", "తెలుగు"]);
    expect(sessionsOf(p)[0]!.windows[0]!.tabs[0]!.title).toBe("My repos");
  });
  it("Edge Collections CSV (synthetic header): one session per collection", () => {
    expect(names(sample("edge-collections.csv"))).toEqual([["Trip to Goa", 2], ["Laptops", 1]]);
    expect(detectAndParse(sample("edge-collections.csv")).format).toBe("edge-collections-csv");
  });
  it("Session Buddy CSV (has Folder) still goes to the Session Buddy reader", () => {
    expect(detectAndParse(sample("sessionbuddy-docs.csv")).format).toBe("sessionbuddy-csv");
  });
  it("hostile lists from the page are checked again: wrong types, __proto__, 25,000 tabs, no web links", () => {
    expect(() => fromLists("nope", "x", "y")).toThrow(/couldn't be read/);
    const p = fromLists(JSON.parse('[{"name":{"x":1},"tabs":[{"url":"https://a.test","title":["x"]},{"url":5},null]},{"__proto__":{"evil":1},"name":"b","tabs":[{"url":"https://b.test"}]}, 7]'), "x", "y");
    expect([p.tabs, p.skipped, sessionsOf(p).map((s) => s.name)]).toEqual([2, 3, ["Imported", "b"]]);
    expect(({} as Record<string, unknown>).evil).toBeUndefined();
    expect(() => fromLists([{ name: "big", tabs: Array.from({ length: 25_000 }, (_, i) => ({ url: `https://x.test/${i}` })) }], "x", "y")).toThrow(/25,000 tabs/);
    expect(() => fromLists([{ name: "a", tabs: [{ url: "javascript:alert(1)" }] }], "x", "y")).toThrow("No web links found: 1 links can't be reopened and were left out.");
    expect(() => detectAndParse("<!DOCTYPE html><a href='https://x.test'>x</a>")).toThrow(/web page file/);
  });
  it("a 20,000-link bookmarks file imports; 20,001 is refused", () => {
    const html = (k: number) => `<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>${Array.from({ length: k }, (_, i) => `<DT><A HREF="https://x.test/${i}">${i}</A>`).join("")}</DL>`;
    expect(detectAndParse(prepareImport(html(20_000), parse)).tabs).toBe(20_000);
    expect(() => detectAndParse(prepareImport(html(20_001), parse))).toThrow(/20,001 tabs/);
  }, 30_000);
});

const hostile = (): Session => ({ id: "h", name: "Work # [notes] =cmd", kind: "manual", createdAt: Date.UTC(2026, 10, 28), windows: [{
  groups: [{ key: "g", title: "Group *bold*", color: "blue", collapsed: false }],
  tabs: [
    { url: "https://a.test/x?q=a b<c>", title: "](javascript:alert(1)) [x]" },
    { url: "https://b.test", title: '=HYPERLINK("https://evil.test","click")', groupKey: "g" },
    { url: "https://c.test", title: `<img src=x onerror=alert(1)>\n${"🚀".repeat(10)}`, groupKey: "g" },
    { url: "https://d.test", title: `తెలుగు ${"x".repeat(10_000)}` },
    { url: "javascript:alert(1)", title: "old import" },
  ] }] });

describe("v0.3 exports (hardening rule 5)", () => {
  it("Markdown: titles escaped, URLs in <…> with <, > and space encoded, non-web links as plain text", () => {
    const md = toMarkdown([hostile()]);
    expect(md).toContain("## Work \\# \\[notes\\] =cmd");
    expect(md).toContain("- [\\]\\(javascript:alert\\(1\\)\\) \\[x\\]](<https://a.test/x?q=a%20b%3Cc%3E>)");
    expect(md).toContain("### Group \\*bold\\*");
    expect(md).toContain("- [\\<img src=x onerror=alert\\(1\\)\\> 🚀🚀");
    expect(md).toContain("Can't reopen:\n- javascript:alert\\(1\\)");
    expect(md).not.toMatch(/\]\(javascript:/);
    expect(mdText("a\nb\\c")).toBe("a b\\\\c");
  });
  it("CSV: every cell quoted, quotes doubled, formula starts neutralised (incl. tab, CR, full-width), BOM + CRLF", () => {
    for (const [v, out] of [["=1+1", `"'=1+1"`], ["+1", `"'+1"`], ["-1", `"'-1"`], ["@SUM(A1)", `"'@SUM(A1)"`], ["\t=x", `"'\t=x"`], ["\r=x", `"'\r=x"`],
      ["＝1", `"'＝1"`], ["＋1", `"'＋1"`], ["－1", `"'－1"`], ["＠x", `"'＠x"`], ['say "hi", ok', `"say ""hi"", ok"`], ["తెలుగు", `"తెలుగు"`]])
      expect(csvCell(v!)).toBe(out);
    const csv = toCsv([hostile()]);
    expect(csv.startsWith("﻿\"Session\",\"Group\",\"Title\",\"URL\",\"Saved\"\r\n")).toBe(true);
    const rows = csvRows(csv.slice(1));
    expect(rows).toHaveLength(6);
    expect(rows[2]).toEqual(["'Work # [notes] =cmd".slice(1), "Group *bold*", `'=HYPERLINK("https://evil.test","click")`, "https://b.test", "2026-11-28T00:00:00.000Z"]);
    expect(rows[4]![2]!.length).toBe(10_007);
  });
  it("link list re-imports into the same tabs (round trip); titles on one line", () => {
    const s = { ...hostile(), windows: [{ ...hostile().windows[0]!, tabs: hostile().windows[0]!.tabs.filter((t) => restorable(t.url)) }] };
    const txt = toUrlList([s, { ...s, id: "h2" }]);
    expect(txt.split("\n")[2]).toBe("https://c.test | <img src=x onerror=alert(1)> 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀");
    const back = detectAndParse(txt);
    expect([back.tabs, back.session.windows.length]).toEqual([8, 2]);
    expect(back.session.windows[0]!.tabs.map((t) => t.url)).toEqual(s.windows[0]!.tabs.map((t) => t.url));
  });
  it("file names: local date, safe characters, at most 100 characters", () => {
    const d = new Date(2026, 10, 28, 23, 30);
    expect(exportName("Work / తెలుగు <x>", "md", d)).toBe("tab-lifeboat-2026-11-28-Work-x.md");
    expect(exportName("y".repeat(300), "csv", d).length).toBeLessThanOrEqual(100);
  });
});
