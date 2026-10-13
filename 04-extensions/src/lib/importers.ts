// Importers for people switching from OneTab and Session Buddy (E6). Pure functions: text in, Session out.
// Formats were read from public exports and docs, not copied from any GPL/MPL code.
import { type SavedWindow, type Session, newId } from "./model";

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
            tabs: tabs.map((t) => ({ url: t.url, title: String((t as { title?: unknown }).title ?? t.url), pinned: !!(t as { pinned?: unknown }).pinned, groupKey: key })),
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
      const name = typeof o.title === "string" ? o.title : typeof o.name === "string" ? o.name : label;
      for (const v of Object.values(o)) if (typeof v === "object") walk(v, name);
    }
  };
  walk(data, null);
  const format = data && typeof data === "object" && "collections" in data ? "sessionbuddy-v4" : "sessionbuddy-v3";
  return preview({ id: newId(), name: "Imported from Session Buddy", createdAt: now, kind: "import", source: "sessionbuddy", windows }, skipped, format);
}

export function detectAndParse(text: string, now = Date.now()): ImportPreview {
  const t = text.trimStart();
  if (t.startsWith("{") || t.startsWith("[")) return parseSessionBuddy(t, now);
  return parseOneTab(text, now);
}

function preview(session: Session, skipped: number, format: string): ImportPreview {
  return { session, tabs: session.windows.reduce((n, w) => n + w.tabs.length, 0), groups: session.windows.reduce((n, w) => n + w.groups.length, 0), skipped, format };
}
