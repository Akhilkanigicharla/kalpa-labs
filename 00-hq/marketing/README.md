# 📣 Kalpa marketing team (every world)

The BotBhai Social Team engine (`01-botbhai/botbhai/social/`), run for Kalpa Labs itself and every world, in the Kalpa design system.

| World | Profile | Colour | Notes |
|---|---|---|---|
| HQ · Kalpa Labs | `brands/hq.json` | --l0 | Build-in-public posts |
| b1 · BotBhai | `brands/b1.json` | --l1 | Selling BotBhai to salon owners (client posts use `setups/`) |
| b2 · JobCard | `brands/b2.json` | --l1 | Waitlist until the 2027 AC season |
| b3 · Kits | `brands/b3.json` | --l2 | GATE + tax/SIP kits |
| b4 · Tab Lifeboat | `brands/b4.json` | --l3 | English only |
| b5 · Deals & Tools | `brands/b5.json` | --l4 | Affiliate: every post gets #ad + disclosure (ASCI) |
| b6 · Ledger Peaks | `brands/b6.json` | --l5 | No "compliant/certified/save X%" claims |
| b7 · Trading Lab | `brands/b7.json` | --l7 | **Switched off**: paper-only research, SEBI finfluencer risk |

```bash
python3 00-hq/marketing/run.py --world all --weeks 4 --out out/marketing   # plan, captions, images, approval message per world
python3 00-hq/marketing/run.py --world b6 --out out/marketing --reply "ok"  # Akhil approves
python3 00-hq/marketing/test_marketing.py                                  # tests (also in test-all.sh)
```

Every post stays **held** until: the real product link replaces `[add link]` in the profile, real screenshots/photos/reviews are added where asked, and Akhil says OK. Publishing uses the same official Meta API publisher (dry run by default); accounts and tokens are Akhil's to create and hold.

Fonts: `00-hq/design/fonts/` (Rozha One, Anek Latin, Anek Telugu; OFL, from @fontsource 5.3.0).
