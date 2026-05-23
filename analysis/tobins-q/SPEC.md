# Spec: A More Current Tobin's Q
## Post 1 — Building a Monthly Q Proxy

**Status:** Draft
**Last updated:** 2026-04-04

---

## Problem Statement

The Federal Reserve's Z.1 Financial Accounts release is the canonical source for Tobin's Q. It is published quarterly with a 60–90 day lag, meaning the most recent official Q reading is always 2–3 months stale. The widely-cited dshort/Advisor Perspectives approach addresses the numerator staleness (extrapolating market cap forward with VTI) but holds the denominator constant between releases. The denominator — replacement cost of nonfinancial corporate net worth — actually moves between quarters as capital goods prices, construction costs, and inventory values change.

This post builds a monthly-updated Q proxy that updates both sides of the ratio and validates it against the official quarterly releases.

---

## Decision It Unlocks

A reproducible, open-source monthly Q estimate gives us:
1. A current signal that is meaningfully more up-to-date than the official series
2. A decomposition framework for Post 3 — we'll know exactly which denominator components are moving and why
3. A methodological foundation for Post 2's leading indicator tests

---

## What Tobin's Q Is (for the post)

Q = Market value of nonfinancial corporate equities / Current-cost (replacement cost) net worth of nonfinancial corporations

- **Numerator**: What the market says all U.S. nonfinancial corporations are worth today
- **Denominator**: What it would cost to physically rebuild those corporations' asset bases at today's prices
- **Q > 1**: Market prices exceed replacement cost → market is paying a premium over the cost of the underlying assets
- **Q < 1**: Market prices are below replacement cost → would be cheaper to buy existing firms than build new ones
- **Long-run mean reversion**: Historical geometric mean is ~0.7. Current reading (~2.0) is ~170% above that mean.

---

## Data Sources

All data pulled via FRED API (free, no key required for basic access; API key unlocks higher rate limits).

### Official Q Components (Quarterly Anchors)

| Series ID | Description | Frequency | Role |
|---|---|---|---|
| `NCBEILQ027S` | Nonfinancial Corp Business; Corporate Equities; Liability, Level | Quarterly | Official numerator |
| `TNWMVBSNNCB` | Nonfinancial Corp Business; Net Worth, Level (current-cost) | Quarterly | Official denominator |

The official Q = `NCBEILQ027S / TNWMVBSNNCB` (both in millions of dollars, so no unit adjustment needed).

### Denominator Component Series (Quarterly, for decomposition)

| Series ID | Description |
|---|---|
| `RCSNNWMVBSNNCB` | Nonresidential Structures, current-cost basis |
| `BOGZ1LM105015205Q` | Equipment, current-cost basis |
| `BOGZ1LM105020015Q` | Inventories, current-cost basis |
| `BOGZ1LM105013765Q` | Nonresidential IP Products, current-cost basis |

These four components sum to most of the asset side of the denominator (net of liabilities). We will validate that they account for a stable share of TNWMVBSNNCB over time.

### Monthly Proxy Series (for rolling forward)

| Series ID | Description | Frequency | Used to proxy |
|---|---|---|---|
| `SP500` | S&P 500 Index | Daily → monthly | Numerator movement |
| `WPUFD49207` | PPI: Final Demand Finished Goods | Monthly | Equipment + inventory price changes |
| `PCUOMFGOMFG` | PPI: Durable Manufacturing | Monthly | Equipment price changes (verify vs WPUFD49207) |
| `WPUSI012011` | PPI: Construction | Monthly | Structures price changes |
| `A008RD3Q086SBEA` | BFI Nonresidential Fixed Investment Price Index | Quarterly | Validation cross-check for deflation |
| `BAMLC0A0CM` | ICE BofA IG Corporate OAS | Daily → monthly | Leading indicator (Post 2 preview) |

**Note on Wilshire 5000**: FRED removed the Wilshire series in June 2024. We use `SP500` as the numerator proxy, scaling the last known Z.1 equity value by the percentage change in the S&P 500 since that quarter-end. This is a simplification (the Z.1 numerator covers all nonfinancial corps, not just S&P 500 constituents), but the S&P 500 tracks total market cap closely enough (~85% correlation in monthly changes) to be a valid proxy. We will document this limitation explicitly.

**Note on IP and Land**: Intellectual property and land are the two denominator components with no clean monthly deflator on FRED. We will hold them at their last quarterly value between releases. This is a known limitation — we will quantify how large these components are as a share of total net worth so readers can assess the materiality of the assumption.

---

## Methodology

### Step 1: Reconstruct Official Q (1945–present)

Pull `NCBEILQ027S` and `TNWMVBSNNCB` from FRED. Compute Q = numerator / denominator. Validate that this matches the published dshort series and the FRED graph at `fred.stlouisfed.org/graph/?g=xtC`.

### Step 2: Decompose the Denominator

Pull the four component series. Verify they sum to ~TNWMVBSNNCB (the difference will be financial assets net of liabilities). Plot the component shares over time. This gives us the weights for the monthly roll-forward and surfaces the intangibles/IP question visually.

### Step 3: Build the Monthly Proxy

Between quarterly Z.1 releases, update each denominator component using the monthly PPI proxy:

```
equipment_proxy(t) = equipment_value(last_Q) × PPI_capital_goods(t) / PPI_capital_goods(last_Q_end)
structures_proxy(t) = structures_value(last_Q) × PPI_construction(t) / PPI_construction(last_Q_end)
inventory_proxy(t) = inventory_value(last_Q) × PPI_finished_goods(t) / PPI_finished_goods(last_Q_end)
IP_proxy(t) = IP_value(last_Q)   # held constant
land_proxy(t) = land_proxy(last_Q)  # held constant (residual)

denominator_proxy(t) = sum of above + net_financial_liabilities(last_Q)

numerator_proxy(t) = equity_value(last_Q) × SP500(t) / SP500(last_Q_end)

Q_proxy(t) = numerator_proxy(t) / denominator_proxy(t)
```

Each time a new Z.1 release comes in, the proxy resets to the official value.

### Step 4: Validate

Compare Q_proxy (monthly) to official Q (quarterly) over the full history where we have data. Compute:
- Mean absolute error (MAE) between proxy at quarter-end and official quarterly value
- Whether the proxy captures the direction of quarterly Q movements correctly (precision on direction, not just level)
- How the proxy performs in volatile periods (2000, 2008, 2020) vs. calm periods

This validation section is the scientific core of the post — it's what distinguishes this from "I guessed at something" vs. "I tested it."

### Step 5: Current Estimate

Apply the proxy to produce the most current Q estimate available. Show:
- The official quarterly Q series (dots or bars)
- The monthly proxy Q (line)
- A highlighted region showing the "current window" where only proxy data is available
- Confidence band (±1 standard deviation of historical proxy error)

---

## Outputs

### Charts (5 planned)

1. **Official Q, 1945–present** — the anchor chart. Long-run mean (geometric), current reading, historical peaks (2000 dot-com, 2021–present). This is the "here's what we're measuring" chart.
2. **Denominator decomposition** — stacked area chart of net worth components (structures, equipment, inventories, IP, land) as % of total, over time. Shows the rising IP share and where the data gaps are.
3. **Proxy vs. official validation** — dual-axis or overlay: quarterly official Q (dots) vs. monthly proxy Q (line) over the backtest period. The residuals should be small.
4. **Proxy error distribution** — histogram or scatter of (proxy value at quarter-end) vs. (official value that quarter), with regression line. Shows how accurate the proxy is.
5. **Current estimate** — the money chart: full history + proxy estimate with uncertainty band for the current window.

### Data File

A CSV of the monthly Q proxy series, published alongside the post, for readers who want to use it.

---

## Open Questions

1. **PPI series selection**: We have `WPUFD49207` (Final Demand Finished Goods) but need to verify this is the right series for deflating equipment. The more specific series `PCUOMFGOMFG` (Durable Manufacturing PPI) may be better. We'll test both and pick the one with lower validation error.

2. **S&P 500 vs. total market cap**: S&P 500 is a large-cap index; a total market index would better match the Z.1 numerator. Without Wilshire on FRED, our options are: (a) use S&P 500 and document the limitation, (b) pull Wilshire data from Yahoo Finance (`^W5000`). Recommend attempting Yahoo Finance first and falling back to S&P 500 if the data is unreliable.

3. **Net financial liabilities**: The denominator (TNWMVBSNNCB) is net worth, meaning it already subtracts liabilities. We don't need to explicitly model the liability side — but we should confirm the component series (structures + equipment + inventories + IP) account for a stable enough fraction of gross assets that our weights remain valid over time.

4. **IP capitalization break in 2013**: The BEA began capitalizing R&D in the 2013 NIPA revision, which structurally changed the denominator. This may create a visible level shift in the decomposition chart. We should note it and investigate whether it shows up as a break in the proxy validation error.

---

## What This Post Is Not

- Not a forecast or market timing signal — we will be explicit that high Q does not tell you when the market will correct, only that it historically has
- Not an endorsement of the Q ratio as the definitive valuation metric — we'll note Smithers/Wright and the intangibles debate in the methodology section
- Not a replacement for the official Z.1 data — it's a more timely read on the same underlying signal

---

## Scale Considerations

The analysis runs on ~80 years of quarterly data and ~40 years of monthly PPI data. No scale issues. Runtime will be seconds. The FRED API is rate-limited at 120 requests/minute for anonymous access; a free API key raises this to 1,000/minute. We'll request one before building.

---

## Relationship to Future Posts

- **Post 2** (Leading indicators): Uses the monthly Q proxy as the dependent variable. Tests whether credit spreads (`BAMLC0A0CM`), PPI changes, and NIPA profits lead the proxy by 1–3 months.
- **Post 3** (Decomposition): Uses the component series from Step 2 to ask which components are driving the sustained Q elevation — and whether the answer is intangibles, profit margins, or something else.
