import "../popup/style.css";
import "./options.css";
import { stamp } from "../../lib/capture";
import { restorable } from "../../lib/model";
import { backupReminder, daysAgo } from "../../lib/tools";

type Row = { id: string; name: string; kind: string; createdAt: number; tabs: number; groups: number; windows: number };
type Status = { lastSnapshot: number | null; lastFileAt: number | null; sessions: number; persisted: boolean; plan: "free" | "pro"; every: number; limits: { freeAutoSnapshots: number; proAutoDays: number } };
// Never throw: if the background is asleep or busy, callers get { ok: false } and show a plain message (UX pattern 20).
const send = <T = Record<string, unknown>>(msg: object) =>
  (browser.runtime.sendMessage(msg) as Promise<T & { ok: boolean; error?: string }>).catch(() => ({ ok: false, error: "Tab Lifeboat is busy. Try again." }) as T & { ok: boolean; error?: string });
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const n = (x: number) => x.toLocaleString("en-IN");
const plural = (x: number, w: string) => `${n(x)} ${w}${x === 1 ? "" : "s"}`;
const err = (e?: string) => (e || "Something went wrong.").replace(/^Error:\s*/, "");
const when = (t: number) => stamp(new Date(t));
const ago = (t: number | null) => { if (!t) return "not yet"; const m = Math.round((Date.now() - t) / 60000); return m < 1 ? "just now" : m < 60 ? `${m} min ago` : when(t); };

let rows: Row[] = [];
function draw() {
  const q = $<HTMLInputElement>("q").value.trim().toLowerCase();
  const ul = $("list"); ul.replaceChildren();
  const shown = rows.filter((r) => !q || r.name.toLowerCase().includes(q));
  if (!shown.length) { const li = document.createElement("li"); li.className = "empty"; li.textContent = rows.length ? "No session matches." : "Nothing saved yet. Use the toolbar button: Save all tabs."; ul.append(li); return; }
  for (const s of shown) {
    const li = document.createElement("li");
    const meta = document.createElement("div"); meta.className = "meta";
    const name = document.createElement("strong"); name.textContent = s.name;
    const sub = document.createElement("span"); sub.textContent = `${when(s.createdAt)} · ${plural(s.tabs, "tab")}${s.groups ? ` · ${plural(s.groups, "group")}` : ""}${s.kind === "auto" ? " · auto" : s.kind === "import" ? " · imported" : ""}`;
    meta.append(name, sub);
    const open = document.createElement("button"); open.type = "button"; open.textContent = "Restore"; open.setAttribute("aria-label", `Restore ${s.name}`);
    open.onclick = async () => { const r = await send<{ tabs: number; asleep: number }>({ type: "restore", id: s.id }); open.textContent = r.ok ? `Opened ${plural(r.tabs, "tab")}${r.asleep ? ", they load when clicked" : ""}` : "Could not open"; };
    const ren = document.createElement("button"); ren.type = "button"; ren.className = "ghost"; ren.textContent = "Rename"; ren.setAttribute("aria-label", `Rename ${s.name}`);
    ren.onclick = async () => { const v = prompt("New name for this session", s.name); if (v && v.trim() && v.trim() !== s.name) { await send({ type: "rename", id: s.id, name: v }); await refresh(); } };
    const del = document.createElement("button"); del.type = "button"; del.className = "ghost"; del.textContent = "Delete"; del.setAttribute("aria-label", `Delete ${s.name}`);
    del.onclick = async () => { if (confirm(`Delete "${s.name}"? This can't be undone.`)) { await send({ type: "delete", id: s.id }); await refresh(); } };
    li.append(meta, open, ren, del); ul.append(li);
  }
}

async function refresh() {
  const [list, st] = await Promise.all([send<{ sessions: Row[] }>({ type: "list" }), send<Status>({ type: "status" })]);
  if (!list.ok) { const li = document.createElement("li"); li.className = "empty"; li.textContent = err(list.error); $("list").replaceChildren(li); return; }
  rows = list.sessions ?? [];
  $("st-sessions").textContent = n(rows.length);
  $("st-tabs").textContent = n(rows.reduce((a, r) => a + r.tabs, 0));
  $("st-last").textContent = ago(st.lastSnapshot);
  const remind = st.ok ? backupReminder({ lastFileAt: st.lastFileAt, sessions: rows.length }) : null;
  $("backup-age").textContent = remind ?? (st.lastFileAt ? `Last backup file: ${daysAgo(st.lastFileAt)}.` : "");
  $("backup-age").classList.toggle("warn", !!remind);
  $("st-persist").textContent = st.persisted ? "Chrome has marked this storage as persistent: it won't be cleared when the disk is low." : "Tip: keep a backup file too. Chrome may clear site storage when the disk is nearly full.";
  $("plan").textContent = st.plan === "pro" ? "Pro" : "Free";
  $("pro-tools").hidden = st.plan !== "pro";
  if (st.plan === "pro") void driveRefresh();
  if (st.plan === "pro") {
    const c = await send<{ duplicates: number; stale: number; days: number }>({ type: "cleanup-preview" });
    if (c.ok) $("clean-preview").textContent = `Open now: ${plural(c.duplicates, "duplicate tab")}, ${plural(c.stale, "tab")} not opened for ${c.days} days. Everything is saved as "Before cleanup" first.`;
    const { dailyBackupOn } = await browser.storage.local.get("dailyBackupOn"); $<HTMLInputElement>("daily").checked = !!dailyBackupOn;
  }
  $("every").textContent = String(st.every ?? 5);
  if (st.limits) { $("free-n").textContent = String(st.limits.freeAutoSnapshots); $("pro-d").textContent = String(st.limits.proAutoDays); }
  draw();
}

$("q").addEventListener("input", draw);
$("download").addEventListener("click", async () => {
  const r = await send<{ fileName: string; json: string }>({ type: "export" });
  if (!r.ok) { $("download-msg").textContent = err(r.error); return; }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([r.json], { type: "application/json" })); a.download = r.fileName; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10_000);
  $("download-msg").textContent = `Saved ${r.fileName} to your Downloads folder.`;
  $("backup-age").textContent = "Last backup file: today."; $("backup-age").classList.remove("warn");
});

let pending = "";
$("restore-file").addEventListener("change", async () => {
  const f = $<HTMLInputElement>("restore-file").files?.[0]; const go = $<HTMLButtonElement>("restore-go");
  pending = ""; go.hidden = true;
  if (!f) { $("restore-preview").textContent = ""; return; }
  if (f.size > 50 * 1024 * 1024) { $("restore-preview").textContent = "That file is over 50 MB, too big to be a Tab Lifeboat backup."; return; }
  const text = await f.text();
  const r = await send<{ sessions: number; tabs: number; groups: number; skipped: number }>({ type: "preview-backup", text });
  if (!r.ok) { $("restore-preview").textContent = err(r.error); return; }
  $("restore-preview").textContent = `${plural(r.sessions, "session")}, ${plural(r.tabs, "tab")}, ${plural(r.groups, "group")}${r.skipped ? ` (${n(r.skipped)} unsafe or empty links left out)` : ""}. Sessions you already have are not doubled.`;
  pending = text; go.hidden = !r.sessions;
});
$("restore-go").addEventListener("click", async () => {
  const r = await send<{ sessions: number }>({ type: "restore-backup", text: pending });
  $("restore-preview").textContent = r.ok ? `Added ${plural(r.sessions, "session")}.` : err(r.error);
  $<HTMLButtonElement>("restore-go").hidden = true; pending = ""; await refresh();
});

let previewT: ReturnType<typeof setTimeout> | undefined;
$("importText").addEventListener("input", () => {  // wait for a pause before parsing a big paste (UX pattern 7)
  clearTimeout(previewT); $<HTMLButtonElement>("doImport").disabled = true;
  previewT = setTimeout(async () => {
    const text = $<HTMLTextAreaElement>("importText").value;
    const r = text.trim() ? await send<{ tabs: number; groups: number; skipped: number }>({ type: "preview-import", text }) : null;
    $("preview").textContent = r?.ok ? `${plural(r.tabs, "tab")} in ${plural(r.groups, "group")}${r.skipped ? `, ${n(r.skipped)} skipped` : ""}` : r ? err(r.error) : "";
    $<HTMLButtonElement>("doImport").disabled = !r?.ok || !r.tabs;
  }, 250);
});
$("importFile").addEventListener("change", async () => {
  const input = $<HTMLInputElement>("importFile"); const f = input.files?.[0];
  if (!f) return;
  if (f.size > 5 * 1024 * 1024) { $("preview").textContent = "That file is over 5 MB, too big to be a OneTab or Session Buddy export."; input.value = ""; return; }
  const box = $<HTMLTextAreaElement>("importText");
  box.value = await f.text(); input.value = "";
  box.dispatchEvent(new Event("input"));
});
$("doImport").addEventListener("click", async () => {
  const r = await send<{ nudge: string | null }>({ type: "import", text: $<HTMLTextAreaElement>("importText").value });
  $<HTMLTextAreaElement>("importText").value = ""; $<HTMLButtonElement>("doImport").disabled = true;
  $("preview").textContent = r.ok ? `Imported.${r.nudge ? " " + r.nudge : ""}` : err(r.error); await refresh();
});

let findT: ReturnType<typeof setTimeout> | undefined;
$("find").addEventListener("input", () => {
  clearTimeout(findT);
  findT = setTimeout(async () => {
    const q = $<HTMLInputElement>("find").value; const ul = $("hits"); ul.replaceChildren();
    if (!q.trim()) return;
    const r = await send<{ hits: { url: string; title: string; sessionName: string; createdAt: number; alsoIn: number }[] }>({ type: "search", text: q });
    const hits = r.hits ?? [];
    if (!hits.length) { const li = document.createElement("li"); li.className = "empty"; li.textContent = "No saved tab matches."; ul.append(li); return; }
    for (const h of hits.slice(0, 50)) {
      const li = document.createElement("li"); const meta = document.createElement("div"); meta.className = "meta";
      // only web addresses become links; anything else from an imported file (javascript:, file:, data:) is shown as plain text
      const a = document.createElement(restorable(h.url) ? "a" : "span"); if (a instanceof HTMLAnchorElement) { a.href = h.url; a.target = "_blank"; a.rel = "noopener"; } a.textContent = h.title || h.url;
      const sub = document.createElement("span"); sub.textContent = `${h.sessionName} · ${when(h.createdAt)}${h.alsoIn ? ` · in ${plural(h.alsoIn, "older session")} too` : ""}`;
      meta.append(a, sub); li.append(meta); ul.append(li);
    }
  }, 200);
});

const cleanup = async (mode: "dupes" | "stale") => {
  if (!confirm("Close these tabs? All open tabs are saved first as \"Before cleanup\", so you can restore them.")) return;
  const r = await send<{ closed: number }>({ type: "cleanup", name: mode });
  $("clean-preview").textContent = r.ok ? `Closed ${plural(r.closed, "tab")}. Restore "Before cleanup" to undo.` : err(r.error); await refresh();
};
$("clean-dupes").addEventListener("click", () => cleanup("dupes"));
$("clean-stale").addEventListener("click", () => cleanup("stale"));
$("daily").addEventListener("change", async () => {
  const on = $<HTMLInputElement>("daily").checked;
  if (on && !(await browser.permissions.request({ permissions: ["downloads"] }))) { $<HTMLInputElement>("daily").checked = false; $("daily-msg").textContent = "Daily file needs permission to save to Downloads."; return; }
  const r = await send<{ made: number | null }>({ type: "daily-backup", name: on ? "on" : "off" });
  $("daily-msg").textContent = !r.ok ? err(r.error) : on ? (r.made ? "On. Today's file is in Downloads/Tab Lifeboat." : "On. The next file is saved within the hour.") : "Off.";
});
$("where").addEventListener("change", async () => {
  const r = await send<{ timeline: { firstSeen: number; lastSeen: number; snapshots: number; goneSince: number | null } | null }>({ type: "timeline", text: $<HTMLInputElement>("where").value });
  const tl = r.timeline;
  $("where-msg").textContent = !r.ok ? err(r.error) : !tl ? "Not in any saved session or snapshot." :
    `First seen ${when(tl.firstSeen)}, last seen ${when(tl.lastSeen)} (${plural(tl.snapshots, "snapshot")}). ${tl.goneSince ? `It was gone by ${when(tl.goneSince)}. Search for it above to restore it.` : "It is still in your newest snapshot."}`;
});

void refresh();

// ---- Google Drive backup (Pro). Every message is answered with { ok, error } in plain words; nothing here can throw.
type DriveStatus = { ready: boolean; pro: boolean; on: boolean; lastAt: number | null; error: { message: string; at: number } | null };
type DriveRow = { id: string; createdTime: string; size: number; sessions: number; tabs: number; device: string };
const kb = (b: number) => (b < 1024 * 1024 ? `${Math.max(1, Math.round(b / 1024))} KB` : `${(b / 1048576).toFixed(1)} MB`);
function driveMsg(text: string, good = false) { $("drive-msg").textContent = text; $("drive-msg").classList.toggle("ok", good); $("drive-msg").classList.toggle("warn", !good && !!text); }
async function driveRefresh() {
  const r = await send<DriveStatus>({ type: "drive-status" });
  if (!r.ok) return;
  const on = r.on;
  $("drive-connect").hidden = on; $("drive-now").hidden = !on; $("drive-off").hidden = !on; $("drive-box").hidden = !on;
  $("drive-state").textContent = !r.ready ? "Google Drive backup is being set up. It arrives in the next update."
    : !on ? "Off. Your tabs are only on this computer."
    : r.lastAt ? `On. Last backup ${when(r.lastAt)}. Checks every hour and uploads only when your tabs changed.` : "On. The first backup is on its way.";
  $<HTMLButtonElement>("drive-connect").disabled = !r.ready;
  if (on && r.error && (!r.lastAt || r.error.at > r.lastAt)) driveMsg(r.error.message);
}
$("drive-connect").addEventListener("click", async () => {
  const b = $<HTMLButtonElement>("drive-connect");
  // permissions.request must run inside the click; "identity" is optional and asked only now
  const granted = await browser.permissions.request({ permissions: ["identity"] }).catch(() => false);
  if (!granted) { driveMsg("Tab Lifeboat needs your OK to use your Google account for this. Nothing was changed."); return; }
  b.disabled = true; b.textContent = "Connecting…"; driveMsg("");
  const r = await send<{ uploaded: boolean }>({ type: "drive-connect" });
  b.disabled = false; b.textContent = "Connect Google Drive";
  driveMsg(r.ok ? "Connected. Your first backup is in your Google Drive." : err(r.error), r.ok);
  await driveRefresh();
});
$("drive-now").addEventListener("click", async () => {
  const b = $<HTMLButtonElement>("drive-now"); b.disabled = true; b.textContent = "Backing up…";
  const r = await send<{ uploaded: boolean }>({ type: "drive-now" });
  b.disabled = false; b.textContent = "Back up now";
  driveMsg(r.ok ? (r.uploaded ? "Backed up to Google Drive just now." : "Nothing to back up yet: save some tabs first.") : err(r.error), r.ok);
  await driveRefresh(); if ((document.getElementById("drive-box") as HTMLDetailsElement).open) void driveFiles();
});
$("drive-off").addEventListener("click", async () => {
  if (!confirm("Stop backing up to Google Drive? Backups already in your Drive stay there and can be restored if you connect again.")) return;
  await send({ type: "drive-disconnect" }); driveMsg("Disconnected. Your tabs are only on this computer now.", true); await driveRefresh();
});
$("drive-box").addEventListener("toggle", () => { if ((document.getElementById("drive-box") as HTMLDetailsElement).open) void driveFiles(); });
async function driveFiles() {
  const ul = $("drive-files"); ul.setAttribute("aria-busy", "true");
  const loading = document.createElement("li"); loading.className = "empty"; loading.textContent = "Loading your backups…"; ul.replaceChildren(loading);
  const r = await send<{ files: DriveRow[] }>({ type: "drive-list" }); ul.removeAttribute("aria-busy");
  const files = r.files ?? [];
  if (!r.ok || !files.length) { const li = document.createElement("li"); li.className = "empty"; li.textContent = r.ok ? "No backups in your Google Drive yet." : err(r.error); ul.replaceChildren(li); return; }
  ul.replaceChildren(...files.map((f) => {
    const li = document.createElement("li"); const meta = document.createElement("div"); meta.className = "meta";
    const b = document.createElement("b"); b.textContent = when(Date.parse(f.createdTime));
    const sub = document.createElement("span"); sub.textContent = `${f.device || "Unknown computer"} · ${plural(f.sessions, "session")} · ${plural(f.tabs, "tab")} · ${kb(f.size)}`;
    meta.append(b, sub);
    const go = document.createElement("button"); go.type = "button"; go.textContent = "Restore…"; let ready = false;
    go.onclick = async () => {   // two steps: see what's inside, then add it (UX pattern: destructive-action protection)
      go.disabled = true;
      const r2 = await send<{ sessions: number; tabs: number }>({ type: ready ? "drive-restore" : "drive-preview", id: f.id });
      go.disabled = false;
      if (!r2.ok) { go.textContent = "Try again"; driveMsg(err(r2.error)); return; }
      if (!ready) { ready = true; go.textContent = `Add ${plural(r2.sessions, "session")}`; go.classList.add("primary"); return; }
      go.textContent = "Added ✓"; go.disabled = true; driveMsg(`Added ${plural(r2.sessions, "session")} (${plural(r2.tabs, "tab")}). Sessions you already had were not doubled.`, true); await refresh();
    };
    li.append(meta, go); return li;
  }));
}
