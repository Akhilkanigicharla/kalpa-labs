import { captureAll, restore } from "../lib/capture";
import { detectAndParse } from "../lib/importers";
import { countTabs } from "../lib/model";
import { deleteSession, getSession, listSessions, pruneAuto, putSession } from "../lib/store";

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

export default defineBackground(() => {
  // ask the browser not to evict our IndexedDB under disk pressure (OneTab users lost data this way)
  void (globalThis.navigator?.storage?.persist?.() ?? Promise.resolve(false));
  browser.runtime.onInstalled.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.runtime.onStartup.addListener(() => browser.alarms.create("snapshot", { periodInMinutes: SNAPSHOT_MINUTES }));
  browser.alarms.onAlarm.addListener((a) => { if (a.name === "snapshot") void snapshot(); });

  browser.runtime.onMessage.addListener((msg: { type: string; id?: string; text?: string; name?: string }, _sender, reply) => {
    (async () => {
      const br = browser;
      switch (msg.type) {
        case "save": { const s = await captureAll(br, "manual", msg.name); await putSession(s); return { ok: true, session: s, counts: countTabs(s) }; }
        case "snapshot": return { ok: true, session: await snapshot() };
        case "status": { const { lastSnapshot } = await browser.storage.local.get("lastSnapshot"); return { ok: true, lastSnapshot: lastSnapshot ?? null, persisted: (await globalThis.navigator?.storage?.persisted?.()) ?? false }; }
        case "list": return { ok: true, sessions: (await listSessions()).map((s) => ({ id: s.id, name: s.name, kind: s.kind, createdAt: s.createdAt, ...countTabs(s) })) };
        case "restore": { const s = await getSession(msg.id!); if (!s) return { ok: false, error: "not found" }; return { ok: true, ...(await restore(br, s)) }; }
        case "delete": await deleteSession(msg.id!); return { ok: true };
        case "preview-import": { const p = detectAndParse(msg.text ?? ""); return { ok: true, tabs: p.tabs, groups: p.groups, skipped: p.skipped, format: p.format }; }
        case "import": { const p = detectAndParse(msg.text ?? ""); await putSession(p.session); return { ok: true, id: p.session.id, tabs: p.tabs, groups: p.groups }; }
        default: return { ok: false, error: "unknown message" };
      }
    })().then(reply, (e) => reply({ ok: false, error: String(e) }));
    return true; // async reply
  });
});
