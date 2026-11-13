import { defineConfig } from "wxt";

// https://wxt.dev/api/config.html
export default defineConfig({
  manifest: {
    name: "Tab Lifeboat",
    description: "Save all tabs and tab groups in one click. Automatic snapshots, so a crash or update never wipes them.",
    permissions: ["tabs", "tabGroups", "alarms", "storage", "unlimitedStorage"],
    // asked only when a Pro user turns on: the daily backup file (downloads) / Google Drive backup (identity)
    optional_permissions: ["downloads", "identity"],
    // Google Drive backup: public OAuth client id from the build setting (not a secret). Without it the Drive card says "being set up".
    ...(process.env.WXT_GOOGLE_CLIENT_ID ? { oauth2: { client_id: process.env.WXT_GOOGLE_CLIENT_ID, scopes: ["https://www.googleapis.com/auth/drive.appdata"] } } : {}),
    action: { default_title: "Tab Lifeboat" },
  },
});
