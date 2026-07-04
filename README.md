# Muyuan (002714 CH) — Hog Cycle Signpost Tracker

Successor to `pork-corn-china.streamlit.app`. Static dashboard (Chart.js, dark
theme) on GitHub Pages, data refreshed daily by GitHub Actions. The difference
vs v1: the front page is a **signpost scorecard wired to the 20-Mar-26 thesis**
— each signpost has an explicit trigger level, the latest reading, and a
green/amber status, so "is it time yet?" is answered by the page itself.

## Structure

```
index.html                      dashboard (single file, Chart.js)
data/live-data.json             all series, written by the fetcher
data/manual/*.csv               hand-maintained series (folded into the json)
scripts/fetch_data.py           akshare fetcher, keeps stale values on failure
.github/workflows/update-data.yml   daily 04:00 UTC cron + manual trigger
```

## Data

**Auto (daily):** weekly national hog price index (2015–), daily lean hog /
15kg piglet / corn / soybean / mixed feed (soozhu), DCE live-hog, corn and
soybean-meal main contracts (Sina), Muyuan A/H closes (Sina). Any source that
fails keeps its previous values — the dashboard never blanks.

**Manual (`data/manual/*.csv` — edit, commit, the next cron folds them in):**

| file | update when |
|---|---|
| `sow_inventory.csv` | NBS quarterly sow print (~mid Jan/Apr/Jul/Oct); Muyuan quarterly |
| `price_checkpoints.csv` | a broker report gives self-breeding profit/loss per head |
| `effective_supply.csv` | GS S/D refresh or actual slaughter data |
| `street_estimates.csv` | new TP / hog price deck |
| `distress_events.csv` | producer default / restructuring / bankruptcy news |
| `muyuan.csv` | replacement / EV-per-head anchors, cost data |

To refresh locally: `pip install akshare pandas && python scripts/fetch_data.py`,
then open `index.html` via any static server (`python -m http.server`).

## Signposts (from the 20-Mar-26 memo)

1. Sow herd ≤37.5mn (moderate turn) / 36.5 (strong) / 35 (super-cycle)
2. Liquidation pace fast enough for the MARA end-Sep-26 deadline
3. PSY-adjusted output rolling ≥5% y/y (the "effective supply" fix)
4. Producer capitulation: sustained cash losses + distress events
5. Piglet price below rebuild-appetite levels (7kg < Rmb200/head)
6. Feed-cost overhang cleared (was: Hormuz risk)
7. Spot trough behind us with narrowing losses
8. Valuation below replacement cost (H ≈ HK$34.5 per GS)

Sources: GS 30-Jun-26, HSBC Qianhai 25-Jun-26, Macquarie 3-Jul-26; NBS/MOA prints.
