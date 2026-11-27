// A356 #7: plain-text and Markdown export, so people own their tabs outside the extension (pain #6, F10).
// Plain text uses OneTab's "url | title" lines, so it imports back into Tab Lifeboat, OneTab and most tab savers.
import { restorable, type Session } from "./model";

const oneLine = (s: string) => s.replace(/[\r\n]+/g, " ").trim();
/** Markdown-escape link text and headings; < > become entities so a title can't smuggle HTML into a notes app. */
const mdText = (s: string) => oneLine(s).replace(/[\\`*_[\]#]/g, "\\$&").replace(/</g, "&lt;").replace(/>/g, "&gt;");
/** Percent-encode what would end or break a Markdown link target. */
const mdUrl = (u: string) => u.replace(/[ ()<>]/g, (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);

const day = (at: number) => new Date(at).toISOString().slice(0, 10);

export function toMarkdown(sessions: Session[]): string {
  const out: string[] = [];
  for (const s of sessions) {
    const wins = s.windows.map((w) => ({ ...w, tabs: w.tabs.filter((t) => restorable(t.url)) })).filter((w) => w.tabs.length);
    if (!wins.length) continue;
    out.push(`## ${mdText(s.name)} (${day(s.createdAt)})`, "");
    wins.forEach((w, i) => {
      if (wins.length > 1) out.push(`### Window ${i + 1}`, "");
      let group: string | null | undefined;
      for (const t of w.tabs) {
        if ((t.groupKey ?? null) !== (group ?? null)) {
          group = t.groupKey ?? null;
          const g = w.groups.find((x) => x.key === group);
          if (g) out.push("", `**${mdText(g.title || "Group")}**`, "");
        }
        out.push(`- [${mdText(t.title || t.url)}](${mdUrl(t.url)})`);
      }
      out.push("");
    });
  }
  return out.length ? `# Tab Lifeboat export\n\n${out.join("\n").replace(/\n{3,}/g, "\n\n")}` : "# Tab Lifeboat export\n\nNo saved tabs yet.\n";
}

export function toPlain(sessions: Session[]): string {
  const blocks: string[] = [];
  for (const s of sessions) for (const w of s.windows) {
    const lines = w.tabs.filter((t) => restorable(t.url)).map((t) => `${t.url} | ${oneLine(t.title || t.url)}`);
    if (lines.length) blocks.push(lines.join("\n"));
  }
  return blocks.length ? `${blocks.join("\n\n")}\n` : "";
}

export const textFileName = (ext: "md" | "txt", now = Date.now()) => `tab-lifeboat-${day(now)}.${ext}`;
