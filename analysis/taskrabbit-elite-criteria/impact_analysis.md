# Post-rollout impact: Elite cancellation threshold

**Observed (shareable) fact:** after rollout, **1.5× as many Taskers met the Elite
cancellation-rate bar** as before — i.e. broad downward pressure on tasker-fault
cancellation as more Taskers held to lower monthly cancel rates.

**Question:** project the invoice-volume and revenue impact, at **$135 / invoice**.

Numbers below use the synthetic US supply for scale (`taskers_clustered.csv`); the
mechanism and bridge are the transferable part. Run `impact_analysis.py` to reproduce.

---

## Mechanism (the core identity)

A tasker-fault cancellation is a booking the Tasker killed. Avoid it and the booking
completes instead:

> **avoided cancellation → completed booking → +1 invoice → +$135**
>
> ΔRevenue = (avoided cancellations) × completion × $135

`completion` (< 1) is a haircut: a recovered booking still faces residual
fall-through (client cancel, no-show).

## Baseline scale (US)

| | |
|---|---|
| Taskers | 58,571 |
| Annual invoices | ~1.50M |
| Annual revenue @ $135 | ~$202M |
| Annual tasker-fault cancellations | ~83,500 |
| …in program-responsive supply (≥2 jobs/mo) | ~55,700 (67% of cancels) |
| Theoretical ceiling (100% eliminated) | ~$11.3M/yr |

Only the **responsive supply** (Taskers doing ≥2 jobs/month, who actually chase Elite
status) is modeled as changing behavior; casual Taskers are held flat. That already
scopes out a third of the cancellation pool.

## Bridge: turning "1.5× compliance" into a cancellation reduction

Headcount can't be used directly (in the mock, most low-volume Taskers trivially sit
below the bar, so ×1.5 overshoots). Instead, model per-Tasker cancel rate as
lognormal (σ ≈ 0.8, fit to the data). If the share below a fixed bar rises from `p0`
to `1.5·p0`, the whole distribution shifts left and the **mean cancel rate — hence
total cancellations — scales by `exp(-σ·(z₁−z₀))`**:

| Pre-rollout compliance `p0` | → post `1.5·p0` | Cancellations fall by |
|---|---|---|
| 0.45 | 0.68 | ~37% |
| 0.50 | 0.75 | ~41% |
| 0.55 | 0.83 | ~47% |
| 0.60 | 0.90 | ~56% |

Central read: pre-rollout roughly half the evaluated supply met the bar → **~45%
fewer cancellations**. This is the model's most sensitive input, so it's carried as a
range, not a point.

## Projection (annual, US)

| Scenario | Cancel reduction | Completion | Recovered invoices/yr | Revenue impact/yr |
|---|---|---|---|---|
| Conservative | 35% | 0.70 | +13,600 (+0.9%) | **+$1.8M** (+0.9%) |
| **Central** | **45%** | **0.85** | **+21,300 (+1.4%)** | **+$2.9M (+1.4%)** |
| Optimistic | 55% | 1.00 | +30,600 (+2.0%) | **+$4.1M** (+2.0%) |

See `fig_impact_scenarios.png` and the `fig_impact_sensitivity.png` grid.

**Headline:** ~**+$2.9M/yr** in recovered revenue and ~**+21k invoices/yr** (a ~1.4%
lift), plausible range **$1.8M–$4.1M/yr**.

## Caveats & extensions

- **Direct channel only.** This counts recovered bookings. Second-order upside —
  better client retention / repeat rate from higher reliability, fewer support costs —
  is real but not quantified here; it would push the estimate up.
- **Most sensitive lever** is the pre-rollout compliance base behind the 1.5×. If it
  was well over half, the cancellation reduction (and impact) is larger.
- **Global** supply is ~1.33× the US Tasker base; a rough global figure scales
  accordingly (~$3.8M central), with the local-currency 1:1 caveat from the deck.
- `completion` and `responsive-supply share` are explicit dials in `impact_analysis.py`.
