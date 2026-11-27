// Importers for people switching from OneTab and Session Buddy (E6). Pure functions: text in, Session out.
// Formats were read from public exports and docs, not copied from any GPL/MPL code.
import { CAPS, clip, type SavedTab, type SavedWindow, type Session, newId, safeUrl } from "./model";

export interface ImportPreview { session: Session; tabs: number; groups: number; skipped: number; format: string; sessions?: Session[] }
/** Every session an import makes (v0.3 formats can make one per folder/collection). */
export const sessionsOf = (p: ImportPreview) => p.sessions ?? [p.session];

/** OneTab "Export URLs" text: one "URL | Title" per line; a blank line starts a new tab group. */
export function parseOneTab(text: string, now = Date.now()): ImportPreview {
  const windows: SavedWindow[] = [];
  let cur: SavedWindow | null = null; let skipped = 0;
  for (const raw of text.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.trim();
    if (!line) { cur = null; continue; }
    const bar = line.indexOf(" | ");
    const url = safeUrl((bar >= 0 ? line.slice(0, bar) : line).trim());
    if (!url) { skipped++; continue; }   // hardening rule 2: only http(s) is stored
    const title = (bar >= 0 ? clip(line.slice(bar + 3), CAPS.title) : "") || url;
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
  let data: unknown;
  try { data = typeof json === "string" ? JSON.parse(json) : json; } catch { throw new Error(UNREADABLE); }
  const windows: SavedWindow[] = []; let skipped = 0;
  const isTab = (x: unknown): x is { url: string } => !!x && typeof x === "object" && typeof (x as { url?: unknown }).url === "string";
  const walk = (node: unknown, label: string | null, depth = 0) => {
    if (depth > CAPS.depth) throw new Error("This file is nested too deeply to be a session export. Nothing was changed.");
    if (Array.isArray(node)) {
      if (node.some(isTab) && node.every((x) => x && typeof x === "object" && !Array.isArray(x))) { // a list of links
        const tabs = node.filter(isTab).filter((t) => safeUrl(t.url));
        skipped += node.length - tabs.length;
        if (tabs.length) {
          const key = label ? `sb-${windows.length + 1}` : null;
          windows.push({
            tabs: tabs.map((t) => toTab(t as Record<string, unknown>, key)),
            groups: key && label ? [{ key, title: clip(label, CAPS.group), color: "blue", collapsed: false }] : [],
          });
        }
        return;
      }
      for (const x of node) walk(x, label, depth + 1);
      return;
    }
    if (node && typeof node === "object") {
      const o = node as Record<string, unknown>;
      // Session Buddy: `name` overrides `title`; a label belongs to the folder/window that holds the links, never inherited.
      const name = typeof o.name === "string" && o.name ? o.name : typeof o.title === "string" && o.title ? o.title : null;
      for (const v of Object.values(o)) if (typeof v === "object") walk(v, name, depth + 1);
    }
  };
  walk(data, null);
  const format = data && typeof data === "object" && "collections" in (data as object) ? "sessionbuddy-v4" : "sessionbuddy-v3";
  return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows }, skipped, format);
}

export const UNREADABLE = "This file couldn't be read. Nothing was changed.";
const isUrl = (s: string) => safeUrl(s) !== null && !/\s/.test(s);
/** Fresh object with known fields only (never copies keys from the parsed data). Callers pass http(s) URLs only. */
function toTab(t: Record<string, unknown>, groupKey: string | null): SavedTab {
  const url = safeUrl(t.url) ?? String(t.url);
  const title = typeof t.title === "string" && t.title && t.title !== "Untitled" ? clip(t.title, CAPS.title) || url : url;
  const tab: SavedTab = { url, title, pinned: t.pinned === true || t.pinned === "true", groupKey };
  if (typeof t.favIconUrl === "string" && /^https:\/\//i.test(t.favIconUrl)) tab.favIconUrl = t.favIconUrl;
  return tab;
}

/** RFC 4180 rows: quoted fields may hold commas, quotes ("") and line breaks. */
export function csvRows(text: string): string[][] {
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
      w = { tabs: [], groups: key ? [{ key, title: clip(folder, CAPS.group), color: "blue", collapsed: false }] : [] };
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
  if (text.length > CAPS.fileBytes) throw new Error("This file is over 20 MB, too big to import. Split it into smaller files.");
  const t = text.replace(/^\uFEFF/, "").trimStart();
  if (t.startsWith("{") || t.startsWith("[")) {
    let data: unknown;
    try { data = JSON.parse(t); } catch { throw new Error(UNREADABLE); }
    const o = data as Record<string, unknown> | null;
    if (o && typeof o === "object" && o.format === LISTS_FORMAT) return fromLists(o.lists, String(o.source ?? "file"), String(o.kind ?? "lists"), now);
    const toby = tobyLists(data);
    if (toby) return fromLists(toby, "toby", "toby-json", now);
    return parseSessionBuddy(data as object, now);
  }
  if (/^<(!doctype|html|head|meta|title|dl|h1)\b/i.test(t)) throw new Error("This is a web page file. Open it with the file button, so Tab Lifeboat can read its links.");
  const first = t.split(/\r?\n/, 1)[0] ?? "";
  if (first.includes(",") && /(^|,)\s*"?url"?\s*(,|$)/i.test(first)) {
    const head = csvRows(first)[0]?.map((h) => h.trim().toLowerCase()) ?? [];
    if (head.includes("time_added") && head.includes("status")) return parseByColumn(t, "status", (v) => `Pocket: ${v.toLowerCase() === "archive" ? "Archive" : "Unread"}`, "pocket", "pocket-csv", now);
    if (!head.includes("folder") && head.some((h) => h === "collection" || h === "collection name"))
      return parseByColumn(t, head.includes("collection") ? "collection" : "collection name", (v) => v || "Edge collection", "edge", "edge-collections-csv", now);
    return parseCsv(t, now);
  }
  const pairs = pairBlocks(t);
  if (pairs) {
    const tabs = pairs.map(([title, url]) => toTab({ url, title }, null));   // pairBlocks only accepts http(s) lines
    return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows: [{ tabs, groups: [] }] }, 0, "sessionbuddy-pairs");
  }
  return parseOneTab(text, now);
}

/** Hardening rule 3: one import holds at most 20,000 tabs in at most 1,000 windows/folders. */
export function checkCaps(tabs: number, sessions: number) {
  if (tabs > CAPS.tabs) throw new Error(`This file has ${tabs.toLocaleString("en-US")} tabs; Tab Lifeboat imports up to ${CAPS.tabs.toLocaleString("en-US")} at a time. Split the file.`);
  if (sessions > CAPS.sessions) throw new Error(`This file has ${sessions.toLocaleString("en-US")} sessions or folders; Tab Lifeboat imports up to ${CAPS.sessions.toLocaleString("en-US")} at a time. Split the file.`);
}
function preview(session: Session, skipped: number, format: string): ImportPreview {
  const tabs = session.windows.reduce((n, w) => n + w.tabs.length, 0);
  checkCaps(tabs, session.windows.length);
  return { session, tabs, groups: session.windows.reduce((n, w) => n + w.groups.length, 0), skipped, format };
}

// ---- v0.3 importers: Pocket (CSV + HTML), Edge Collections CSV, Toby JSON, bookmarks HTML (Netscape)
// Formats (read 28 Nov 2026):
// - Pocket CSV `title,url,time_added,tags,status` (older files also have `cursor`; status = unread | archive):
//   https://note.com/ueponx/n/n039889e00270 , https://infopirate.org/pocket-csv-what-survives/ , karakeep parsers.ts
//   (github.com/karakeep-app/karakeep packages/shared/import-export/parsers.ts). Pocket shut down 8 Jul 2025.
// - Pocket HTML ril_export.html: <title>Pocket Export</title>, <h1>Unread</h1><ul><li><a href=… time_added=… tags=…>title</a>,
//   then <h1>Read Archive</h1>: github.com/dandavison/pocket/blob/master/ril_export.html , github.com/billpalombi/pocket_parse
// - Toby JSON: { lists: [{ title, cards: [{ title, customTitle, url, customDescription }] }] }: Toby team's export snippet
//   gist.github.com/krishpop/8a954b171a5403117bf0f2fdda0a8e90 (and its `jq '.lists[].cards[].url'` comment).
// - Netscape bookmarks HTML: <!DOCTYPE NETSCAPE-Bookmark-file-1>, <DL><p><DT><H3>Folder</H3><DL><p><DT><A HREF=…>Title</A>.
//   Edge "Move to Favorites" then "Export favorites" gives this file (go.tabbit.ai/blog/edge-collections-removed-how-to-export).
// - Edge Collections CSV: UNVERIFIED. No public sample of the column names was found (Microsoft's page only says work/school
//   accounts can export). Read tolerantly: a URL column plus a "Collection" column, one session per collection.
// HTML is parsed in the page (DOMParser, see html-import.ts) because the service worker has no DOM; the page sends
// { format: LISTS_FORMAT, lists } and fromLists() below checks every field again.

export const LISTS_FORMAT = "tab-lifeboat-lists";
export interface ListIn { name: string; tabs: { url: string; title: string }[] }

/** One session per list. Untrusted input: only arrays of objects with string fields are read; URLs pass safeUrl. */
export function fromLists(lists: unknown, source: string, format: string, now = Date.now()): ImportPreview {
  if (!Array.isArray(lists)) throw new Error(UNREADABLE);
  const sessions: Session[] = []; let skipped = 0, tabs = 0;
  checkCaps(0, lists.length);
  for (const l of lists) {
    if (!l || typeof l !== "object" || !Array.isArray((l as ListIn).tabs)) { skipped++; continue; }
    const ts: SavedTab[] = [];
    for (const t of (l as ListIn).tabs) {
      const url = safeUrl((t as { url?: unknown })?.url);
      if (!url) { skipped++; continue; }
      ts.push({ url, title: clip((t as { title?: unknown }).title, CAPS.title) || url });
    }
    if (!ts.length) continue;
    tabs += ts.length; checkCaps(tabs, sessions.length + 1);
    sessions.push({ id: newId(), name: clip((l as ListIn).name, CAPS.name) || "Imported", createdAt: now - sessions.length, kind: "import", source: clip(source, 40), windows: [{ tabs: ts, groups: [] }] });
  }
  if (!sessions.length) throw new Error(skipped ? `No web links found: ${skipped.toLocaleString("en-US")} links can't be reopened and were left out.` : "No links found in this file.");
  return { session: sessions[0]!, sessions, tabs, groups: 0, skipped, format };
}

/** Toby: any `lists` array of { title, cards: [...] } (a whole-workspace export may nest them under spaces). Depth-capped. */
export function tobyLists(data: unknown): ListIn[] | null {
  const out: ListIn[] = [];
  const walk = (node: unknown, depth: number) => {
    if (depth > CAPS.depth || !node || typeof node !== "object") return;
    const o = node as Record<string, unknown>;
    if (Array.isArray(o.lists) && o.lists.some((l) => l && typeof l === "object" && Array.isArray((l as { cards?: unknown }).cards))) {
      for (const l of o.lists as Record<string, unknown>[]) {
        if (!l || !Array.isArray(l.cards)) continue;
        out.push({ name: typeof l.title === "string" ? l.title : "Toby", tabs: (l.cards as Record<string, unknown>[]).map((c) => ({
          url: typeof c?.url === "string" ? c.url : "", title: typeof c?.customTitle === "string" && c.customTitle ? c.customTitle : typeof c?.title === "string" ? c.title : "" })) });
      }
      return;
    }
    for (const v of Array.isArray(node) ? node : Object.values(o)) walk(v, depth + 1);
  };
  walk(data, 0);
  return out.length ? out : null;
}

/** CSV with a URL column, one session per value of `by` (Pocket status, Edge collection). Map keys, never object keys. */
function parseByColumn(text: string, by: string, name: (v: string) => string, source: string, format: string, now: number): ImportPreview {
  const [head, ...rows] = csvRows(text);
  const col = (n: string) => (head ?? []).findIndex((h) => h.trim().toLowerCase() === n);
  const iUrl = col("url"), iTitle = col("title"), iBy = col(by);
  const lists = new Map<string, ListIn>(); let bad = 0;
  for (const r of rows) {
    if (r.length < 2 && !safeUrl((r[iUrl] ?? "").trim())) { bad++; continue; }
    const key = name(iBy >= 0 ? clip(r[iBy], CAPS.name) : "");
    let l = lists.get(key); if (!l) { l = { name: key, tabs: [] }; lists.set(key, l); }
    l.tabs.push({ url: (r[iUrl] ?? "").trim(), title: iTitle >= 0 ? (r[iTitle] ?? "") : "" });
  }
  const p = fromLists([...lists.values()], source, format, now);
  return { ...p, skipped: p.skipped + bad };
}
