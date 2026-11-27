// One Restore button for the popup, the restart banner and the options page (hardening 2.4):
// above 100 tabs it asks first (tap again), the result goes to a status line, and pages skipped as already open
// can still be opened with "Open N anyway". Text only (textContent), never HTML.
import { CAPS } from "./model";

type Send = <T>(msg: object) => Promise<T & { ok: boolean; error?: string }>;
type Result = { tabs: number; asleep: number; alreadyOpen: number };
const n = (x: number) => x.toLocaleString("en-IN");

export function restoreText(r: Result & { ok: boolean; error?: string }): string {
  if (!r.ok) return r.error || "Could not open. Try again.";
  if (!r.tabs && r.alreadyOpen) return `All ${n(r.alreadyOpen)} already open`;
  return `Opened ${n(r.tabs)}${r.alreadyOpen ? `, skipped ${n(r.alreadyOpen)} already open` : ""}${r.asleep ? ", they load when clicked" : ""}`;
}

export function wireRestore(btn: HTMLButtonElement, status: HTMLElement, id: string, tabs: number, send: Send, label = "Restore", after?: () => void) {
  let mode: "ask" | "go" | "dupes" = tabs > CAPS.askAbove ? "ask" : "go";
  btn.textContent = label;
  btn.onclick = async () => {
    if (mode === "ask") { mode = "go"; btn.textContent = `Open ${n(tabs)} tabs?`; status.textContent = `Open ${n(tabs)} tabs? They open asleep and load when clicked. Tap again to open.`; return; }
    btn.disabled = true; const was = btn.textContent; btn.textContent = "Opening…";
    const r = await send<Result>({ type: "restore", id, ...(mode === "dupes" ? { name: "dupes" } : {}) });
    btn.disabled = false; status.textContent = mode === "dupes" && r.ok ? `Opened ${n(r.tabs)} again` : restoreText(r);
    if (r.ok) after?.();
    if (r.ok && mode === "go" && r.alreadyOpen) { mode = "dupes"; btn.textContent = `Open ${n(r.alreadyOpen)} anyway`; return; }
    btn.textContent = r.ok ? label : was ?? label; if (r.ok) mode = tabs > CAPS.askAbove ? "ask" : "go";
  };
}
