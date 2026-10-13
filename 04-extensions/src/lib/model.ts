// Tab Lifeboat data model. A session is a snapshot of windows, tabs and tab groups.
export type GroupColor = "grey" | "blue" | "red" | "yellow" | "green" | "pink" | "purple" | "cyan" | "orange";
export interface SavedTab { url: string; title: string; pinned?: boolean; groupKey?: string | null; favIconUrl?: string }
export interface SavedGroup { key: string; title: string; color: GroupColor; collapsed: boolean }
export interface SavedWindow { tabs: SavedTab[]; groups: SavedGroup[]; focused?: boolean; incognito?: false }
export interface Session {
  id: string; name: string; createdAt: number; kind: "manual" | "auto" | "import";
  source?: string; windows: SavedWindow[];
}
export const COLORS: GroupColor[] = ["grey", "blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];

/** Pages Chrome won't let an extension reopen, or that are pointless to save. */
export function restorable(url: string): boolean {
  return /^(https?|ftp|file):\/\//i.test(url); // chrome://, about:, data:, javascript: are skipped on restore
}

export function countTabs(s: Pick<Session, "windows">): { tabs: number; groups: number; windows: number } {
  return { tabs: s.windows.reduce((n, w) => n + w.tabs.length, 0), groups: s.windows.reduce((n, w) => n + w.groups.length, 0), windows: s.windows.length };
}

export const newId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
