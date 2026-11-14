// Importers for people switching from OneTab and Session Buddy (E6). Pure functions: text in, Session out.
// Formats were read from public exports and docs, not copied from any GPL/MPL code.
import { type SavedTab, type SavedWindow, type Session, newId } from "./model";

export interface ImportPreview { session: Session; tabs: number; groups: number; skipped: number; format: string }

/** OneTab "Export URLs" text: one "URL | Title" per line; a blank line starts a new tab group. */
export function parseOneTab(text: string, now = Date.now()): ImportPreview {
  const windows: SavedWindow[] = [];
  let cur: SavedWindow | null = null; let skipped = 0;
  for (const raw of text.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.trim();
    if (!line) { cur = null; continue; }
    const bar = line.indexOf(" | ");
    const url = (bar >= 0 ? line.slice(0, bar) : line).trim();
    const title = bar >= 0 ? line.slice(bar + 3).trim() : url;
    if (!/^[a-z][\w+.-]*:/i.test(url)) { skipped++; continue; }
    if (!cur) { cur = { tabs: [], groups: [] }; windows.push(cur); }
    cur.tabs.push({ url, title });
  }
  // OneTab groups become windows of one tab group each, named like OneTab shows them
  windows.forEach((w, i) => { const key = `onetab-${i + 1}`; w.groups.push({ key, title: `OneTab ${i + 1}`, color: "grey", collapsed: false }); for (const t of w.tabs) t.groupKey = key; });
  return preview({ id: newId(), name: "Imported from OneTab", createdAt: now, kind: "import", source: "onetab", windows }, skipped, "onetab-text");
}

/** Session Buddy JSON backups (v3 "sessions → windows → tabs" and v4 "collections → folders → links").
 *  Tolerant by design: walks the JSON and treats any array of objects with a `url` as one window. */
export function parseSessionBuddy(json: string | object, now = Date.now()): ImportPreview {
  const data = typeof json === "string" ? JSON.parse(json) : json;
  const windows: SavedWindow[] = []; let skipped = 0;
  const isTab = (x: unknown): x is { url: string } => !!x && typeof x === "object" && typeof (x as { url?: unknown }).url === "string";
  const walk = (node: unknown, label: string | null) => {
    if (Array.isArray(node)) {
      if (node.some(isTab) && node.every((x) => x && typeof x === "object" && !Array.isArray(x))) { // a list of links
        const tabs = node.filter(isTab).filter((t) => /^[a-z][\w+.-]*:/i.test(t.url));
        skipped += node.length - tabs.length;
        if (tabs.length) {
          const key = label ? `sb-${windows.length + 1}` : null;
          windows.push({
            tabs: tabs.map((t) => toTab(t as Record<string, unknown>, key)),
            groups: key && label ? [{ key, title: label, color: "blue", collapsed: false }] : [],
          });
        }
        return;
      }
      for (const x of node) walk(x, label);
      return;
    }
    if (node && typeof node === "object") {
      const o = node as Record<string, unknown>;
      // Session Buddy: `name` overrides `title`; a label belongs to the folder/window that holds the links, never inherited.
      const name = typeof o.name === "string" && o.name ? o.name : typeof o.title === "string" && o.title ? o.title : null;
      for (const v of Object.values(o)) if (typeof v === "object") walk(v, name);
    }
  };
  walk(data, null);
  const format = data && typeof data === "object" && "collections" in data ? "sessionbuddy-v4" : "sessionbuddy-v3";
  return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows }, skipped, format);
}

const URL_RE = /^[a-z][\w+.-]*:/i;
const isUrl = (s: string) => URL_RE.test(s) && !/\s/.test(s);
function toTab(t: Record<string, unknown>, groupKey: string | null): SavedTab {
  const title = typeof t.title === "string" && t.title && t.title !== "Untitled" ? t.title : String(t.url);
  const tab: SavedTab = { url: String(t.url), title, pinned: t.pinned === true || t.pinned === "true", groupKey };
  if (typeof t.favIconUrl === "string" && /^https:\/\//i.test(t.favIconUrl)) tab.favIconUrl = t.favIconUrl;
  return tab;
}

/** RFC 4180 rows: quoted fields may hold commas, quotes ("") and line breaks. */
function csvRows(text: string): string[][] {
  const rows: string[][] = []; let row: string[] = []; let f = ""; let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i]!;
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; continue; }
    if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(f); rows.push(row); row = []; f = ""; }
    else f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  return rows.filter((r) => r.some((x) => x.trim()));
}

/** Session Buddy CSV export (Collection, Folder, Title, URL, ...). Header row required, with a URL column. */
export function parseCsv(text: string, now = Date.now()): ImportPreview {
  const [head, ...rows] = csvRows(text.replace(/^\uFEFF/, ""));
  const col = (...names: string[]) => (head ?? []).findIndex((h) => names.includes(h.trim().toLowerCase()));
  const iUrl = col("url");
  if (iUrl < 0) throw new Error("This CSV has no URL column. Export it again from Session Buddy as CSV.");
  const iTitle = col("title"), iFolder = col("folder", "window"), iColl = col("collection", "session"), iIcon = col("faviconurl"), iPin = col("pinned");
  const byKey = new Map<string, SavedWindow>(); let skipped = 0;
  for (const r of rows) {
    const url = (r[iUrl] ?? "").trim();
    if (!isUrl(url)) { skipped++; continue; }
    const folder = iFolder >= 0 ? (r[iFolder] ?? "").trim() : "";
    const k = `${iColl >= 0 ? r[iColl] : ""}\u0000${folder}`;
    let w = byKey.get(k);
    if (!w) {
      const key = folder ? `sb-${byKey.size + 1}` : null;
      w = { tabs: [], groups: key ? [{ key, title: folder, color: "blue", collapsed: false }] : [] };
      byKey.set(k, w);
    }
    w.tabs.push(toTab({ url, title: iTitle >= 0 ? r[iTitle] : "", favIconUrl: iIcon >= 0 ? r[iIcon] : undefined, pinned: iPin >= 0 ? r[iPin] : false }, w.groups[0]?.key ?? null));
  }
  return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows: [...byKey.values()] }, skipped, "sessionbuddy-csv");
}

/** Session Buddy "Title/URL pairs": a title line, then its URL, pairs separated by a blank line. */
function pairBlocks(text: string): string[][] | null {
  const blocks = text.replace(/\r\n?/g, "\n").trim().split(/\n\s*\n/).map((b) => b.split("\n").map((l) => l.trim()));
  return blocks.length && blocks.every((b) => b.length === 2 && !isUrl(b[0]!) && isUrl(b[1]!)) ? blocks : null;
}

export function detectAndParse(text: string, now = Date.now()): ImportPreview {
  const t = text.replace(/^\uFEFF/, "").trimStart();
  if (t.startsWith("{") || t.startsWith("[")) return parseSessionBuddy(t, now);
  const first = t.split(/\r?\n/, 1)[0] ?? "";
  if (first.includes(",") && /(^|,)\s*"?url"?\s*(,|$)/i.test(first)) return parseCsv(t, now);
  const pairs = pairBlocks(t);
  if (pairs) {
    const tabs = pairs.map(([title, url]) => toTab({ url, title }, null));
    return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows: [{ tabs, groups: [] }] }, 0, "sessionbuddy-pairs");
  }
  return parseOneTab(text, now);
}

function preview(session: Session, skipped: number, format: string): ImportPreview {
  return { session, tabs: session.windows.reduce((n, w) => n + w.tabs.length, 0), groups: session.windows.reduce((n, w) => n + w.groups.length, 0), skipped, format };
}
