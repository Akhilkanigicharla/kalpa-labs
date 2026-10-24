import { captureAll, restore } from "../lib/capture";
import { detectAndParse } from "../lib/importers";
import { backupFileName, parseBackup, toBackup } from "../lib/backup";
import { countTabs } from "../lib/model";
import { LIMITS, deleteSession, getSession, listSessions, pruneAuto, putSession } from "../lib/store";
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

export default defineBackground(() => {
  // ask the browser not to evict our IndexedDB under disk pressure (OneTab users lost data this way)
  void (globalThis.navigator?.storage?.persist?.() ?? Promise.resolve(false));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("daily-backup", { periodInMinutes: 60 }));
  browser.alarms.onAlarm.addListener((a) => { if (a.name === "snapshot") void snapshot(); if (a.name === "daily-backup") void dailyBackup(); });

  browser.runtime.onMessage.addListener((msg: { type: string; id?: string; text?: string; name?: string }, _sender, reply) => {
    (async () => {
      const br = browser;
      switch (msg.type) {
        case "save": { const s = await captureAll(br, "manual", msg.name); await putSession(s); return { ok: true, session: s, counts: countTabs(s) }; }
        case "snapshot": return { ok: true, session: await snapshot() };
        case "status": { const { lastSnapshot } = await browser.storage.local.get("lastSnapshot"); return { ok: true, lastSnapshot: lastSnapshot ?? null, persisted: (await globalThis.navigator?.storage?.persisted?.()) ?? false, plan: await plan(), every: SNAPSHOT_MINUTES, limits: LIMITS }; }
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
        case "export": { const now = Date.now(); return { ok: true, fileName: backupFileName(now), json: JSON.stringify(toBackup(await listSessions(), now)) }; }
        case "preview-backup": { const p = parseBackup(msg.text ?? ""); return { ok: true, sessions: p.sessions.length, tabs: p.tabs, groups: p.groups, skipped: p.skipped }; }
        case "restore-backup": { const p = parseBackup(msg.text ?? ""); for (const s of p.sessions) await putSession(s); return { ok: true, sessions: p.sessions.length, tabs: p.tabs }; }
        default: return { ok: false, error: "unknown message" };
      }
    })().then(reply, (e) => reply({ ok: false, error: String(e) }));
    return true; // async reply
  });
});
