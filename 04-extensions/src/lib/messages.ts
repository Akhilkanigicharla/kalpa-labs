// Every message the background accepts is checked here first: known type, right field types, size caps.
// The result is a fresh object with only the known fields, so nothing from a payload (e.g. "__proto__") leaks through.

export const MAX_TEXT = 21 * 1024 * 1024;   // a 20 MB import file as text, plus room for UTF-16 surprises
export const MAX_ID = 200;
export const MAX_NAME = 500;

export const TYPES = new Set([
  "save", "snapshot", "status", "list", "restore", "rate-ask", "rate-answer", "delete", "trash-list", "undelete", "delete-forever",
  "preview-import", "import", "search", "rename", "cleanup-preview", "cleanup", "timeline", "daily-backup",
  "drive-status", "drive-connect", "drive-now", "drive-list", "drive-preview", "drive-restore", "drive-disconnect",
  "export", "preview-backup", "restore-backup", "banner-dismiss",
  "session-get", "edit-remove-tab", "edit-move-tab", "edit-merge", "edit-undo", "export-text",
]);

export interface Msg { type: string; id?: string; to?: string; text?: string; name?: string; wi?: number; ti?: number; url?: string; scope?: string; v?: number }

const str = (v: unknown, max: number) => (typeof v === "string" && v.length <= max ? v : undefined);
const idx = (v: unknown) => (Number.isInteger(v) && (v as number) >= 0 && (v as number) < 1_000_000 ? (v as number) : undefined);

/** Returns a clean message, or null when the payload is not one of ours (wrong type, wrong field type, too big). */
export function checkMsg(m: unknown): Msg | null {
  if (!m || typeof m !== "object" || Array.isArray(m)) return null;
  const o = m as Record<string, unknown>;
  if (typeof o.type !== "string" || !TYPES.has(o.type)) return null;
  const out: Msg = { type: o.type };
  const fields: [keyof Msg, unknown, number][] = [["id", o.id, MAX_ID], ["to", o.to, MAX_ID], ["text", o.text, MAX_TEXT], ["name", o.name, MAX_NAME], ["url", o.url, 8192], ["scope", o.scope, MAX_ID]];
  for (const [k, v, max] of fields) {
    if (v === undefined || v === null) continue;
    const s = str(v, max); if (s === undefined) return null;
    (out as unknown as Record<string, unknown>)[k] = s;
  }
  for (const k of ["wi", "ti"] as const) {
    if (o[k] === undefined) continue;
    const n = idx(o[k]); if (n === undefined) return null;
    out[k] = n;
  }
  if (o.v !== undefined) {   // the session version the page saw (a millisecond time)
    if (!Number.isSafeInteger(o.v) || (o.v as number) < 0) return null;
    out.v = o.v as number;
  }
  return out;
}

/** Only our own pages (popup, options) may talk to the background. No content scripts exist; nothing external is accepted. */
export function fromUs(sender: { id?: string; url?: string } | undefined, runtimeId: string, base: string): boolean {
  return !!sender && sender.id === runtimeId && typeof sender.url === "string" && sender.url.startsWith(base);
}

export const DISK_FULL = "Your disk is nearly full, so Tab Lifeboat couldn't save. Free some space or download a backup file.";
const GENERIC = "Something went wrong. Nothing was changed. Try again.";
/** Replies carry fixed plain-English errors, never a raw exception (hardening 2.6). Our own `new Error("…")` texts are
 *  plain English and pass through; library errors (TypeError, DOMException…) become the generic sentence. */
export function errorText(e: unknown): { text: string; diskFull: boolean } {
  const name = (e as { name?: unknown })?.name;
  if (name === "QuotaExceededError" || (e instanceof Error && /quota/i.test(e.message))) return { text: DISK_FULL, diskFull: true };
  return { text: e instanceof Error && e.constructor === Error && e.message ? e.message : GENERIC, diskFull: false };
}
