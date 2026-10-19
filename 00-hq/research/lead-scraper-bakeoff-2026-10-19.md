# Lead scraper bake-off: ScrapeGraphAI vs Crawl4AI (+ free AI models), 19 Oct 2026

Question (Akhil, 19 Oct): clone ScrapeGraphAI, compare with free Hugging Face models, pick the best free open-source option and use it for lead generation in all 8 worlds.

## Verdict
**Crawl4AI (Apache-2.0) for reading websites + NuExtract3 4B (Apache-2.0, Hugging Face) for the optional AI step.**
ScrapeGraphAI stays out. Built as `00-hq/leads/kalpa_leads.py` (23 offline tests, live-tested on real sites).

## What was tested (live, in this cloud box: 2 vCPU / 7 GB, same as a private-repo GitHub runner)
Same 8 real Hyderabad business sites (Naturals, Green Trends, Lakmé Salon, CBIT, Aparna Constructions, Partha Dental, cult.fit, Jawed Habib).

| | ScrapeGraphAI 2.3.1 | Crawl4AI 0.9.5 | Our old urllib enricher |
|---|---|---|---|
| Licence | MIT | Apache-2.0 | ours |
| Last commit | 6 Oct 2026 | 15 Oct 2026 | — |
| Install size (venv) | 537 MB (LangChain stack) | 835 MB (Playwright, LiteLLM) | stdlib |
| Sites read | 8/8 | 8/8 | 8/8 |
| Avg time per site | 4.0 s | 4.8 s | 1.3 s |
| Renders JavaScript | yes | yes | no (missed Naturals' WhatsApp button) |
| Text sent to an AI per page | **~7,600 tokens avg** (60.6k for 8 pages; it sends the whole page) | **~1,960 tokens avg** with its pruning filter (~74% less) | n/a |
| Works with no AI at all | no: every page needs an LLM call | yes (contacts by rules; AI optional) | yes |
| robots.txt | separate "robots node", off by default | built-in `check_robots_txt=True` | built-in |
| Anti-bot extras shipped | free-proxy rotation, undetected-playwright | stealth mode (we leave it off) | none |

Why ScrapeGraphAI lost: it needs an LLM call for every page and sends ~4x more text, which burns free-tier limits (Groq 8k tokens/min, OpenRouter free daily caps). Its built-in proxy-rotation and undetected-browser helpers also pull toward evasion, which our rules (robots.txt, no banned sources) forbid.

## Free AI models for the "qualify" step (Hugging Face)
| Model | Licence | Result |
|---|---|---|
| **numind/NuExtract3 4B** (Q4_K_M GGUF, 2.8 GB) | Apache-2.0 | Live: 4/4 real pages gave valid JSON. 35–73 s per page on 2 CPUs, no key, no limit. Vendor benchmark: 0.651 vs Qwen3.5-9B 0.479, Nemotron-3-Nano-Omni 0.387 (vendor's own benchmark, unverified by a second source). Weakness seen: over-ticks multi-choice lists (Made Easy listed JEE/NEET/bank). |
| jinaai/ReaderLM-v2 | CC-BY-NC-4.0 | **Excluded**: non-commercial |
| Nemotron 3.5 Super VL (OpenRouter free) | NVIDIA open model licence | Our 19 Oct bake-off winner (5/5). Faster and smarter, but needs the OpenRouter key (secret) and has free daily caps. Optional backend `--llm openrouter`. |

## Limits (checked today)
- GitHub private repo runner: 2 vCPU, 8 GB RAM, 14 GB SSD (docs.github.com, github-hosted-runners page, fetched 19 Oct).
- GitHub Free: 2,000 Actions minutes/month (docs.github.com "GitHub's plans", fetched 19 Oct). One NuExtract run of 20 sites is about 25–30 min, so about 60 such runs a month fit. Runs with `--llm none` take ~5 min.

## Rules baked into the code
Business sites only; Google Maps / Justdial / Instagram / Facebook / LinkedIn / IndiaMART URLs are refused; robots.txt checked; 1 s pause; lists are private 7-day artifacts, never committed; no automatic messages (TRAI, WhatsApp opt-in); Trading Lab finds research data sources only (SEBI).
