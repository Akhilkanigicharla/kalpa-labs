// v0.3 Group B: edit a saved session (remove a tab, move a tab to another session, merge two sessions).
// Pure functions: they never change their inputs, so the caller still holds the old copy for Undo.
import type { SavedGroup, SavedTab, SavedWindow, Session } from "./model";

const copy = (s: Session): Session => structuredClone(s);
/** A session someone has edited by hand is theirs to keep: automatic snapshots become manual so pruning never eats them. */
const own = (s: Session): Session => (s.kind === "auto" ? { ...s, kind: "manual" } : s);

/** Drop windows with no tabs and groups no tab points at. */
function tidy(s: Session): Session {
  s.windows = s.windows.filter((w) => w.tabs.length).map((w) => ({ ...w, groups: w.groups.filter((g) => w.tabs.some((t) => t.groupKey === g.key)) }));
  return s;
}

/** The tab at windows[wi].tabs[ti], or null if it is not there or its address changed (the page showed old data). */
export function tabAt(s: Session, wi: number, ti: number, url?: string): SavedTab | null {
  const t = s.windows[wi]?.tabs[ti];
  return t && (url === undefined || t.url === url) ? t : null;
}

export function removeTab(s: Session, wi: number, ti: number): Session {
  const out = copy(s); out.windows[wi]!.tabs.splice(ti, 1);
  return own(tidy(out));
}

/** Moves one tab to the last window of `to` (a new window if it has none). A grouped tab brings its group along:
 *  joined to a group with the same title and colour if `to` has one, else added under a fresh key. */
export function moveTab(from: Session, to: Session, wi: number, ti: number): [Session, Session] {
  const src = copy(from), dst = copy(to);
  const w = src.windows[wi]!; const [tab] = w.tabs.splice(ti, 1);
  if (!dst.windows.length) dst.windows.push({ tabs: [], groups: [] });
  const target = dst.windows[dst.windows.length - 1]!;
  const g = tab!.groupKey ? w.groups.find((x) => x.key === tab!.groupKey) : undefined;
  tab!.groupKey = g ? groupIn(target, g) : null;
  target.tabs.push(tab!);
  return [own(tidy(src)), own(dst)];
}

function groupIn(w: SavedWindow, g: SavedGroup): string {
  const same = w.groups.find((x) => x.title === g.title && x.color === g.color);
  if (same) return same.key;
  let key = g.key, i = 2;
  while (w.groups.some((x) => x.key === key)) key = `${g.key}-${i++}`;
  w.groups.push({ ...g, key });
  return key;
}

/** Every window of `source` is added after the windows of `target` (group keys belong to a window, so none clash). */
export function mergeSessions(target: Session, source: Session): Session {
  const out = copy(target); out.windows.push(...copy(source).windows);
  return own(tidy(out));
}

export const isEmpty = (s: Session) => !s.windows.some((w) => w.tabs.length);
