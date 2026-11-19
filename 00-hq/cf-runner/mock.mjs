// Local mock of the GitHub API + an OpenAI-style model API, for test.mjs (in-process) and test-dev.sh (HTTP).
import http from "node:http";
const enc = (s) => Buffer.from(s, "utf8").toString("base64");
const P = "/repos/Akhilkanigicharla/kalpa-labs";

export function makeMock({ tasks, files = {}, draft = "1. Draft text ✓", verdict = "PASS", moveMain = false }) {
  const s = { head: "base000sha", files: { ...files }, commits: [], modelCalls: 0, refPatch: 0 };
  for (const [w, rows] of Object.entries(tasks)) s.files[`00-hq/tasks/${w}.json`] = JSON.stringify(rows);
  const json = (status, body) => ({ status, ok: status < 300, json: async () => body });
  s.handle = async (url, opt = {}) => {
    const u = new URL(url), p = u.pathname, m = opt.method || "GET";
    if (p === "/v1/chat/completions" || p.endsWith("/chat/completions")) {
      s.modelCalls++;
      const body = JSON.parse(opt.body);
      const isVigil = body.messages[0].content.startsWith("You are Vigil");
      return json(200, { choices: [{ finish_reason: "stop", message: { content: isVigil ? verdict : draft } }] });
    }
    if (!p.startsWith(P)) return json(404, {});
    const r = p.slice(P.length);
    if (r === "/git/ref/heads/main") return json(200, { object: { sha: s.head } });
    if (r.startsWith("/contents/")) {
      const f = decodeURIComponent(r.slice(10));
      return f in s.files ? json(200, { content: enc(s.files[f]) }) : json(404, {});
    }
    if (r === "/git/commits/" + s.head && m === "GET") return json(200, { tree: { sha: "tree0" } });
    if (r === "/git/trees" && m === "POST") { s.pendingTree = JSON.parse(opt.body).tree; return json(201, { sha: "tree1" }); }
    if (r === "/git/commits" && m === "POST") { s.pendingCommit = JSON.parse(opt.body); return json(201, { sha: "newcommit123" }); }
    if (r === "/git/refs/heads/main" && m === "PATCH") {
      s.refPatch++;
      if (moveMain) return json(422, {});
      for (const t of s.pendingTree) s.files[t.path] = t.content;
      s.commits.push(s.pendingCommit.message); s.head = JSON.parse(opt.body).sha;
      return json(200, {});
    }
    return json(404, {});
  };
  return s;
}

// HTTP mode for wrangler dev: node mock.mjs <port>; GET /__state returns what happened.
if (process.argv[1] && process.argv[1].endsWith("mock.mjs")) {
  const old = new Date(Date.now() - 3 * 3600e3).toISOString();
  const s = makeMock({ tasks: { hq: [{ id: "K900", world: "hq", priority: "P1", owner: "Forge", title: "Dev test row", details: "Say hi.", status: "todo", created: old, read: ["README.md"] }] }, files: { "README.md": "# Kalpa" } });
  http.createServer(async (req, res) => {
    let body = ""; for await (const c of req) body += c;
    if (req.url === "/__state") { res.end(JSON.stringify({ commits: s.commits, modelCalls: s.modelCalls, hq: JSON.parse(s.files["00-hq/tasks/hq.json"]), knowledge: s.files["00-hq/knowledge/K900.md"] || null })); return; }
    const r = await s.handle(`http://x${req.url}`, { method: req.method, body });
    res.writeHead(r.status, { "Content-Type": "application/json" }); res.end(JSON.stringify(await r.json()));
  }).listen(Number(process.argv[2] || 8799), "127.0.0.1");
}
