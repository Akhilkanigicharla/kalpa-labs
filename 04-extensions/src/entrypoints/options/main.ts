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
    const del = document.createElement("button"); del.type = "button"; del.className = "ghost"; del.textContent = "Delete"; del.setAttribute("aria-label", `Delete ${s.name}`);
    del.onclick = async () => { if (confirm(`Delete "${s.name}"? This can't be undone.`)) { await send({ type: "delete", id: s.id }); await refresh(); } };
    li.append(meta, open, del); ul.append(li);
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
  const r = await send({ type: "import", text: $<HTMLTextAreaElement>("importText").value });
  $<HTMLTextAreaElement>("importText").value = ""; $<HTMLButtonElement>("doImport").disabled = true;
  $("preview").textContent = r.ok ? "Imported." : err(r.error); await refresh();
});

void refresh();
