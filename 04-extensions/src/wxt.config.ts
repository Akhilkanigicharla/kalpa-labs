import { defineConfig } from "wxt";

// https://wxt.dev/api/config.html
export default defineConfig({
  manifest: {
    name: "Tab Lifeboat",
    description: "Save all tabs and tab groups in one click. Automatic snapshots, so a crash or update never wipes them.",
    permissions: ["tabs", "tabGroups", "alarms", "storage", "unlimitedStorage"],
    action: { default_title: "Tab Lifeboat" },
  },
});
