import { backupFileName, parseBackup, toBackup } from "../lib/backup";
import { captureAll, restore } from "../lib/capture";
import { DRIVE_SCOPE, type DriveDeps, DriveError, deviceName, download as driveDownload, driveFileName, list as driveList, remove as driveRemove, upload as driveUpload, gunzip, gzip, sha256, toPrune } from "../lib/drive";
import { answerRating, formLink, RATE_DEFAULT, type RateState, STORE_REVIEW_URL, shouldAskRating, UNINSTALL_FORM_URL } from "../lib/feedback";
import { detectAndParse, sessionsOf } from "../lib/importers";
import { isEmpty, mergeSessions, moveTab, removeTab, tabAt } from "../lib/edit";
import { exportName, toCsv, toMarkdown, toUrlList } from "../lib/export";
import { checkMsg, errorText, fromUs } from "../lib/messages";
import { countTabs, type Session } from "../lib/model";
import { applyEdit, deleteForever, getSession, undoEdit, LIMITS, listSessions, listTrash, pruneAuto, purgeTrash, putSession, trashSession, undeleteSession } from "../lib/store";
import { BANNER_DAYS, type Banner, type BannerKind, backupDue, bannerSession, clock, findDuplicates, findStale, missingTabs, type OpenTab, searchTabs, staleSince, tabTimeline, upgradeNudge } from "../lib/tools";

export const SNAPSHOT_MINUTES = 5;

async function plan(): Promise<"free" | "pro"> {
  const { plan } = await browser.storage.local.get("plan");
  return plan === "pro" ? "pro" : "free";
}

/** Storage can hold anything (an old version, a bad write): read numbers through this, never trust the type. */
const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);

async function snapshot() {
  const s = await captureAll(browser, "auto");
  const empty = countTabs(s).tabs === 0;
  if (!empty) {
    await putSession(s);
    await pruneAuto(await plan(), Date.now(), await keepIds());
    await browser.storage.local.set({ lastSnapshot: s.createdAt }); // shown in the popup: proof backups happen
  }
  await browser.storage.local.set({ lastAutoRun: Date.now() });   // ran fine (even with nothing to save): clears the stale warning
  await setBadge(null);
  return empty ? null : s;
}

// ---- v0.3 Group A: stale-snapshot warning, restart/update banner
const ALARMS: Record<string, number> = { snapshot: SNAPSHOT_MINUTES, "daily-backup": 60, "drive-backup": 60 };
/** Recreate any alarm that went missing (the usual reason auto-save silently stops). Existing alarms keep their schedule. */
async function ensureAlarms() {
  for (const [name, every] of Object.entries(ALARMS)) if (!(await browser.alarms.get(name))) await browser.alarms.create(name, { periodInMinutes: every });
}
/** When this browser run started (storage.session is wiped when the browser closes). */
async function bootAt(): Promise<number> {
  const v = num((await browser.storage.session.get("bootAt").catch(() => ({} as Record<string, unknown>))).bootAt);
  if (v !== null) return v;
  const now = Date.now(); await browser.storage.session.set({ bootAt: now }).catch(() => {}); return now;
}
async function setBadge(since: number | null) {
  const a = browser.action; if (!a) return;
  await a.setBadgeText({ text: since === null ? "" : "!" });
  if (since !== null) await a.setBadgeBackgroundColor({ color: "#B13A2D" });
  await a.setTitle({ title: since === null ? "Tab Lifeboat" : `Auto-save hasn't run since ${clock(since)}` });
}
/** Stale = no automatic run for 3 intervals while the browser was open. First try to heal it (alarms back, one snapshot
 *  now); the "!" badge and the popup line stay only if that fails too. Returns the time it last ran, or null when fine. */
async function health(): Promise<number | null> {
  const st = await browser.storage.local.get(["lastAutoRun", "lastSnapshot"]);
  const since = staleSince({ lastRun: num(st.lastAutoRun) ?? num(st.lastSnapshot), bootAt: await bootAt(), now: Date.now(), everyMin: SNAPSHOT_MINUTES });
  if (since === null) return null;
  await ensureAlarms().catch(() => {});
  try { await snapshot(); return null; } catch { await setBadge(since).catch(() => {}); return since; }
}
let healthAt = 0;
const healthSoon = () => { const now = Date.now(); if (now - healthAt > 60_000) { healthAt = now; void health().catch(() => {}); } };

const BANNER_KINDS: BannerKind[] = ["restart", "update", "chrome-update"];
async function readBanner(now = Date.now()): Promise<Banner | null> {
  const b = (await browser.storage.local.get("banner")).banner as Partial<Banner> | null | undefined;
  if (!b || !BANNER_KINDS.includes(b.kind as BannerKind) || num(b.at) === null || typeof b.id !== "string") return null;
  return now - (b.at as number) > BANNER_DAYS * 864e5 ? null : (b as Banner);
}
const keepIds = async () => { const b = await readBanner(); return b ? [b.id] : []; };
/** Remember which snapshot was taken just before Chrome restarted or updated. Never opens a tab by itself. */
async function setBanner(kind: BannerKind, at: number) {
  const s = bannerSession(await listSessions(), at);
  await browser.storage.local.set({ banner: s ? { kind, at, id: s.id } : null });
}
async function bannerInfo() {
  const b = await readBanner(); if (!b) return null;
  const s = await getSession(b.id); if (!s) return null;
  const missing = missingTabs(s, (await browser.tabs.query({})).map((t) => t.url ?? ""));
  return missing ? { kind: b.kind, id: b.id, tabs: countTabs(s).tabs, missing, savedAt: s.createdAt } : null;   // all open again: nothing to offer
}
// ---- v0.3 Group B: edits with Undo. The old copies stay in memory for the Undo window (the page shows Undo for 8 s).
// The undo copy lives in storage.session (survives the worker stopping); memory only if it is too big for that (10 MB).
const UNDO_MS = 10_000;
type LastEdit = { at: number; prev: Session[]; trashed: string[] };
let lastEdit: LastEdit | null = null;
async function edit(prev: Session[], puts: Session[], trashed: string[] = []) {
  await applyEdit(puts, trashed); lastEdit = { at: Date.now(), prev, trashed };
  await browser.storage.session.set({ lastEdit }).then(() => { lastEdit = null; }, () => browser.storage.session.remove("lastEdit").catch(() => {}));
  return { ok: true, trashed: trashed.length > 0 };
}
async function takeLastEdit(): Promise<LastEdit | null> {
  const e = lastEdit ?? ((await browser.storage.session.get("lastEdit").catch(() => ({} as Record<string, unknown>))).lastEdit as LastEdit | undefined) ?? null;
  lastEdit = null; await browser.storage.session.remove("lastEdit").catch(() => {});
  return e && num(e.at) !== null && Array.isArray(e.prev) && Array.isArray(e.trashed) ? e : null;
}

/** Plain-English error for a reply; a full disk also lights the icon with the reason (hardening 2.8). */
function plainError(e: unknown): string {
  if (e instanceof DriveError) return e.message;
  const { text, diskFull } = errorText(e);
  if (diskFull) { void browser.action?.setBadgeText({ text: "!" }).catch(() => {}); void browser.action?.setTitle({ title: text }).catch(() => {}); }
  return text;
}
// ---- v0.3 Group C: save this window / selected tabs, from the popup, the toolbar-icon menu and a keyboard shortcut
type Scope = "all" | "window" | "selected";
async function saveScoped(scope: Scope, name?: string, windowId?: number) {
  const only = scope === "all" ? undefined : { windowId: windowId ?? (await browser.windows.getLastFocused({ windowTypes: ["normal"] })).id ?? -1, selected: scope === "selected" };
  const s = await captureAll(browser, "manual", name, only);
  const counts = countTabs(s);
  if (!counts.tabs) throw new Error(scope === "selected" ? "No tabs selected. Ctrl-click or Shift-click tabs first." : "No tabs to save in this window.");
  await putSession(s);
  return { session: s, counts };
}
let lastQuickSave = 0;
/** Menu and shortcut saves: ignored if repeated within 2 s; result shown on the icon (text, not colour alone). */
async function quickSave(scope: Scope, windowId?: number) {
  const now = Date.now(); if (now - lastQuickSave < 2000) return; lastQuickSave = now;
  try {
    const { counts } = await saveScoped(scope, undefined, windowId);
    await browser.action.setBadgeText({ text: "✓" }); await browser.action.setBadgeBackgroundColor({ color: "#1D3A25" });
    await browser.action.setTitle({ title: `Saved ${counts.tabs} tab${counts.tabs === 1 ? "" : "s"}` });
    setTimeout(() => { void setBadge(null).then(() => health()).catch(() => {}); }, 2500);
  } catch (e) {
    const text = plainError(e); await browser.action.setBadgeText({ text: "!" }).catch(() => {}); await browser.action.setTitle({ title: text }).catch(() => {});
  }
}
const MENU: [Scope, string][] = [["all", "Save all tabs"], ["window", "Save this window"], ["selected", "Save selected tabs"]];

let restoring = false;   // one restore at a time (a double click must not open everything twice)
const GONE = { ok: false, error: "That session changed or is gone. The page has been refreshed." };
const row = (s: Session) => ({ id: s.id, name: s.name, kind: s.kind, createdAt: s.createdAt, ...countTabs(s) });

async function openUrlsUnlessDupes(): Promise<string[]> {
  const { openDupes } = await browser.storage.local.get("openDupes");
  return openDupes === true ? [] : (await browser.tabs.query({})).map((t) => t.url ?? "");
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
  // v0.3: after a restart or an update the popup offers the last snapshot (Restore / Dismiss); nothing opens by itself
  browser.runtime.onStartup.addListener(() => { void setBanner("restart", Date.now()); });
  browser.runtime.onInstalled.addListener((d) => { if (d.reason === "update" || d.reason === "chrome_update") void setBanner(d.reason === "update" ? "update" : "chrome-update", Date.now()); });
  browser.tabs.onCreated.addListener(healthSoon);
  // Right-click on the toolbar icon (contextMenus: no install warning). removeAll first so an update can't duplicate ids.
  browser.runtime.onInstalled.addListener(() => {
    void browser.contextMenus.removeAll().then(() => { for (const [id, title] of MENU) browser.contextMenus.create({ id: `save-${id}`, title, contexts: ["action"] }); }).catch(() => {});
  });
  browser.contextMenus.onClicked.addListener((info, tab) => {
    const m = MENU.find(([id]) => info.menuItemId === `save-${id}`); if (m) void quickSave(m[0], tab?.windowId);
  });
  browser.commands.onCommand.addListener((cmd, tab) => { if (cmd === "save-all" || cmd === "save-window") void quickSave(cmd === "save-all" ? "all" : "window", tab?.windowId); });   // checks at most once a minute while the browser is in use
  void ensureAlarms().catch(() => {}); healthSoon();
  // Feedback (27 Nov 2026): the uninstall form opens once, only when the user removes Tab Lifeboat; off until Akhil sets the link.
  const bye = formLink(UNINSTALL_FORM_URL); if (bye) void browser.runtime.setUninstallURL(bye).catch(() => {});
  browser.runtime.onStartup.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("drive-backup", { periodInMinutes: 60 }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("drive-backup", { periodInMinutes: 60 }));
  browser.alarms.onAlarm.addListener((a) => {
    if (a.name === "snapshot") void snapshot().catch((e) => plainError(e));   // a failed run leaves lastAutoRun old, so the warning shows; disk full says so
    else healthSoon();
    if (a.name === "daily-backup") { void dailyBackup(); void purgeTrash(); }
    if (a.name === "drive-backup") void driveOnce(false).catch(() => { /* error saved for the settings page */ });
  });

  browser.runtime.onMessage.addListener((raw: unknown, sender, reply) => {
    const msg = checkMsg(raw);
    if (!msg || !fromUs(sender, browser.runtime.id, browser.runtime.getURL("/"))) { reply({ ok: false, error: "unknown message" }); return false; }
    (async () => {
      const br = browser;
      switch (msg.type) {
        case "save": { const scope: Scope = msg.scope === "window" || msg.scope === "selected" ? msg.scope : "all"; return { ok: true, ...(await saveScoped(scope, msg.name)) }; }
        case "snapshot": return { ok: true, session: await snapshot() };
        case "session-get": {
          const s = await getSession(msg.id ?? ""); if (!s) return GONE;
          return { ok: true, session: s, others: (await listSessions()).filter((x) => x.id !== s.id).map(row) };
        }
        case "edit-remove-tab": {
          const s = await getSession(msg.id ?? "");
          if (!s || msg.wi === undefined || msg.ti === undefined || !tabAt(s, msg.wi, msg.ti, msg.url)) return GONE;
          const next = removeTab(s, msg.wi, msg.ti);
          return isEmpty(next) ? edit([s], [], [s.id]) : edit([s], [next]);   // last tab gone: the session goes to Recently deleted
        }
        case "edit-move-tab": {
          const [from, to] = [await getSession(msg.id ?? ""), await getSession(msg.to ?? "")];
          if (!from || !to || from.id === to.id || msg.wi === undefined || msg.ti === undefined || !tabAt(from, msg.wi, msg.ti, msg.url)) return GONE;
          const [a, b] = moveTab(from, to, msg.wi, msg.ti);
          return isEmpty(a) ? edit([from, to], [b], [a.id]) : edit([from, to], [a, b]);
        }
        case "edit-merge": {   // id = merged away (goes to Recently deleted), to = kept and gets its windows
          const [src, dst] = [await getSession(msg.id ?? ""), await getSession(msg.to ?? "")];
          if (!src || !dst || src.id === dst.id) return GONE;
          return edit([dst, src], [mergeSessions(dst, src)], [src.id]);
        }
        case "edit-undo": {
          const e = await takeLastEdit();
          if (!e || Date.now() - e.at > UNDO_MS) return { ok: false, error: "Too late to undo. Merged or emptied sessions are still in Recently deleted." };
          await undoEdit(e.prev, e.trashed); return { ok: true };
        }
        case "banner-dismiss": await browser.storage.local.set({ banner: null }); return { ok: true };
        case "status": { const stale = await health(); const { lastSnapshot, lastFileAt, lastBackupAt } = await browser.storage.local.get(["lastSnapshot", "lastFileAt", "lastBackupAt"]); const files = [lastFileAt, lastBackupAt].filter((x): x is number => typeof x === "number"); return { ok: true, stale, banner: await bannerInfo(), lastSnapshot: num(lastSnapshot), lastFileAt: files.length ? Math.max(...files) : null, sessions: (await listSessions()).length, persisted: (await globalThis.navigator?.storage?.persisted?.()) ?? false, plan: await plan(), every: SNAPSHOT_MINUTES, limits: LIMITS }; }
        case "list": return { ok: true, sessions: (await listSessions()).map(row) };
        case "restore": {
          const s = await getSession(msg.id ?? ""); if (!s) return { ok: false, error: "That session is gone." };
          if (restoring) return { ok: false, error: "Already restoring. One moment." };
          restoring = true; let out: Awaited<ReturnType<typeof restore>>;
          try { out = msg.name === "dupes"   // "Open them anyway": only the pages the last restore skipped as already open
            ? await restore(br, s, undefined, undefined, (await browser.tabs.query({})).map((t) => t.url ?? ""), true)
            : await restore(br, s, undefined, undefined, await openUrlsUnlessDupes()); } finally { restoring = false; }
          const { rate } = await browser.storage.local.get("rate"); const r = { ...RATE_DEFAULT, ...(rate as RateState | undefined) };
          await browser.storage.local.set({ rate: { ...r, restores: r.restores + 1 } });   // a count only, nothing about the tabs
          return { ok: true, ...out };
        }
        case "rate-ask": { const { rate } = await browser.storage.local.get("rate"); return { ok: true, ask: shouldAskRating({ ...RATE_DEFAULT, ...(rate as RateState | undefined) }) }; }
        case "rate-answer": {
          const { rate } = await browser.storage.local.get("rate");
          const a = msg.name === "rate" ? "rate" : "later";
          await browser.storage.local.set({ rate: answerRating({ ...RATE_DEFAULT, ...(rate as RateState | undefined) }, a) });
          if (a === "rate") await browser.tabs.create({ url: STORE_REVIEW_URL });
          return { ok: true };
        }
        case "delete": return (await trashSession(msg.id ?? "")) ? { ok: true } : { ok: false, error: "That session is already gone." };   // A231: 7 days in Recently deleted
        case "trash-list": return { ok: true, sessions: (await listTrash()).map((s) => ({ id: s.id, name: s.name, kind: s.kind, createdAt: s.createdAt, deletedAt: s.deletedAt, ...countTabs(s) })) };
        case "undelete": return (await undeleteSession(msg.id ?? "")) ? { ok: true } : { ok: false, error: "That session is no longer in Recently deleted." };
        case "delete-forever": return (await deleteForever(msg.id ?? "")) ? { ok: true } : { ok: false, error: "That session is already gone." };
        case "preview-import": { const p = detectAndParse(msg.text ?? ""); return { ok: true, tabs: p.tabs, groups: p.groups, sessions: sessionsOf(p).length, windows: p.session.windows.length, skipped: p.skipped, format: p.format }; }
        case "import": {
          const p = detectAndParse(msg.text ?? ""); await applyEdit(sessionsOf(p));   // all sessions of one import in one transaction
          const { lastNudge } = await browser.storage.local.get("lastNudge"); const now = Date.now();
          const nudge = upgradeNudge({ plan: await plan(), importedTabs: p.tabs, lastNudge: (lastNudge as number) ?? null, now });
          if (nudge) await browser.storage.local.set({ lastNudge: now });
          return { ok: true, id: p.session.id, tabs: p.tabs, groups: p.groups, nudge };
        }
        case "export-text": {   // v0.3: Markdown / URL list / CSV of one session or all, built here, downloaded by the page
          const all = await listSessions(); const pick = msg.id ? all.filter((x) => x.id === msg.id) : all;
          if (!pick.length) return { ok: false, error: "Nothing saved yet to export." };
          const f = msg.name === "md" ? { text: toMarkdown(pick), ext: "md", mime: "text/markdown" } : msg.name === "csv" ? { text: toCsv(pick), ext: "csv", mime: "text/csv" } : { text: toUrlList(pick), ext: "txt", mime: "text/plain" };
          return { ok: true, ...f, fileName: exportName(msg.id ? pick[0]!.name : "all-sessions", f.ext) };
        }
        case "search": return { ok: true, hits: searchTabs(await listSessions(), msg.text ?? "") };
        case "rename": { const s = await getSession(msg.id ?? ""); if (!s) return GONE; return edit([s], [{ ...s, name: (msg.name ?? "").trim().slice(0, 80) || s.name }]); }
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
          } catch (e) { return { ok: false, error: plainError(e) }; }
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
    })().then(reply, (e) => reply({ ok: false, error: plainError(e) }));
    return true; // async reply
  });
});
