// Cloudflare entry for cf-timer. Logic + tests: lib.js / test.mjs. workerd treats every named export of the main
// module as an entrypoint (found 19 Nov 2026: exported constants stopped `wrangler dev`), so only the handler is exported here.
import { run } from "./lib.js";

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(event.cron, new Date(event.scheduledTime), env).then((d) => console.log(event.cron, d.join("; "))));
  },
};
