# Claude Code setup on Windows (PowerShell, user scope)

**Do this first (about 25 minutes total):** steps 1–6 below, in order. Each step says what it does. Nothing here asks for a password or key except the optional Perplexity step, and you type that key yourself.

- **Who runs it:** Akhil, in **Windows PowerShell** (not as Administrator), on his PC. Node.js 24 is already installed (see `00-hq/HANDOFF.md`).
- **Scope:** everything is installed at **user scope** (`-s user` / `-g`), so it works in every folder. Nothing here installs Docker, Python or a model on the PC (Kalpa hard rule 2). Python and Docker tools run in the cloud instead (see [cloud-hosting-plan.md](cloud-hosting-plan.md)).
- **Secrets:** this file contains no real keys. Where a key is needed, it says `<YOUR_KEY>`. Never paste a key into a chat, a commit or this repo.
- **Source of each command:** the official README or docs linked next to it (checked 17 Oct 2026). If a command fails, the vendor may have changed it. Check that link and don't guess.

## 0. Check the basics (1 minute)

```powershell
node --version        # needs v18+ (Playwright MCP) and v22+ (HyperFrames)
claude --version      # Claude Code must be installed
```

## 1. Turn off skill-installer telemetry (1 minute)

`npx skills` sends anonymous usage data by default. Either variable below turns it off ([vercel-labs/skills README](https://github.com/vercel-labs/skills)).

```powershell
[Environment]::SetEnvironmentVariable("DISABLE_TELEMETRY", "1", "User")
[Environment]::SetEnvironmentVariable("DO_NOT_TRACK", "1", "User")
# close and reopen PowerShell after this
```

## 2. Official Anthropic plugin: claude-code-setup (3 minutes)

It recommends hooks, skills and MCPs for a repo. Source: [anthropics/claude-plugins-official/plugins/claude-code-setup](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup).

Inside a Claude Code session (type `claude`), run:

```text
/plugin marketplace add anthropics/claude-plugins-official
/plugin install claude-code-setup@claude-plugins-official
```

If the marketplace is already added, the first line just says so.

## 3. MCP servers (5 minutes)

### 3a. Playwright MCP (ADOPT, no key)
Source: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp).

```powershell
claude mcp add -s user playwright -- npx @playwright/mcp@latest
```

### 3b. PostHog MCP (ADOPT, browser login, no key stored)
Do this only after Akhil has a PostHog Cloud account. Source: [PostHog docs for Claude Code](https://posthog.com/docs/model-context-protocol/claude-code).

```powershell
claude mcp add -s user --transport http posthog https://mcp.posthog.com/mcp
```

Then, inside Claude Code, type `/mcp`, pick **posthog** and log in in the browser. PostHog's docs ask you to review each tool call it makes.

### 3c. Perplexity MCP (TRY LATER, **paid API**, only if Akhil decides to pay)
Source: [perplexityai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol). Store the key as a user environment variable that you type yourself, then reference it:

```powershell
# You type the real key yourself. Never paste it into Claude.
[Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "<YOUR_KEY>", "User")
# reopen PowerShell, then:
claude mcp add -s user perplexity -e PERPLEXITY_API_KEY=$env:PERPLEXITY_API_KEY -- npx -y @perplexity-ai/mcp-server
```

Note: `claude mcp add -e` saves the value in your user Claude config (`~\.claude.json`). If you prefer it never be written there, use the repo's [`.mcp.json`](../../.mcp.json) instead. That file reads `${PERPLEXITY_API_KEY}` from the environment at start-up.

### 3d. Rea (already installed, nothing to do)
`claude mcp list` should show `rea`. Audit notes: `00-hq/research/rea-audit-2026-10-16.md`.

Check that the servers are listed:

```powershell
claude mcp list
```

## 4. Skills via `npx skills` (5 minutes)

`-g` installs to your user folder. `-a claude-code` targets Claude Code. The installer shows a list. Pick only the named skill and say no to the rest.

```powershell
# Grill Me (Matt Pocock). When asked, tick only "grill-me"
npx skills@latest add mattpocock/skills -g -a claude-code

# Cloudflare security audit (official Cloudflare)
npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit -g -a claude-code

# Emil Kowalski design skills (Markdown only)
npx skills add emilkowalski/skills -g -a claude-code
```

Sources: [mattpocock/skills](https://github.com/mattpocock/skills) (grill-me lives at `skills/productivity/grill-me/SKILL.md`), [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) and [emilkowalski/skills](https://github.com/emilkowalski/skills). The `-a claude-code` flag is how `npx skills` picks the agent (`npx skills --help` lists the exact agent names; if `claude-code` is not accepted, drop `-a` and choose Claude Code in the menu).

To **find** more skills later:

```powershell
npx skills find seo
npx skills list -g
```

## 5. HyperFrames plugin (ADOPT, 3 minutes)

Source: [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes). It needs Node 22+ and FFmpeg only to **render**. Rendering runs in GitHub Actions (see cloud plan), so on the PC you only install the plugin for writing compositions.

```powershell
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
```

Use it in Claude Code as `/hyperframes:hyperframes`.

## 6. Check everything (2 minutes)

```powershell
claude mcp list
npx skills list -g
```

Inside Claude Code, run `/plugin` and confirm that **claude-code-setup** and **hyperframes** are enabled.

## Not installed on purpose

| Tool | Why not now |
|---|---|
| ECC | Installs 311 skills and hooks, edits `settings.json`, and has Windows defects. It overlaps Superpowers. |
| Impeccable | Telemetry is on by default, it downloads a binary, and its hooks run outside tool approval. |
| ponytail | Review its `hooks/` and `scripts/` folders first. |
| codebase-memory MCP | Unsigned Windows binary. Only worth it for very large repos. |
| graphify, headroom | Need Python on the PC (rule 2). Run them in cloud sessions instead. |
| Zapier MCP | n8n already covers it, and the free plan is tiny. |

## If something goes wrong

- **`npx` asks to install a package:** answer `y`. That only downloads the package named in the command.
- **Execution policy error:** don't change machine policy. Run the command in a new PowerShell window. If a vendor script needs it, use `Set-ExecutionPolicy -Scope Process Bypass`, which lasts only for that window.
- **Remove something:** `claude mcp remove <name> -s user`, `npx skills remove <skill> -g`, or `/plugin` → uninstall.

**Next step:** do steps 0–2 today (10 minutes). Then tell Claude "toolkit steps 0–2 done", and the next session will check them with you.
