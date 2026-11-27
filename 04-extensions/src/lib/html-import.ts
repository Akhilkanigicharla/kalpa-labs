// Bookmarks HTML (Netscape format: Chrome, Edge, Firefox, Toby, Pocket-era tools) and Pocket's ril_export.html.
// Runs in the options/popup page, because the service worker has no DOMParser (hardening 2.2). Reads only a[href],
// text and folder headings; parsed nodes are never inserted into our page. The result is checked again by fromLists().
import { CAPS } from "./model";
import { LISTS_FORMAT, type ListIn } from "./importers";

export const looksHtml = (t: string) => /^\s*(<!--[\s\S]*?-->\s*)*<(!doctype|html|head|meta|title|dl|h1)\b/i.test(t.replace(/^﻿/, ""));

/** How many lists (DL/UL) hold this element: its folder depth. */
function depthOf(e: Element): number {
  let d = 0; for (let x = e.parentElement; x && d <= CAPS.depth; x = x.parentElement) if (x.tagName === "DL" || x.tagName === "UL") d++;
  return d;
}

/** Walks headings and links in document order (works however the parser nests <DT> and <p>): a heading at depth d names
 *  the folder for links deeper than d. Bookmarks use H3 folders; Pocket uses H1 ("Unread", "Read Archive"). */
export function htmlToLists(doc: Document): { kind: string; source: string; lists: ListIn[] } {
  const pocket = /pocket export/i.test(doc.title ?? "") || [...doc.querySelectorAll("h1")].some((h) => /^(unread|read archive)$/i.test((h.textContent ?? "").trim()));
  const head = pocket ? "H1" : "H3";
  const lists = new Map<string, ListIn>(); const path: string[] = []; let links = 0;
  for (const e of doc.querySelectorAll(`${head.toLowerCase()}, a`)) {
    const d = Math.min(depthOf(e), CAPS.depth);
    if (e.tagName === head) { path.length = d; path[d] = (e.textContent ?? "").replace(/\s+/g, " ").trim(); continue; }
    const href = e.getAttribute("href") ?? e.getAttribute("HREF"); if (href === null) continue;
    if (++links > CAPS.tabs + 1) break;   // one over the cap, so fromLists reports the file as too big
    const folder = path.slice(0, d).filter(Boolean).join(" / ");
    const name = pocket ? `Pocket: ${/archive/i.test(folder) ? "Archive" : "Unread"}` : folder || "Bookmarks";
    let l = lists.get(name); if (!l) { l = { name, tabs: [] }; lists.set(name, l); }
    l.tabs.push({ url: href.trim(), title: (e.textContent ?? "").trim() });
  }
  return { kind: pocket ? "pocket-html" : "bookmarks-html", source: pocket ? "pocket" : "bookmarks", lists: [...lists.values()] };
}

/** Text for the background: HTML becomes our plain lists format (the background re-checks it); anything else is unchanged. */
export function prepareImport(text: string, parse: (t: string) => Document = (t) => new DOMParser().parseFromString(t, "text/html")): string {
  if (!looksHtml(text)) return text;
  const r = htmlToLists(parse(text));
  return JSON.stringify({ format: LISTS_FORMAT, kind: r.kind, source: r.source, lists: r.lists });
}
