// v0.3 exports: Markdown, plain URL list (OneTab-style, re-imports), CSV. Escaping per hardening rule 5.
import { restorable, type Session } from "./model";

const line = (s: string) => s.replace(/[\r\n\t\u2028\u2029]+/g, " ").trim();

/** Markdown text: backslash before every character Markdown or HTML could act on. */
export const mdText = (s: string) => line(s).replace(/[\\[\]()*_`<>#!|~]/g, (c) => `\\${c}`);
/** Markdown link target in <…>: only http(s); <, > and spaces percent-encoded so the link can't break out. */
export const mdUrl = (u: string) => `<${u.replace(/</g, "%3C").replace(/>/g, "%3E").replace(/ /g, "%20")}>`;

export function toMarkdown(sessions: Session[]): string {
  const out: string[] = [];
  for (const s of sessions) {
    out.push(`## ${mdText(s.name)}`, "");
    const cant: string[] = [];
    for (const w of s.windows) {
      let group: string | null | undefined;
      for (const t of w.tabs) {
        if (!restorable(t.url)) { cant.push(`- ${mdText(t.url)}`); continue; }
        if ((t.groupKey ?? null) !== group) {
          group = t.groupKey ?? null;
          const g = w.groups.find((x) => x.key === group);
          if (g) out.push(`### ${mdText(g.title || "Tab group")}`, "");
        }
        out.push(`- [${mdText(t.title || t.url) || "link"}](${mdUrl(t.url)})`);
      }
    }
    if (cant.length) out.push("", "Can't reopen:", ...cant);
    out.push("");
  }
  return out.join("\n");
}

/** "url | title" per line, a blank line between sessions: the OneTab format, so it imports back into Tab Lifeboat or OneTab. */
export function toUrlList(sessions: Session[]): string {
  const body = sessions.map((s) => s.windows.flatMap((w) => w.tabs).map((t) => { const ti = line(t.title); return ti && ti !== t.url ? `${line(t.url)} | ${ti}` : line(t.url); }).join("\n")).join("\n\n");
  return `${body}\n`;
}

/** CSV cell: always quoted, quotes doubled, and a ' in front of anything a spreadsheet would run as a formula. */
export function csvCell(v: string): string {
  const s = /^[=+\-@\t\r\uFF1D\uFF0B\uFF0D\uFF20]/.test(v) ? `'${v}` : v;
  return `"${s.replace(/"/g, '""')}"`;
}

/** UTF-8 BOM (Excel then shows Telugu and Hindi correctly), CRLF line ends, header row. */
export function toCsv(sessions: Session[]): string {
  const rows = [["Session", "Group", "Title", "URL", "Saved"]];
  for (const s of sessions) for (const w of s.windows) for (const t of w.tabs)
    rows.push([s.name, w.groups.find((g) => g.key === t.groupKey)?.title ?? "", t.title, t.url, new Date(s.createdAt).toISOString()]);
  return `\uFEFF${rows.map((r) => r.map(csvCell).join(",")).join("\r\n")}\r\n`;
}

/** tab-lifeboat-2026-11-28-Work-stuff.md: local date, only [A-Za-z0-9._-], at most 100 characters. */
export function exportName(what: string, ext: string, now = new Date()): string {
  const d = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const base = `tab-lifeboat-${d}-${what}`.replace(/[^\w.-]+/g, "-").replace(/-+/g, "-").replace(/-$/, "").slice(0, 100 - ext.length - 1);
  return `${base}.${ext}`;
}
