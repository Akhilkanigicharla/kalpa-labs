// Rules from 04-extensions/research/v03-hardening-2026-11-27.md, one test block per rule.
import { describe, expect, it } from "vitest";
import { parseBackup } from "../lib/backup";
import { detectAndParse, parseCsv, parseOneTab, parseSessionBuddy } from "../lib/importers";
import { DISK_FULL, errorText } from "../lib/messages";
import { CAPS, clip, safeUrl, sameKey } from "../lib/model";
import { restoreText, wireRestore } from "../lib/restore-ui";

const bad = ["javascript:alert(1)", "data:text/html,<b>x</b>", "file:///C:/secret.pdf", "chrome://settings", "about:blank", "blob:https://x.test/1", "view-source:https://x.test", "ftp://x.test", `https://x.test/${"a".repeat(CAPS.url)}`];

describe("rule 2: one URL gate, http(s) only, everywhere", () => {
  it("safeUrl keeps http(s) as saved, refuses every other scheme and over-long addresses", () => {
    expect(safeUrl("https://x.test/తెలుగు?q=🚀")).toBe("https://x.test/తెలుగు?q=🚀");
    expect(safeUrl("HTTP://X.test")).toBe("HTTP://X.test");
    for (const u of [...bad, "https://", "http//x", 42, null]) expect(safeUrl(u)).toBeNull();
  });
  it("every existing importer and the backup reader leave non-web links out and count them", () => {
    expect(parseOneTab(bad.map((u) => `${u} | t`).concat("https://ok.test | ok").join("\n"))).toMatchObject({ tabs: 1, skipped: bad.length });
    expect(parseSessionBuddy({ sessions: [{ windows: [{ tabs: [...bad.map((url) => ({ url })), { url: "https://ok.test" }] }] }] })).toMatchObject({ tabs: 1, skipped: bad.length });
    expect(parseCsv(`url,title\n${bad.map((u) => `"${u}",x`).join("\n")}\nhttps://ok.test,ok`)).toMatchObject({ tabs: 1, skipped: bad.length });
    const b = parseBackup(JSON.stringify({ format: "tab-lifeboat-backup", version: 1, sessions: [{ id: "a", windows: [{ tabs: [...bad.map((url) => ({ url })), { url: "https://ok.test" }] }] }] }));
    expect([b.tabs, b.skipped]).toEqual([1, bad.length]);
  });
  it("already-open check: exact address, only a trailing slash ignored", () => {
    expect(sameKey("https://a.test/x/")).toBe(sameKey("https://a.test/x"));
    expect(sameKey("https://a.test/?q=/")).toBe("https://a.test?q=/");
    expect(sameKey("https://a.test/#/doc/1")).not.toBe(sameKey("https://a.test/#/doc/2"));
    expect(sameKey("https://a.test/?utm_source=x")).not.toBe(sameKey("https://a.test/"));
  });
});

describe("rule 3: limits", () => {
  it("25,000-tab file is refused with its count; 20,000 is fine", () => {
    const lines = (k: number) => Array.from({ length: k }, (_, i) => `https://x.test/${i} | t${i}`).join("\n");
    expect(() => parseOneTab(lines(25_000))).toThrow("This file has 25,000 tabs; Tab Lifeboat imports up to 20,000 at a time. Split the file.");
    expect(parseOneTab(lines(20_000)).tabs).toBe(20_000);
  });
  it("more than 1,000 sessions/folders refused; backup over 20,000 tabs or 1,000 sessions refused", () => {
    expect(() => parseOneTab(Array.from({ length: 1001 }, (_, i) => `https://x.test/${i}`).join("\n\n"))).toThrow(/1,001 sessions or folders/);
    const sessions = Array.from({ length: 1001 }, (_, i) => ({ id: `s${i}`, windows: [{ tabs: [{ url: "https://x.test" }] }] }));
    expect(() => parseBackup(JSON.stringify({ format: "tab-lifeboat-backup", version: 1, sessions }))).toThrow(/1,001 sessions/);
    const big = [{ id: "a", windows: [{ tabs: Array.from({ length: 20_001 }, (_, i) => ({ url: `https://x.test/${i}` })) }] }];
    expect(() => parseBackup(JSON.stringify({ format: "tab-lifeboat-backup", version: 1, sessions: big }))).toThrow(/more than 20,000 tabs/);
  });
  it("JSON nested 100 deep is refused in plain words (no RangeError); bad JSON says nothing changed", () => {
    let deep: unknown = [{ url: "https://x.test" }]; for (let i = 0; i < 100; i++) deep = { a: deep };
    expect(() => detectAndParse(JSON.stringify(deep))).toThrow("This file is nested too deeply to be a session export. Nothing was changed.");
    expect(() => detectAndParse("{ not json")).toThrow("This file couldn't be read. Nothing was changed.");
  });
  it("text over 20 MB refused; titles cut to 1,000, names to 200, group titles to 100, single line", () => {
    expect(() => detectAndParse("x".repeat(CAPS.fileBytes + 1))).toThrow(/over 20 MB/);
    const p = parseOneTab(`https://x.test | ${"t".repeat(5000)}`);
    expect(p.session.windows[0]!.tabs[0]!.title).toHaveLength(1000);
    const b = parseBackup(JSON.stringify({ format: "tab-lifeboat-backup", version: 1, sessions: [{ id: "a", name: "n".repeat(900), windows: [{ groups: [{ key: "g", title: "g".repeat(900) }], tabs: [{ url: "https://x.test", title: "a\n\tb", groupKey: "g" }] }] }] }));
    expect([b.sessions[0]!.name.length, b.sessions[0]!.windows[0]!.groups[0]!.title.length, b.sessions[0]!.windows[0]!.tabs[0]!.title]).toEqual([200, 100, "a b"]);
    expect(clip(42, 10)).toBe("");
  });
  it("__proto__ in an import never pollutes objects", () => {
    const p = parseSessionBuddy('{"__proto__":{"polluted":1},"sessions":[{"windows":[{"tabs":[{"url":"https://x.test","__proto__":{"evil":1}}]}]}]}');
    expect(p.tabs).toBe(1);
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
    expect(Object.keys(p.session.windows[0]!.tabs[0]!).sort()).toEqual(["groupKey", "pinned", "title", "url"]);
  });
});

describe("restore asks first above 100 tabs; Open them anyway", () => {
  const btn = () => ({ textContent: "", disabled: false, onclick: null as null | (() => Promise<void>) });
  it("101 tabs: first tap asks, second opens; skipped pages offer \"Open N anyway\" which sends name=dupes", async () => {
    const sent: object[] = [];
    const send = async <T,>(m: object) => { sent.push(m); return ({ ok: true, tabs: 90, asleep: 89, alreadyOpen: 11 }) as unknown as T & { ok: boolean } };
    const b = btn(), st = { textContent: "" };
    wireRestore(b as unknown as HTMLButtonElement, st as unknown as HTMLElement, "s1", 101, send);
    await b.onclick!(); expect(sent).toEqual([]); expect(st.textContent).toMatch(/^Open 101 tabs\? They open asleep/);
    await b.onclick!(); expect(sent).toEqual([{ type: "restore", id: "s1" }]);
    expect([st.textContent, b.textContent]).toEqual(["Opened 90, skipped 11 already open, they load when clicked", "Open 11 anyway"]);
    await b.onclick!(); expect(sent[1]).toEqual({ type: "restore", id: "s1", name: "dupes" }); expect(st.textContent).toBe("Opened 90 again");
  });
  it("100 tabs or fewer open at once; errors are shown, not thrown", async () => {
    const send = async <T,>() => ({ ok: false, error: "Already restoring. One moment." }) as unknown as T & { ok: boolean };
    const b = btn(), st = { textContent: "" };
    wireRestore(b as unknown as HTMLButtonElement, st as unknown as HTMLElement, "s", 100, send);
    await b.onclick!(); expect(st.textContent).toBe("Already restoring. One moment.");
    expect(restoreText({ ok: true, tabs: 0, asleep: 0, alreadyOpen: 4 })).toBe("All 4 already open");
  });
});

describe("rule 7 + 2.6: storage failures and plain errors", () => {
  it("QuotaExceededError becomes the disk-full sentence; raw library errors never reach the user", () => {
    expect(errorText(new DOMException("x", "QuotaExceededError"))).toEqual({ text: DISK_FULL, diskFull: true });
    expect(errorText(new TypeError("Cannot read properties of undefined (reading 'x')")).text).toBe("Something went wrong. Nothing was changed. Try again.");
    expect(errorText(new Error("This file couldn't be read. Nothing was changed.")).text).toBe("This file couldn't be read. Nothing was changed.");
    expect(errorText("boom").diskFull).toBe(false);
  });
});
