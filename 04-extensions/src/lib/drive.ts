// Tab Lifeboat Pro: backup to the user's own Google Drive (hidden app folder, scope drive.appdata).
// Pure logic with injected fetch/token/sleep so every failure path is unit-tested against a fake Drive.
// Google docs (12 Nov 2026): files go in parents ["appDataFolder"], are listed with spaces=appDataFolder,
// and drive.appdata is a "Recommended, Non-sensitive" scope. Only this extension can see that folder.

export const DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.appdata";
const API = "https://www.googleapis.com/drive/v3/files";
const UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,size,createdTime,appProperties";
export const TIMEOUT_MS = 20_000;
const RETRY_STATUS = new Set([429, 500, 502, 503, 504]);

export interface DriveDeps {
  fetch: typeof fetch;
  /** OAuth access token (chrome.identity.getAuthToken). interactive=false must never show UI. */
  token(interactive: boolean): Promise<string>;
  /** Forget a token Google rejected (chrome.identity.removeCachedAuthToken). */
  dropToken(token: string): Promise<void>;
  sleep(ms: number): Promise<void>;
}

export type DriveErrorKind = "signed-out" | "offline" | "quota" | "busy" | "server" | "bad";
export class DriveError extends Error {
  constructor(readonly kind: DriveErrorKind, message: string, readonly status = 0) { super(message); this.name = "DriveError"; }
}
const MESSAGES: Record<DriveErrorKind, string> = {
  "signed-out": "Google sign-in needed. Press Connect Google Drive again.",
  offline: "No internet right now. Tab Lifeboat will try again in an hour.",
  quota: "Your Google Drive is full. Free up space, then press Back up now.",
  busy: "Google Drive is busy. Tab Lifeboat will try again in an hour.",
  server: "Google Drive had a problem. Tab Lifeboat will try again in an hour.",
  bad: "Google Drive refused this backup. Please email us so we can fix it.",
};
export const driveError = (kind: DriveErrorKind, status = 0) => new DriveError(kind, MESSAGES[kind], status);

export interface DriveFile {
  id: string; name: string; size: number; createdTime: string;
  appProperties: { format?: string; v?: string; sessions?: string; tabs?: string; device?: string; hash?: string };
}

/** One HTTP call with timeout, token refresh on 401 (once) and backoff on 429/5xx (up to 4 tries). */
export async function call(d: DriveDeps, url: string, init: RequestInit = {}, interactive = false): Promise<Response> {
  let token = await d.token(interactive).catch(() => { throw driveError("signed-out"); });
  let refreshed = false;
  for (let attempt = 0; ; attempt++) {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), TIMEOUT_MS);
    let res: Response;
    try {
      res = await d.fetch(url, { ...init, signal: ac.signal, headers: { ...(init.headers as Record<string, string>), Authorization: `Bearer ${token}` } });
    } catch {
      if (attempt < 3) { await d.sleep(backoff(attempt)); continue; }   // network blip or timeout
      throw driveError("offline");
    } finally { clearTimeout(timer); }
    if (res.ok) return res;
    if (res.status === 401 && !refreshed) {          // token expired or revoked: drop it and ask Chrome for a fresh one
      refreshed = true; await d.dropToken(token);
      token = await d.token(false).catch(() => { throw driveError("signed-out"); });
      continue;
    }
    if (res.status === 401) throw driveError("signed-out", 401);
    const reason = await errorReason(res);
    if (res.status === 403 && reason === "storageQuotaExceeded") throw driveError("quota", 403);
    const retryable = RETRY_STATUS.has(res.status) || (res.status === 403 && /rateLimitExceeded|userRateLimitExceeded/.test(reason));
    if (retryable && attempt < 3) { await d.sleep(retryAfter(res) ?? backoff(attempt)); continue; }
    if (retryable) throw driveError(res.status === 429 || res.status === 403 ? "busy" : "server", res.status);
    throw driveError("bad", res.status);
  }
}

/** 1 s, 2 s, 4 s, plus up to 250 ms jitter so many browsers don't retry in step. */
export function backoff(attempt: number, rand = Math.random) { return 1000 * 2 ** attempt + Math.floor(rand() * 250); }
function retryAfter(res: Response): number | null {
  const s = Number(res.headers.get("retry-after"));
  return Number.isFinite(s) && s > 0 ? Math.min(s, 60) * 1000 : null;
}
async function errorReason(res: Response): Promise<string> {
  try { const j = await res.clone().json(); return String(j?.error?.errors?.[0]?.reason ?? j?.error?.status ?? ""); } catch { return ""; }
}

/** Upload one gzipped backup into the hidden app folder. */
export async function upload(d: DriveDeps, gz: Uint8Array, meta: { name: string; appProperties: DriveFile["appProperties"] }, interactive = false): Promise<DriveFile> {
  const boundary = `lifeboat-${Math.random().toString(36).slice(2)}`;
  const head = `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify({ name: meta.name, parents: ["appDataFolder"], mimeType: "application/gzip", appProperties: meta.appProperties })}\r\n--${boundary}\r\nContent-Type: application/gzip\r\n\r\n`;
  const body = new Blob([head, gz as BlobPart, `\r\n--${boundary}--`]);
  const res = await call(d, UPLOAD, { method: "POST", headers: { "Content-Type": `multipart/related; boundary=${boundary}` }, body }, interactive);
  return normalise(await res.json());
}

/** Every backup in the app folder, newest first (follows page tokens). */
export async function list(d: DriveDeps, interactive = false): Promise<DriveFile[]> {
  const out: DriveFile[] = [];
  let page = "";
  for (let i = 0; i < 50; i++) {   // 50 pages × 100 = far more than the retention keeps; stops a runaway loop
    const q = new URLSearchParams({ spaces: "appDataFolder", pageSize: "100", orderBy: "createdTime desc", fields: "nextPageToken,files(id,name,size,createdTime,appProperties)" });
    if (page) q.set("pageToken", page);
    const j = await (await call(d, `${API}?${q}`, {}, interactive)).json();
    for (const f of j.files ?? []) out.push(normalise(f));
    page = j.nextPageToken ?? "";
    if (!page) break;
  }
  return out.filter((f) => f.appProperties.format === "tab-lifeboat-backup");
}

export async function download(d: DriveDeps, id: string): Promise<Uint8Array> {
  if (!/^[\w-]{1,200}$/.test(id)) throw driveError("bad");   // ids come from list(); never build a URL from anything else
  return new Uint8Array(await (await call(d, `${API}/${id}?alt=media`)).arrayBuffer());
}

export async function remove(d: DriveDeps, id: string): Promise<void> {
  if (!/^[\w-]{1,200}$/.test(id)) throw driveError("bad");
  await call(d, `${API}/${id}`, { method: "DELETE" });
}

function normalise(f: Record<string, unknown>): DriveFile {
  return { id: String(f.id ?? ""), name: String(f.name ?? ""), size: Number(f.size ?? 0), createdTime: String(f.createdTime ?? ""), appProperties: (f.appProperties as DriveFile["appProperties"]) ?? {} };
}

/** Retention: keep every backup from the last 48 hours, then the newest one of each day for 30 days. Returns ids to delete. */
export function toPrune(files: DriveFile[], now = Date.now()): string[] {
  const H = 3_600_000, D = 24 * H;
  const keep = new Set<string>(); const days = new Set<string>();
  for (const f of [...files].sort((a, b) => Date.parse(b.createdTime) - Date.parse(a.createdTime))) {
    const t = Date.parse(f.createdTime);
    if (!Number.isFinite(t)) continue;               // unknown date: leave it alone rather than delete it
    const age = now - t;
    if (age <= 48 * H) { keep.add(f.id); continue; }
    if (age > 30 * D) continue;
    const day = new Date(t).toISOString().slice(0, 10);
    if (!days.has(day)) { days.add(day); keep.add(f.id); }
  }
  return files.filter((f) => Number.isFinite(Date.parse(f.createdTime)) && !keep.has(f.id)).map((f) => f.id);
}

export async function gzip(text: string): Promise<Uint8Array> {
  const stream = new Blob([text]).stream().pipeThrough(new CompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}
export async function gunzip(bytes: Uint8Array): Promise<string> {
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream("gzip"));
  return await new Response(stream).text();
}
export async function sha256(text: string): Promise<string> {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** "Chrome on Windows": shown next to each backup so people with several computers know which is which. */
export function deviceName(ua = globalThis.navigator?.userAgent ?? ""): string {
  const os = /Windows/.test(ua) ? "Windows" : /CrOS/.test(ua) ? "ChromeOS" : /Mac OS X|Macintosh/.test(ua) ? "Mac" : /Android/.test(ua) ? "Android" : /Linux/.test(ua) ? "Linux" : "a computer";
  const br = /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Chrome\//.test(ua) ? "Chrome" : "Browser";
  return `${br} on ${os}`;
}

/** tab-lifeboat-2026-11-12T22-05-00Z.json.gz */
export const driveFileName = (now = Date.now()) => `tab-lifeboat-${new Date(now).toISOString().replace(/\.\d+Z$/, "Z").replace(/:/g, "-")}.json.gz`;
