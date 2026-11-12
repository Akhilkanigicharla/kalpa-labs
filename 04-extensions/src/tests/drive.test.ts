import { describe, expect, it } from "vitest";
import { DriveError, backoff, call, deviceName, download, driveFileName, gunzip, gzip, list, remove, sha256, toPrune, upload, type DriveDeps, type DriveFile } from "../lib/drive";

// ---- an in-memory Google Drive app folder, speaking just enough of the real REST shapes
function fakeDrive(opts: { pageSize?: number } = {}) {
  const files: (DriveFile & { bytes: Uint8Array })[] = [];
  const calls: { method: string; url: string; auth: string }[] = [];
  const failures: (number | "network" | { status: number; reason: string; retryAfter?: string })[] = [];   // consumed one per request
  let validToken = "t1"; let n = 0;
  const f = async (url: string | URL | Request, init: RequestInit = {}) => {
    const u = new URL(String(url)); const method = init.method ?? "GET";
    const auth = String((init.headers as Record<string, string>)?.Authorization ?? "");
    calls.push({ method, url: u.toString(), auth });
    const fail = failures.shift();
    if (fail === "network") throw new TypeError("Failed to fetch");
    if (typeof fail === "number") return new Response("{}", { status: fail });
    if (fail) return new Response(JSON.stringify({ error: { errors: [{ reason: fail.reason }] } }), { status: fail.status, headers: fail.retryAfter ? { "retry-after": fail.retryAfter } : {} });
    if (auth !== `Bearer ${validToken}`) return new Response("{}", { status: 401 });
    if (method === "POST" && u.pathname === "/upload/drive/v3/files") {
      const raw = new Uint8Array(await new Response(init.body as Blob).arrayBuffer());
      const text = new TextDecoder("latin1").decode(raw);
      const boundary = /boundary=(\S+)/.exec(String((init.headers as Record<string, string>)["Content-Type"]))![1]!;
      const parts = text.split(`--${boundary}`);
      const meta = JSON.parse(new TextDecoder().decode(raw.slice(text.indexOf("{"), text.indexOf("}\r\n--") + 1)));
      const start = text.indexOf("\r\n\r\n", text.indexOf("Content-Type: application/gzip")) + 4;
      const end = text.lastIndexOf(`\r\n--${boundary}--`);
      expect(parts.length).toBe(4); expect(meta.parents).toEqual(["appDataFolder"]);
      const file = { id: `f${++n}`, name: meta.name, size: end - start, createdTime: new Date(Date.UTC(2026, 10, 12, 0, n)).toISOString(), appProperties: meta.appProperties, bytes: raw.slice(start, end) };
      files.push(file); const { bytes: _b, ...pub } = file; return Response.json(pub);
    }
    if (method === "GET" && u.pathname === "/drive/v3/files") {
      expect(u.searchParams.get("spaces")).toBe("appDataFolder");
      const size = opts.pageSize ?? 100; const from = Number(u.searchParams.get("pageToken") || 0);
      const sorted = [...files].sort((a, b) => b.createdTime.localeCompare(a.createdTime)).map(({ bytes: _b, ...pub }) => pub);
      return Response.json({ files: sorted.slice(from, from + size), ...(from + size < sorted.length ? { nextPageToken: String(from + size) } : {}) });
    }
    const id = u.pathname.split("/").pop()!; const i = files.findIndex((x) => x.id === id);
    if (i < 0) return new Response("{}", { status: 404 });
    if (method === "DELETE") { files.splice(i, 1); return new Response(null, { status: 204 }); }
    return new Response(files[i]!.bytes as BlobPart);
  };
  const slept: number[] = []; const dropped: string[] = []; let tokenNow = "t1"; let signedIn = true;
  const deps: DriveDeps = {
    fetch: f as typeof fetch,
    token: async () => { if (!signedIn) throw new Error("not signed in"); return tokenNow; },
    dropToken: async (t) => { dropped.push(t); tokenNow = "t2"; },
    sleep: async (ms) => { slept.push(ms); },
  };
  return { deps, files, calls, failures, slept, dropped, rotate: () => { validToken = "t2"; }, signOut: () => { signedIn = false; } };
}
const meta = (n = 1) => ({ name: driveFileName(Date.UTC(2026, 10, 12)), appProperties: { format: "tab-lifeboat-backup", v: "1", sessions: String(n), tabs: "20", device: "Chrome on Windows", hash: "abc" } });

describe("Google Drive backup (Pro)", () => {
  it("gzips, uploads into the hidden app folder, lists, downloads and unzips the exact text (Telugu + emoji)", async () => {
    const d = fakeDrive(); const text = JSON.stringify({ sessions: [{ name: "తెలుగు 🚀", tabs: Array.from({ length: 500 }, (_, i) => `https://x.test/${i}`) }] });
    const gz = await gzip(text);
    expect(gz.length).toBeLessThan(text.length / 3);                    // 500 similar URLs compress well
    const f = await upload(d.deps, gz, meta());
    expect(f.appProperties.device).toBe("Chrome on Windows");
    const all = await list(d.deps);
    expect(all.map((x) => x.id)).toEqual([f.id]);
    expect(await gunzip(await download(d.deps, f.id))).toBe(text);
    expect(d.calls.every((c) => c.auth === "Bearer t1")).toBe(true);
  });
  it("lists across pages and ignores files that aren't Tab Lifeboat backups", async () => {
    const d = fakeDrive({ pageSize: 2 });
    for (let i = 0; i < 5; i++) await upload(d.deps, await gzip("{}"), meta(i));
    await upload(d.deps, await gzip("{}"), { name: "other.json", appProperties: {} });
    const all = await list(d.deps);
    expect(all.length).toBe(5);
    expect(all[0]!.createdTime > all[4]!.createdTime).toBe(true);       // newest first
  });
  it("expired token: drops it, gets a fresh one and retries once", async () => {
    const d = fakeDrive(); d.rotate();
    await upload(d.deps, await gzip("{}"), meta());
    expect(d.dropped).toEqual(["t1"]); expect(d.files.length).toBe(1);
  });
  it("signed out: a plain 'sign-in needed' error, no retry loop", async () => {
    const d = fakeDrive(); d.signOut();
    const e = await upload(d.deps, await gzip("{}"), meta()).catch((x) => x);
    expect(e).toBeInstanceOf(DriveError); expect(e.kind).toBe("signed-out"); expect(d.calls.length).toBe(0);
  });
  it("503 and 429 are retried with backoff (Retry-After honoured), then succeed", async () => {
    const d = fakeDrive(); d.failures.push(503, { status: 429, reason: "rateLimitExceeded", retryAfter: "3" });
    await upload(d.deps, await gzip("{}"), meta());
    expect(d.files.length).toBe(1); expect(d.slept.length).toBe(2); expect(d.slept[1]).toBe(3000);
  });
  it("gives up after 4 tries with a 'busy' or 'server' message, never loops forever", async () => {
    const d = fakeDrive(); d.failures.push(503, 503, 503, 503);
    const e = await list(d.deps).catch((x) => x);
    expect([e.kind, d.calls.length]).toEqual(["server", 4]);
  });
  it("Drive full: tells the user to free space, does not retry", async () => {
    const d = fakeDrive(); d.failures.push({ status: 403, reason: "storageQuotaExceeded" });
    const e = await upload(d.deps, await gzip("{}"), meta()).catch((x) => x);
    expect(e.kind).toBe("quota"); expect(e.message).toMatch(/Drive is full/); expect(d.calls.length).toBe(1);
  });
  it("offline: retried 3 times, then 'no internet' (not a crash)", async () => {
    const d = fakeDrive(); d.failures.push("network", "network", "network", "network");
    const e = await list(d.deps).catch((x) => x);
    expect([e.kind, d.calls.length]).toEqual(["offline", 4]);
  });
  it("a 400 is not retried (a retry would fail the same way)", async () => {
    const d = fakeDrive(); d.failures.push(400);
    expect((await list(d.deps).catch((x) => x)).kind).toBe("bad"); expect(d.calls.length).toBe(1);
  });
  it("refuses odd file ids instead of building a URL from them", async () => {
    const d = fakeDrive();
    for (const id of ["../files", "a/b", "x?alt=media&y", ""]) expect((await download(d.deps, id).catch((x) => x)).kind).toBe("bad");
    await expect(remove(d.deps, "../../x")).rejects.toThrow(DriveError);
    expect(d.calls.length).toBe(0);
  });
  it("retention: every backup from the last 48 h, then one per day for 30 days, unknown dates never deleted", () => {
    const now = Date.UTC(2026, 10, 30, 12); const H = 3_600_000;
    const mk = (id: string, hoursAgo: number): DriveFile => ({ id, name: id, size: 1, createdTime: new Date(now - hoursAgo * H).toISOString(), appProperties: {} });
    const files = [mk("h1", 1), mk("h47", 47), mk("d3a", 72), mk("d3b", 73), mk("d10", 240), mk("old", 31 * 24), { ...mk("weird", 0), createdTime: "?" }];
    expect(toPrune(files, now).sort()).toEqual(["d3b", "old"]);
  });
  it("small helpers: backoff doubles with jitter, device names, file names, stable hashes", async () => {
    expect([backoff(0, () => 0), backoff(1, () => 0), backoff(2, () => 0.999)]).toEqual([1000, 2000, 4249]);
    expect(deviceName("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0 Safari/537.36")).toBe("Chrome on Windows");
    expect(deviceName("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/157.0 Safari/537.36 Edg/157.0")).toBe("Edge on Mac");
    expect(driveFileName(Date.UTC(2026, 10, 12, 16, 35, 9, 123))).toBe("tab-lifeboat-2026-11-12T16-35-09Z.json.gz");
    expect(await sha256("a")).toBe(await sha256("a")); expect(await sha256("a")).not.toBe(await sha256("b"));
  });
});
