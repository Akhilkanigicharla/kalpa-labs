import { describe, expect, it } from "vitest";
import { textFileName, toMarkdown, toPlain } from "../lib/export";
import { parseOneTab } from "../lib/importers";
import type { Session } from "../lib/model";

const s: Session = {
  id: "a", name: "Work [Q4]", createdAt: Date.UTC(2026, 10, 28, 6, 0), kind: "manual",
  windows: [
    { tabs: [
      { url: "https://a.com/x_(y)", title: "A [draft] *bold*", groupKey: "g1" },
      { url: "https://b.com/", title: "", groupKey: null },
      { url: "chrome://settings", title: "Settings" },
    ], groups: [{ key: "g1", title: "Research", color: "blue", collapsed: false }] },
    { tabs: [{ url: "https://c.com/?q=a b", title: "తెలుగు 🚀 | pipe" }], groups: [] },
  ],
};

describe("Markdown export", () => {
  const md = toMarkdown([s]);
  it("has session heading, window headings and group heading", () => {
    expect(md).toContain("## Work \\[Q4\\]");
    expect(md).toContain("### Window 1");
    expect(md).toContain("### Window 2");
    expect(md).toContain("**Research**");
  });
  it("escapes brackets in titles and parens/spaces in URLs so links never break", () => {
    expect(md).toContain("[A \\[draft\\] \\*bold\\*](https://a.com/x_%28y%29)");
    expect(md).toContain("(https://c.com/?q=a%20b)");
  });
  it("falls back to the URL when a tab has no title, and skips non-web pages", () => {
    expect(md).toContain("[https://b.com/](https://b.com/)");
    expect(md).not.toContain("chrome://");
  });
  it("keeps emoji and Telugu as is", () => { expect(md).toContain("తెలుగు 🚀"); });
  it("one window = no window headings", () => {
    expect(toMarkdown([{ ...s, windows: [s.windows[1]!] }])).not.toContain("### Window");
  });
  it("hostile title cannot inject HTML or a javascript: link", () => {
    const bad = toMarkdown([{ ...s, windows: [{ groups: [], tabs: [{ url: "javascript:alert(1)", title: "x" }, { url: "https://ok.com", title: "<img src=x onerror=alert(1)>](javascript:alert(1))" }] }] }]);
    expect(bad).not.toMatch(/[^\\]\]\(javascript:/);   // only escaped \] may precede it, so it stays text
    expect(bad).not.toContain("<img");
  });
  it("empty list gives a short note, not an empty file", () => { expect(toMarkdown([])).toMatch(/No saved tabs/); });
});

describe("Plain text export", () => {
  const txt = toPlain([s]);
  it("is OneTab format (url | title) and round-trips through our OneTab importer", () => {
    expect(txt.split("\n")[0]).toBe("https://a.com/x_(y) | A [draft] *bold*");
    const back = parseOneTab(txt);
    expect(back.tabs).toBe(3);
    expect(back.session.windows.flatMap((w) => w.tabs).map((t) => t.url)).toEqual(["https://a.com/x_(y)", "https://b.com/", "https://c.com/?q=a b"]);
  });
  it("blank line between windows, no newlines inside a title", () => {
    expect(toPlain([{ ...s, windows: [{ groups: [], tabs: [{ url: "https://x.com", title: "a\nb\r\nc" }] }] }])).toBe("https://x.com | a b c\n");
    expect(txt).toContain("\n\nhttps://c.com/");
  });
});

it("file names are safe and dated", () => {
  expect(textFileName("md", Date.UTC(2026, 10, 28))).toBe("tab-lifeboat-2026-11-28.md");
  expect(textFileName("txt", Date.UTC(2026, 10, 28))).toBe("tab-lifeboat-2026-11-28.txt");
});
