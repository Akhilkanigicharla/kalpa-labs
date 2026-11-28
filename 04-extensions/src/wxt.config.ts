import { defineConfig } from "wxt";

// https://wxt.dev/api/config.html
export default defineConfig({
  manifest: {
    name: "Tab Lifeboat",
    description: "Save all tabs and tab groups in one click. Automatic snapshots, so a crash or update never wipes them.",
    // contextMenus: no install warning (developer.chrome.com/docs/extensions/reference/permissions-list, read 28 Nov 2026)
    permissions: ["tabs", "tabGroups", "alarms", "storage", "unlimitedStorage", "contextMenus"],
    // keyboard shortcuts (a manifest key, not a permission). Alt+Shift+Y was not checked against Chrome's own shortcut list
    // (that page needed approval); Chrome ignores a clashing suggestion, and users can change it at chrome://extensions/shortcuts.
    commands: {
      "save-all": { suggested_key: { default: "Alt+Shift+Y" }, description: "Save all tabs" },
      "save-window": { description: "Save this window" },
    },
    // asked only when a Pro user turns on: the daily backup file (downloads) / Google Drive backup (identity)
    optional_permissions: ["downloads", "identity"],
    // Google Drive backup: public OAuth client id from the build setting (not a secret). Without it the Drive card says "being set up".
    ...(process.env.WXT_GOOGLE_CLIENT_ID ? { oauth2: { client_id: process.env.WXT_GOOGLE_CLIENT_ID, scopes: ["https://www.googleapis.com/auth/drive.appdata"] } } : {}),
    action: { default_title: "Tab Lifeboat" },
    // A357: explicit CSP for our pages (research/v03-hardening-2026-11-27.md 1.1). Only our own scripts, no plugins,
    // images from the extension or data: (favicons we draw), network only to Google Drive + its token endpoint.
    content_security_policy: {
      extension_pages: "default-src 'self'; script-src 'self'; object-src 'none'; img-src 'self' data:; connect-src https://www.googleapis.com https://oauth2.googleapis.com; base-uri 'none'; form-action 'none'",
    },
  },
});
