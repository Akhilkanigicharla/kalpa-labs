// Cloudflare entry for cf-runner (A239). Logic and tests live in lib.js / test.mjs: workerd treats every named
// export of the main module as an entrypoint, so the main module exports only the handler.
import { runOnce } from "./lib.js";

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runOnce(env, event.scheduledTime).then((d) => console.log("cf-runner", d)).catch((e) => console.log("cf-runner error", e.name)));
  },
};
