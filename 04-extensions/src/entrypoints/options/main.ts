import "../popup/style.css";
import "./options.css";
import { stamp } from "../../lib/capture";

type Row = { id: string; name: string; kind: string; createdAt: number; tabs: number; groups: number; windows: number };
type Status = { lastSnapshot: number | null; persisted: boolean; plan: "free" | "pro"; every: number; limits: { freeAutoSnapshots: number; proAutoDays: number } };
const send = <T = Record<string, unknown>>(msg: object) => browser.runtime.sendMessage(msg) as Promise<T & { ok: boolean; error?: string }>;
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
    const sub = document.createElement("span"); sub.textContent = `${when(s.createdAt)} · ${plural(s.tabs, "tab")} · ${plural(s.groups, "group")}${s.kind === "auto" ? " · auto" : s.kind === "import" ? " · imported" : ""}`;
    meta.append(name, sub);
    const open = document.createElement("button"); open.type = "button"; open.textContent = "Restore"; open.setAttribute("aria-label", `Restore ${s.name}`);
    open.onclick = async () => { const r = await send<{ tabs: number }>({ type: "restore", id: s.id }); open.textContent = r.ok ? `Opened ${plural(r.tabs, "tab")}` : "Could not open"; };
    const ren = document.createElement("button"); ren.type = "button"; ren.className = "ghost"; ren.textContent = "Rename"; ren.setAttribute("aria-label", `Rename ${s.name}`);
    ren.onclick = async () => { const v = prompt("New name for this session", s.name); if (v && v.trim() && v.trim() !== s.name) { await send({ type: "rename", id: s.id, name: v }); await refresh(); } };
    const del = document.createElement("button"); del.type = "button"; del.className = "ghost"; del.textContent = "Delete"; del.setAttribute("aria-label", `Delete ${s.name}`);
    del.onclick = async () => { if (confirm(`Delete "${s.name}"? This can't be undone.`)) { await send({ type: "delete", id: s.id }); await refresh(); } };
    li.append(meta, open, ren, del); ul.append(li);
  }
}

async function refresh() {
  const [list, st] = await Promise.all([send<{ sessions: Row[] }>({ type: "list" }), send<Status>({ type: "status" })]);
  rows = list.sessions ?? [];
  $("st-sessions").textContent = n(rows.length);
  $("st-tabs").textContent = n(rows.reduce((a, r) => a + r.tabs, 0));
  $("st-last").textContent = ago(st.lastSnapshot);
  $("st-persist").textContent = st.persisted ? "Chrome has marked this storage as persistent: it won't be cleared when the disk is low." : "Tip: keep a backup file too. Chrome may clear site storage when the disk is nearly full.";
  $("plan").textContent = st.plan === "pro" ? "Pro" : "Free";
  $("pro-tools").hidden = st.plan !== "pro";
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

$("importText").addEventListener("input", async () => {
  const text = $<HTMLTextAreaElement>("importText").value;
  const r = text.trim() ? await send<{ tabs: number; groups: number; skipped: number }>({ type: "preview-import", text }) : null;
  $("preview").textContent = r?.ok ? `${plural(r.tabs, "tab")} in ${plural(r.groups, "group")}${r.skipped ? `, ${n(r.skipped)} skipped` : ""}` : r ? err(r.error) : "";
  $<HTMLButtonElement>("doImport").disabled = !r?.ok || !r.tabs;
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
      const a = document.createElement("a"); a.href = h.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = h.title || h.url;
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
