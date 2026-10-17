import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import { stamp } from "../lib/capture";
import { BACKUP_FORMAT, backupFileName, parseBackup, toBackup } from "../lib/backup";
import type { Session } from "../lib/model";
import { _clearForTests, listSessions, putSession } from "../lib/store";

const s = (id: string, kind: Session["kind"], urls: string[], at = 1_760_000_000_000): Session => ({
  id, name: `S ${id}`, createdAt: at, kind,
  windows: [{ tabs: urls.map((url, i) => ({ url, title: `T${i}`, groupKey: i ? "g1" : null })), groups: [{ key: "g1", title: "Work", color: "purple", collapsed: true }] }],
});

describe("backup file (free off-device backup, research gap 7)", () => {
  beforeEach(async () => { await _clearForTests(); });

  it("round-trips every session, group names, colours and collapsed state", () => {
    const all = [s("a", "manual", ["https://a.test", "https://b.test"]), s("b", "auto", ["https://c.test"])];
    const p = parseBackup(JSON.stringify(toBackup(all, 1_760_100_000_000)));
    expect(p.sessions).toEqual(all);
    expect([p.tabs, p.groups, p.skipped]).toEqual([3, 2, 0]);
  });

  it("file has format, version and export time; name is dated in IST", () => {
    const b = toBackup([], Date.UTC(2026, 9, 16, 20, 0)); // 01:30 IST on 17 Oct
    expect([b.format, b.version, b.exportedAt]).toEqual([BACKUP_FORMAT, 1, "2026-10-16T20:00:00.000Z"]);
    expect(backupFileName(Date.UTC(2026, 9, 16, 20, 0))).toBe("tab-lifeboat-backup-2026-10-17.json");
  });

  it("restoring the same file twice does not duplicate sessions (ids are kept)", async () => {
    const text = JSON.stringify(toBackup([s("a", "manual", ["https://a.test"])]));
    for (let i = 0; i < 2; i++) for (const x of parseBackup(text).sessions) await putSession(x);
    expect((await listSessions()).length).toBe(1);
  });

  it("drops unsafe URLs (file:, javascript:, data:) and counts them as skipped", () => {
    const text = JSON.stringify(toBackup([s("a", "import", ["https://ok.test", "file:///etc/passwd", "javascript:alert(1)", "data:text/html,x"])]));
    const p = parseBackup(text);
    expect(p.sessions[0]!.windows[0]!.tabs.map((t) => t.url)).toEqual(["https://ok.test"]);
    expect([p.tabs, p.skipped]).toEqual([1, 3]);
  });

  it("refuses files that are not a Tab Lifeboat backup, or a newer version", () => {
    expect(() => parseBackup("not json")).toThrow(/not a Tab Lifeboat backup/);
    expect(() => parseBackup(JSON.stringify({ format: "other", version: 1, sessions: [] }))).toThrow(/not a Tab Lifeboat backup/);
    expect(() => parseBackup(JSON.stringify({ format: BACKUP_FORMAT, version: 9, sessions: [] }))).toThrow(/newer version/);
  });

  it("cleans bad fields: unknown kind becomes import, bad colour becomes grey, missing name is filled", () => {
    const raw = { format: BACKUP_FORMAT, version: 1, sessions: [{ id: "x", createdAt: 5, kind: "evil", windows: [{ tabs: [{ url: "https://a.test" }], groups: [{ key: "k", title: "G", color: "neon" }] }] }] };
    const p = parseBackup(JSON.stringify(raw));
    expect(p.sessions[0]).toMatchObject({ id: "x", kind: "import", name: "Restored session" });
    expect(p.sessions[0]!.windows[0]!.groups[0]).toEqual({ key: "k", title: "G", color: "grey", collapsed: false });
    expect(p.sessions[0]!.windows[0]!.tabs[0]!.title).toBe("https://a.test");
  });

  it("10,000 tabs parse in well under a second", () => {
    const big = Array.from({ length: 100 }, (_, i) => s(`s${i}`, "manual", Array.from({ length: 100 }, (_, j) => `https://e.test/${i}/${j}`)));
    const t0 = performance.now(); const p = parseBackup(JSON.stringify(toBackup(big)));
    expect(p.tabs).toBe(10_000); expect(performance.now() - t0).toBeLessThan(1000);
  });
});

describe("names", () => {
  it("snapshot names use '17 Oct, 8:46 pm', never the US 10/17 order", () => {
    expect(stamp(new Date(2026, 9, 17, 20, 46))).toBe("17 Oct, 8:46 pm");
    expect(stamp(new Date(2026, 0, 5, 9, 5))).toBe("5 Jan, 9:05 am");
  });
});
