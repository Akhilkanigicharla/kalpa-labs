# Kalpa Labs architecture (one page)

Made with `.claude/skills/diagrams/SKILL.md` (A77, 22 Oct 2026). It answers one question: what talks to what.

```mermaid
%%{init: {"theme":"base","themeVariables":{"background":"#F2EEE3","primaryColor":"#F2EEE3","primaryBorderColor":"#2F6A3A","primaryTextColor":"#1E2A1F","lineColor":"#6B4226","secondaryColor":"#FCFAF4","tertiaryColor":"#E9E3D3","fontFamily":"Anek Latin, sans-serif"}}}%%
flowchart TB
  ceo["Akhil (CEO): decisions, accounts, selling"]
  hq["HQ: ROADMAP, CLAUDE.md, agents, design system"]
  claude["Claude build sessions: code, tests, checks"]
  n8n["n8n Task Runner + KL Tasks table: free models draft words"]
  gha["GitHub Actions: quality gate, lead lists, backtests"]
  subgraph worlds["The 7 worlds"]
    b1["b1 BotBhai"]
    b2["b2 JobCard"]
    b3["b3 Kits"]
    b4["b4 Tab Lifeboat"]
    b5["b5 Deals and Tools"]
    b6["b6 Ledger Peaks"]
    b7["b7 Trading Lab (paper only)"]
  end
  ceo -- "go / no-go" --> hq
  hq -- "next item" --> claude
  claude -- "commits to main" --> hq
  claude -- "queues research and drafts" --> n8n
  n8n -- "reviewed drafts" --> claude
  hq --> worlds
  claude -- "builds" --> worlds
  gha -- "tests every push" --> worlds
  gha -. "lead lists" .-> hq
  classDef hqc fill:#2F6A3A,color:#FFFFFF,stroke:#1D3A25
  classDef world fill:#F2EEE3,color:#1E2A1F,stroke:#6B4226
  classDef cloud fill:#C38E12,color:#1E2A1F,stroke:#6B4226
  class hq,ceo hqc
  class b1,b2,b3,b4,b5,b6,b7,claude world
  class n8n,gha cloud
```

- Akhil decides; nothing goes public until he says "go" (CLAUDE.md rule 9).
- HQ holds the plan and rules; Claude sessions take the next roadmap item, build it with tests and push to `main`.
- Word work (research, drafts, translations) goes to the n8n Task Runner on free models (`00-hq/DELEGATE.md`); GitHub Actions runs every world's tests and the lead lists.
