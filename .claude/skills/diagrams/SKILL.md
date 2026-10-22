---
name: diagrams
description: Use when a Kalpa Labs doc needs an architecture, flow or sequence diagram. Writes Mermaid inside markdown (renders on GitHub, no images, no tools to install) in Kalpavruksha colours, kept small enough to read on a 390 px phone.
---

# Diagrams (Kalpa Labs, our own skill)

Text diagrams are cheap in tokens and safe: no image tools, no network, no install. Use Mermaid in a fenced block inside the markdown file it explains.

## Steps
1. Decide the one question the diagram answers ("what talks to what?", "what happens when a booking arrives?"). One diagram, one question.
2. Pick the type: `flowchart LR` or `TB` for architecture, `sequenceDiagram` for a request in time, `stateDiagram-v2` for status changes.
3. At most 15 nodes. More than that: split into two diagrams.
4. Labels in plain short English (the reader is Akhil on a phone). Node ids short and ASCII (`hq`, `b1`); the label carries the words.
5. Put the Kalpa theme at the top of every diagram:

```
%%{init: {"theme":"base","themeVariables":{"background":"#F2EEE3","primaryColor":"#F2EEE3","primaryBorderColor":"#2F6A3A","primaryTextColor":"#1E2A1F","lineColor":"#6B4226","secondaryColor":"#FCFAF4","tertiaryColor":"#E9E3D3","fontFamily":"Anek Latin, sans-serif"}}}%%
```

6. Colour roles with `classDef`, never new colours:
   - `classDef hq fill:#2F6A3A,color:#FFFFFF,stroke:#1D3A25` (leaf: HQ and the main thing)
   - `classDef world fill:#F2EEE3,color:#1E2A1F,stroke:#6B4226` (parchment with bark edge: worlds and products)
   - `classDef cloud fill:#C38E12,color:#1E2A1F,stroke:#6B4226` (gold: outside free services)
7. Under the diagram write 2 to 4 lines saying what it shows, so it still makes sense where Mermaid doesn't render.
8. Check: the block starts with ```` ```mermaid ````, every node used in a link exists, and nothing secret (keys, URLs with tokens, phone numbers) is in a label.

## Don'ts
- No emoji in labels, no gradients, no colours outside the four above plus the token text colour `#1E2A1F`.
- No screenshots of diagrams; the text is the source.
- Don't draw what doesn't exist yet as if it does: mark planned parts with a dashed link `-.->` and "(planned)".
