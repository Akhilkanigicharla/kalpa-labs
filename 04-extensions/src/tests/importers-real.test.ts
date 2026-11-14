// A213: import tests against the formats Session Buddy publishes (sessionbuddy.com/formats, read 14 Nov 2026).
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { detectAndParse, parseCsv } from "../lib/importers";
import { restorable } from "../lib/model";

const sample = (f: string) => readFileSync(new URL(`./fixtures/samples/${f}`, import.meta.url), "utf8");
const tabsOf = (p: ReturnType<typeof detectAndParse>) => p.session.windows.flatMap((w) => w.tabs);
const groupTitles = (p: ReturnType<typeof detectAndParse>) => p.session.windows.flatMap((w) => w.groups.map((g) => g.title));

describe("Session Buddy samples (A213)", () => {
  it("v4 JSON backup: 8 links, one window per folder, folder names kept, pinned kept", () => {
    const p = detectAndParse(sample("sessionbuddy-v4-docs.json"));
    expect([p.format, p.tabs, p.session.windows.length, p.skipped]).toEqual(["sessionbuddy-v4", 8, 4, 0]);
    expect(groupTitles(p)).toEqual(["Dogs", "Cats", "Snakes", "Lizards"]);
    expect(tabsOf(p).find((t) => t.title.startsWith("Boa"))?.pinned).toBe(true);
    expect(tabsOf(p)[0]!.favIconUrl).toBe("https://en.wikipedia.org/static/favicon/wikipedia.ico");
  });

  it("v3 JSON backup: `name` wins over `title`, chrome:// kept in the archive but never reopened", () => {
    const p = detectAndParse(sample("sessionbuddy-v3-object.json"));
    expect([p.format, p.tabs, p.session.windows.length]).toEqual(["sessionbuddy-v3", 3, 2]);
    expect(groupTitles(p)).toEqual(["Mail"]);
    expect(tabsOf(p).filter((t) => !restorable(t.url)).map((t) => t.url)).toEqual(["chrome://settings/"]);
  });

  it("CSV export: quoted commas, one window per folder, header order free", () => {
    const p = detectAndParse(sample("sessionbuddy-docs.csv"));
    expect([p.format, p.tabs, p.session.windows.length, p.skipped]).toEqual(["sessionbuddy-csv", 8, 4, 0]);
    expect(groupTitles(p)).toEqual(["Dogs", "Cats", "Snakes", "Lizards"]);
    const q = parseCsv('URL,Title\r\n"https://a.test/?x=1,2","He said ""hi"""\r\nnot a url,x\r\n');
    expect([q.tabs, q.skipped]).toEqual([1, 1]);
    expect(tabsOf(q)[0]).toMatchObject({ url: "https://a.test/?x=1,2", title: 'He said "hi"' });
  });

  it("CSV without a URL column is refused with a plain message", () => {
    expect(() => parseCsv("Name,Link\nx,https://a.test\n")).toThrow(/URL column/);
  });

  it("Title/URL pairs text: titles attach to their links, all in one list", () => {
    const p = detectAndParse(sample("sessionbuddy-pairs.txt"));
    expect([p.format, p.tabs, p.session.windows.length]).toEqual(["sessionbuddy-pairs", 3, 1]);
    expect(tabsOf(p).map((t) => t.title)).toEqual(["German Shepherd - Wikipedia", "https://www.google.com/search?q=Labrador+Retriever", "Ragdoll kitten - YouTube"]);
  });

  it("OneTab text is still OneTab (blank line = new group)", () => {
    const p = detectAndParse("https://a.test | A\nhttps://b.test | B\n\nhttps://c.test | C\n");
    expect([p.format, p.tabs, p.groups]).toEqual(["onetab-text", 3, 2]);
  });
});
