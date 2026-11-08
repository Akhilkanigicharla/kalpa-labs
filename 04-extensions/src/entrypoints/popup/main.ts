import "./style.css";

type Row = { id: string; name: string; kind: string; createdAt: number; tabs: number; groups: number; windows: number };
// Never throw: if the background is asleep or busy, callers get { ok: false } and show a plain message (UX pattern 20).
const send = <T = Record<string, unknown>>(msg: object) =>
  (browser.runtime.sendMessage(msg) as Promise<T & { ok: boolean; error?: string }>).catch(() => ({ ok: false, error: "Tab Lifeboat is busy. Try again." }) as T & { ok: boolean; error?: string });
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const plural = (n: number, w: string) => `${n.toLocaleString("en-IN")} ${w}${n === 1 ? "" : "s"}`;

async function refresh() {
  const r = await send<{ sessions: Row[] }>({ type: "list" });
  const ul = $("list"); ul.replaceChildren(); ul.removeAttribute("aria-busy");
  if (!r.ok) { const li = document.createElement("li"); li.className = "empty"; li.textContent = r.error || "Could not load. Close and open again."; ul.append(li); return; }
  if (!r.sessions?.length) { const li = document.createElement("li"); li.className = "empty"; li.textContent = "Nothing saved yet."; ul.append(li); return; }
  for (const s of r.sessions) {
    const li = document.createElement("li");
    const meta = document.createElement("div"); meta.className = "meta";
    const name = document.createElement("strong"); name.textContent = s.name;
    const sub = document.createElement("span"); sub.textContent = `${plural(s.tabs, "tab")} · ${plural(s.groups, "group")}${s.kind === "auto" ? " · auto" : ""}`;
    meta.append(name, sub);
    const open = document.createElement("button"); open.textContent = "Restore"; open.onclick = async () => { const x = await send<{ tabs: number }>({ type: "restore", id: s.id }); open.textContent = x.ok ? `Opened ${plural(x.tabs, "tab")}` : "Could not open"; };
    const del = document.createElement("button"); del.className = "ghost"; del.textContent = "Delete"; del.setAttribute("aria-label", `Delete ${s.name}`);
    del.onclick = async () => { if (confirm(`Delete "${s.name}"?`)) { await send({ type: "delete", id: s.id }); await refresh(); } };
    li.append(meta, open, del); ul.append(li);
  }
}

$("save").addEventListener("click", async () => {
  const b = $<HTMLButtonElement>("save"); b.disabled = true;
  const r = await send<{ counts: { tabs: number; groups: number } }>({ type: "save" });
  b.textContent = r.ok ? `Saved ${plural(r.counts.tabs, "tab")}` : "Could not save"; b.disabled = false;
  setTimeout(() => (b.textContent = "Save all tabs"), 2000); await refresh();
});
let previewT: ReturnType<typeof setTimeout> | undefined;
$("importText").addEventListener("input", () => {  // wait for a pause before parsing a big paste (UX pattern 7)
  clearTimeout(previewT); $<HTMLButtonElement>("doImport").disabled = true;
  previewT = setTimeout(async () => {
    const text = $<HTMLTextAreaElement>("importText").value;
    const r = text.trim() ? await send<{ tabs: number; groups: number; skipped: number }>({ type: "preview-import", text }) : null;
    $("preview").textContent = r?.ok ? `${plural(r.tabs, "tab")} in ${plural(r.groups, "group")}${r.skipped ? `, ${r.skipped} skipped` : ""}` : r ? (r.error || "Could not read that text.") : "";
    $<HTMLButtonElement>("doImport").disabled = !r?.ok || !r.tabs;
  }, 250);
});
$("doImport").addEventListener("click", async () => {
  const r = await send({ type: "import", text: $<HTMLTextAreaElement>("importText").value });
  if (!r.ok) { $("preview").textContent = r.error || "Could not import."; return; }  // keep the pasted text so nothing is lost
  $<HTMLTextAreaElement>("importText").value = ""; $<HTMLButtonElement>("doImport").disabled = true; $("preview").textContent = "Imported."; await refresh();
});
async function status() {
  const r = await send<{ lastSnapshot: number | null }>({ type: "status" }); if (!r.ok) return;
  const mins = r.lastSnapshot ? Math.round((Date.now() - r.lastSnapshot) / 60000) : null;
  $("auto").textContent = mins === null ? "Auto-save every 5 min" : mins < 1 ? "Last snapshot just now" : `Last snapshot ${mins} min ago`;
}
$("more").addEventListener("click", () => void browser.runtime.openOptionsPage());
void refresh(); void status();
