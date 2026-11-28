// A357: v0.3 hardening leftovers. Restore never eats a newer edit; edits carry the version the page saw; gunzip cap.
import { describe, expect, it } from "vitest";
import { parseBackup, restorePlan, toBackup } from "../lib/backup";
import { gunzip, gzip } from "../lib/drive";
import { changedSince, version } from "../lib/edit";
import { checkMsg } from "../lib/messages";
import type { Session } from "../lib/model";

const s = (over: Partial<Session> = {}): Session => ({ id: "a", name: "Work", createdAt: 1_000, kind: "manual",
  windows: [{ tabs: [{ url: "https://a.example/", title: "A" }], groups: [] }], ...over });
const ids = () => "new-id";

describe("restorePlan (backup restore vs newer edits)", () => {
  it("adds a session that is not stored", () => expect(restorePlan(undefined, s(), ids)).toEqual([s()]));
  it("same id and same tabs: writes nothing (restoring twice never doubles)", () => expect(restorePlan(s(), s(), ids)).toEqual([]));
  it("edit, then restore the old backup: the edit survives and the backup is kept as a copy", () => {
    const edited = s({ name: "Work 2", updatedAt: 5_000 });
    const out = restorePlan(edited, s(), ids);
    expect(out).toHaveLength(1);
    expect(out[0]?.id).toBe("new-id");
    expect(out[0]?.name).toMatch(/^Work \(from backup \d{1,2} [A-Z][a-z]{2}\)$/);
  });
  it("pre-updatedAt data with different tabs (same version): keeps both", () => {
    const local = s({ windows: [{ tabs: [{ url: "https://b.example/", title: "B" }], groups: [] }] });
    expect(restorePlan(local, s(), ids)[0]?.id).toBe("new-id");
  });
  it("a strictly newer backup replaces the older stored copy", () => {
    const newer = s({ name: "Work 3", updatedAt: 9_000 });
    expect(restorePlan(s({ updatedAt: 2_000 }), newer, ids)).toEqual([newer]);
  });
  it("updatedAt survives a backup round trip; junk updatedAt is dropped", () => {
    const text = JSON.stringify(toBackup([s({ updatedAt: 7_000 }), s({ id: "b", updatedAt: "x" as unknown as number })]));
    const p = parseBackup(text);
    expect(p.sessions[0]?.updatedAt).toBe(7_000);
    expect(p.sessions[1]?.updatedAt).toBeUndefined();
  });
  it("a long name stays within the name cap", () => {
    const out = restorePlan(s({ name: "x".repeat(200), updatedAt: 9 }), s({ name: "y".repeat(200) }), ids);
    expect(out[0]?.name.length).toBeLessThanOrEqual(200);
  });
});

describe("edit conflict check (two open pages)", () => {
  it("version is updatedAt, or createdAt before any edit", () => {
    expect(version(s())).toBe(1_000);
    expect(version(s({ updatedAt: 3_000 }))).toBe(3_000);
  });
  it("same version: no conflict; another window edited: conflict; old caller with no version: allowed", () => {
    expect(changedSince(s(), 1_000)).toBe(false);
    expect(changedSince(s({ updatedAt: 3_000 }), 1_000)).toBe(true);
    expect(changedSince(s({ updatedAt: 3_000 }))).toBe(false);
  });
  it("messages accept a whole-number version and refuse anything else", () => {
    expect(checkMsg({ type: "rename", id: "a", v: 1_732_000_000_000 })?.v).toBe(1_732_000_000_000);
    for (const v of [-1, 1.5, "1", Number.MAX_SAFE_INTEGER + 2, {}]) expect(checkMsg({ type: "rename", id: "a", v })).toBeNull();
  });
});

describe("gunzip size cap (gzip bomb)", () => {
  it("unpacks a normal backup", async () => expect(await gunzip(await gzip("héllo"))).toBe("héllo"));
  it("stops when the unpacked size passes the cap", async () => {
    const bomb = await gzip("0".repeat(5 * 1024 * 1024));   // 5 MB of zeros packs to a few kB
    expect(bomb.byteLength).toBeLessThan(64 * 1024);
    await expect(gunzip(bomb, 1024 * 1024)).rejects.toThrow(/too big/);
  });
  it("a 3 MB backup round-trips through gzip", async () => {
    const big = JSON.stringify(toBackup([s({ windows: [{ tabs: Array.from({ length: 20_000 }, (_, i) => ({ url: `https://e.example/${i}?q=${"é".repeat(40)}`, title: `T ${i} 🚀` })), groups: [] }] })]));
    expect(big.length).toBeGreaterThan(3 * 1024 * 1024 / 2);
    expect(await gunzip(await gzip(big))).toBe(big);
  });
});
