// Deterministic 1,000-tab fixtures in the OneTab and Session Buddy formats (synthetic URLs only).
import fs from "node:fs";
export function onetabText(tabs = 1000, groups = 10) {
  const per = tabs / groups; const out = [];
  for (let g = 0; g < groups; g++) { for (let i = 0; i < per; i++) out.push(`https://example.com/g${g}/page-${i}?q=${g * per + i} | Page ${g * per + i} – grupo ${g} | test`); out.push(""); }
  return out.join("\n");
}
export function sessionBuddyV3(tabs = 1000, windows = 10) {
  const per = tabs / windows;
  return { sessions: [{ name: "Work", windows: Array.from({ length: windows }, (_, w) => ({ tabs: Array.from({ length: per }, (_, i) => ({ url: `https://example.org/w${w}/${i}`, title: `Tab ${w}-${i}`, pinned: i === 0 })) })) }] };
}
export function sessionBuddyV4() {
  return { collections: [{ title: "Reading", folders: [{ title: "Articles", links: [{ url: "https://a.example/1", title: "One" }, { url: "https://a.example/2", title: "Two" }] },
    { title: "Video", links: [{ url: "https://v.example/1", title: "V" }, { url: "chrome://settings", title: "settings" }, { title: "no url" }] }] }] };
}
if (process.argv[1]?.endsWith("make-fixtures.mjs")) {
  fs.writeFileSync(new URL("./onetab-1000.txt", import.meta.url), onetabText());
  fs.writeFileSync(new URL("./sessionbuddy-v3-1000.json", import.meta.url), JSON.stringify(sessionBuddyV3()));
  console.log("fixtures written");
}
