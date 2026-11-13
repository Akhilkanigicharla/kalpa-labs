import { captureAll, restore } from "../lib/capture";
import { detectAndParse } from "../lib/importers";
import { backupFileName, parseBackup, toBackup } from "../lib/backup";
import { countTabs } from "../lib/model";
import { LIMITS, deleteSession, getSession, listSessions, pruneAuto, putSession } from "../lib/store";
import { DRIVE_SCOPE, DriveError, deviceName, driveFileName, gunzip, gzip, list as driveList, download as driveDownload, remove as driveRemove, sha256, toPrune, upload as driveUpload, type DriveDeps } from "../lib/drive";
import { backupDue, findDuplicates, findStale, searchTabs, tabTimeline, upgradeNudge, type OpenTab } from "../lib/tools";

export const SNAPSHOT_MINUTES = 5;

async function plan(): Promise<"free" | "pro"> {
  const { plan } = await browser.storage.local.get("plan");
  return plan === "pro" ? "pro" : "free";
}

async function snapshot() {
  const s = await captureAll(browser, "auto");
  if (countTabs(s).tabs === 0) return null;
  await putSession(s);
  await pruneAuto(await plan());
  await browser.storage.local.set({ lastSnapshot: s.createdAt }); // shown in the popup: proof backups happen
  return s;
}

const STALE_DAYS = 7;

async function openTabs(): Promise<OpenTab[]> {
  return (await browser.tabs.query({})).filter((t) => t.id !== undefined && t.url)
    .map((t) => ({ id: t.id!, url: t.url!, pinned: !!t.pinned, active: !!t.active, audible: !!t.audible, lastAccessed: (t as { lastAccessed?: number }).lastAccessed }));
}

/** Pro: one backup file a day in Downloads/Tab Lifeboat/ (needs the optional "downloads" permission the user grants). */
async function dailyBackup(now = Date.now()) {
  if ((await plan()) !== "pro") return null;
  const { lastBackupAt, dailyBackupOn } = await browser.storage.local.get(["lastBackupAt", "dailyBackupOn"]);
  if (!dailyBackupOn || !backupDue((lastBackupAt as number) ?? null, now)) return null;
  if (!(await browser.permissions.contains({ permissions: ["downloads"] }))) return null;
  const json = JSON.stringify(toBackup(await listSessions(), now));
  const url = `data:application/json;charset=utf-8,${encodeURIComponent(json)}`;
  await browser.downloads.download({ url, filename: `Tab Lifeboat/${backupFileName(now)}`, saveAs: false, conflictAction: "overwrite" });
  await browser.storage.local.set({ lastBackupAt: now });
  return now;
}

// ---- Pro: backup to the user's own Google Drive (hidden app folder). Plan: 04-extensions/docs/drive-backup-plan.md
const hasClientId = () => !!(browser.runtime.getManifest() as { oauth2?: { client_id?: string } }).oauth2?.client_id;
const driveDeps: DriveDeps = {
  fetch: (...a) => fetch(...a),
  token: async (interactive) => {
    if (!hasClientId()) throw new Error("no client id");
    const r = await browser.identity.getAuthToken({ interactive, scopes: [DRIVE_SCOPE] }) as unknown as { token?: string } | string;
    const t = typeof r === "string" ? r : r?.token;
    if (!t) throw new Error("no token");
    return t;
  },
  dropToken: async (token) => { await browser.identity.removeCachedAuthToken({ token }); },
  sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
};
type DriveState = { driveOn?: boolean; lastDriveAt?: number; lastDriveHash?: string; lastDriveError?: { message: string; kind: string; at: number } | null };
let driveRunning: Promise<unknown> | null = null;   // one backup at a time (alarm + button can't race)

/** Upload a backup if Drive is on and something changed since the last upload (force = the "Back up now" button). */
async function driveBackup(force = false, interactive = false): Promise<{ uploaded: boolean; at?: number }> {
  if ((await plan()) !== "pro") return { uploaded: false };
  const st = (await browser.storage.local.get(["driveOn", "lastDriveHash"])) as DriveState;
  if (!st.driveOn || !(await browser.permissions.contains({ permissions: ["identity"] }))) return { uploaded: false };
  const sessions = await listSessions();
  if (!sessions.length) return { uploaded: false };
  const json = JSON.stringify(toBackup(sessions.map((x) => ({ ...x })).sort((a, b) => a.createdAt - b.createdAt), 0));   // exportedAt=0 so the hash only changes when tabs change
  const hash = await sha256(json);
  if (!force && hash === st.lastDriveHash) return { uploaded: false };
  const now = Date.now();
  try {
    const counts = sessions.reduce((n, x) => n + countTabs(x).tabs, 0);
    await driveUpload(driveDeps, await gzip(JSON.stringify(toBackup(sessions, now))), { name: driveFileName(now),
      appProperties: { format: "tab-lifeboat-backup", v: "1", sessions: String(sessions.length), tabs: String(counts), device: deviceName(), hash } }, interactive);
    await browser.storage.local.set({ lastDriveAt: now, lastDriveHash: hash, lastDriveError: null });
    try { for (const id of toPrune(await driveList(driveDeps), now)) await driveRemove(driveDeps, id); } catch { /* pruning can wait for the next run */ }
    return { uploaded: true, at: now };
  } catch (e) {
    const err = e instanceof DriveError ? { message: e.message, kind: e.kind } : { message: "Google Drive backup failed. Tab Lifeboat will try again in an hour.", kind: "server" };
    await browser.storage.local.set({ lastDriveError: { ...err, at: now } });
    throw e;
  }
}
const driveOnce = (force: boolean, interactive = false) => {
  if (!driveRunning) driveRunning = driveBackup(force, interactive).finally(() => { driveRunning = null; });
  return driveRunning as Promise<{ uploaded: boolean; at?: number }>;
};
const driveMsg = (e: unknown) => (e instanceof DriveError ? e.message : "Google Drive isn't reachable right now. Try again in a minute.");

export default defineBackground(() => {
  // ask the browser not to evict our IndexedDB under disk pressure (OneTab users lost data this way)
  void (globalThis.navigator?.storage?.persist?.() ?? Promise.resolve(false));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("drive-backup", { periodInMinutes: 60 }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("drive-backup", { periodInMinutes: 60 }));
  browser.alarms.onAlarm.addListener((a) => {
    if (a.name === "snapshot") void snapshot();
    if (a.name === "daily-backup") void dailyBackup();
    if (a.name === "drive-backup") void driveOnce(false).catch(() => { /* error saved for the settings page */ });
  });

  browser.runtime.onMessage.addListener((msg: { type: string; id?: string; text?: string; name?: string }, _sender, reply) => {
    (async () => {
      const br = browser;
      switch (msg.type) {
        case "save": { const s = await captureAll(br, "manual", msg.name); await putSession(s); return { ok: true, session: s, counts: countTabs(s) }; }
        case "snapshot": return { ok: true, session: await snapshot() };
        case "status": { const { lastSnapshot, lastFileAt, lastBackupAt } = await browser.storage.local.get(["lastSnapshot", "lastFileAt", "lastBackupAt"]); const files = [lastFileAt, lastBackupAt].filter((x): x is number => typeof x === "number"); return { ok: true, lastSnapshot: lastSnapshot ?? null, lastFileAt: files.length ? Math.max(...files) : null, sessions: (await listSessions()).length, persisted: (await globalThis.navigator?.storage?.persisted?.()) ?? false, plan: await plan(), every: SNAPSHOT_MINUTES, limits: LIMITS }; }
        case "list": return { ok: true, sessions: (await listSessions()).map((s) => ({ id: s.id, name: s.name, kind: s.kind, createdAt: s.createdAt, ...countTabs(s) })) };
        case "restore": { const s = await getSession(msg.id!); if (!s) return { ok: false, error: "not found" }; return { ok: true, ...(await restore(br, s)) }; }
        case "delete": await deleteSession(msg.id!); return { ok: true };
        case "preview-import": { const p = detectAndParse(msg.text ?? ""); return { ok: true, tabs: p.tabs, groups: p.groups, skipped: p.skipped, format: p.format }; }
        case "import": {
          const p = detectAndParse(msg.text ?? ""); await putSession(p.session);
          const { lastNudge } = await browser.storage.local.get("lastNudge"); const now = Date.now();
          const nudge = upgradeNudge({ plan: await plan(), importedTabs: p.tabs, lastNudge: (lastNudge as number) ?? null, now });
          if (nudge) await browser.storage.local.set({ lastNudge: now });
          return { ok: true, id: p.session.id, tabs: p.tabs, groups: p.groups, nudge };
        }
        case "search": return { ok: true, hits: searchTabs(await listSessions(), msg.text ?? "") };
        case "rename": { const s = await getSession(msg.id!); if (!s) return { ok: false, error: "not found" }; s.name = (msg.name ?? "").trim().slice(0, 80) || s.name; await putSession(s); return { ok: true }; }
        case "cleanup-preview": { if ((await plan()) !== "pro") return { ok: false, error: "pro" }; const t = await openTabs(); return { ok: true, duplicates: findDuplicates(t).length, stale: findStale(t, STALE_DAYS).length, days: STALE_DAYS }; }
        case "cleanup": { // saves everything first, so a cleanup can always be undone from the list
          if ((await plan()) !== "pro") return { ok: false, error: "pro" };
          const t = await openTabs(); const ids = [...new Set([...findDuplicates(t), ...(msg.name === "stale" ? findStale(t, STALE_DAYS) : [])])];
          if (!ids.length) return { ok: true, closed: 0 };
          await putSession(await captureAll(br, "manual", "Before cleanup"));
          await browser.tabs.remove(ids); return { ok: true, closed: ids.length };
        }
        case "timeline": { if ((await plan()) !== "pro") return { ok: false, error: "pro" }; return { ok: true, timeline: tabTimeline(await listSessions(), msg.text ?? "") }; }
        case "daily-backup": { await browser.storage.local.set({ dailyBackupOn: msg.name === "on" }); return { ok: true, made: msg.name === "on" ? await dailyBackup() : null }; }
        case "drive-status": {
          const st = (await browser.storage.local.get(["driveOn", "lastDriveAt", "lastDriveError"])) as DriveState;
          return { ok: true, ready: hasClientId(), pro: (await plan()) === "pro", on: !!st.driveOn && (await browser.permissions.contains({ permissions: ["identity"] })), lastAt: st.lastDriveAt ?? null, error: st.lastDriveError ?? null };
        }
        case "drive-connect": {   // the page asked for the "identity" permission first, inside the user's click
          if ((await plan()) !== "pro") return { ok: false, error: "pro" };
          if (!hasClientId()) return { ok: false, error: "Google Drive backup is being set up. It arrives in the next update." };
          try { await driveDeps.token(true); await driveList(driveDeps); } catch (e) { return { ok: false, error: e instanceof DriveError ? e.message : "Google sign-in was cancelled. Press Connect again when you're ready." }; }
          await browser.storage.local.set({ driveOn: true, lastDriveError: null });
          try { return { ok: true, ...(await driveOnce(true)) }; } catch (e) { return { ok: false, error: driveMsg(e) }; }
        }
        case "drive-now": { try { return { ok: true, ...(await driveOnce(true)) }; } catch (e) { return { ok: false, error: driveMsg(e) }; } }
        case "drive-list": {
          try { return { ok: true, files: (await driveList(driveDeps)).map((f) => ({ id: f.id, createdTime: f.createdTime, size: f.size, sessions: Number(f.appProperties.sessions ?? 0), tabs: Number(f.appProperties.tabs ?? 0), device: f.appProperties.device ?? "" })) }; }
          catch (e) { return { ok: false, error: driveMsg(e) }; }
        }
        case "drive-preview": case "drive-restore": {
          try {
            const p = parseBackup(await gunzip(await driveDownload(driveDeps, msg.id ?? "")));
            if (msg.type === "drive-restore") for (const x of p.sessions) await putSession(x);   // same ids → never doubled
            return { ok: true, sessions: p.sessions.length, tabs: p.tabs, groups: p.groups, skipped: p.skipped };
          } catch (e) { return { ok: false, error: e instanceof DriveError ? e.message : e instanceof Error ? e.message : "That backup could not be read." }; }
        }
        case "drive-disconnect": {
          await browser.storage.local.set({ driveOn: false });
          try { const t = await driveDeps.token(false); await browser.identity.removeCachedAuthToken({ token: t }); await fetch(`https://oauth2.googleapis.com/revoke?token=${encodeURIComponent(t)}`, { method: "POST" }); } catch { /* already signed out */ }
          await browser.permissions.remove({ permissions: ["identity"] }).catch(() => false);
          return { ok: true };
        }
        case "export": { const now = Date.now(); await browser.storage.local.set({ lastFileAt: now }); return { ok: true, fileName: backupFileName(now), json: JSON.stringify(toBackup(await listSessions(), now)) }; }
        case "preview-backup": { const p = parseBackup(msg.text ?? ""); return { ok: true, sessions: p.sessions.length, tabs: p.tabs, groups: p.groups, skipped: p.skipped }; }
        case "restore-backup": { const p = parseBackup(msg.text ?? ""); for (const s of p.sessions) await putSession(s); return { ok: true, sessions: p.sessions.length, tabs: p.tabs }; }
        default: return { ok: false, error: "unknown message" };
      }
    })().then(reply, (e) => reply({ ok: false, error: String(e) }));
    return true; // async reply
  });
});
