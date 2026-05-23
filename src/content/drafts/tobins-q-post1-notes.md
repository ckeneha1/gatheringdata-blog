# Tobin's Q — Post 1 Working Notes
**Status:** Paused for strategic rethink
**Last updated:** April 2026

---

## Where We Are

The analysis script (`analysis/tobins-q/analyze.py`) runs end-to-end and produces 5 charts plus a CSV. The spec is at `analysis/tobins-q/SPEC.md`. The methodological novelty is real, but the validation results complicate the story in ways worth thinking through before writing.

**Current validation results:**
- 147 quarters validated
- Mean absolute error: **0.073** (on a ratio that ranges ~0.3–2.0)
- Mean absolute % error: **6.5%**
- Direction accuracy: **55.8%** — barely above a coin flip

The direction accuracy number is the central tension. More on that below.

---

## The Two Schools of Thought (Worth Including in the Post)

There are essentially two practitioners who maintain public Tobin's Q estimates. Everyone else either cites them or republishes the raw quarterly Z.1 dots.

### School 1: Numerator-only updating (dshort / Smithers)

**Doug Short / Jill Mislinski (Advisor Perspectives)** — publishing since ~2009. Between Z.1 releases, they scale the last-known equity market value by the change in VTI (Vanguard Total Stock Market ETF). The denominator — replacement cost net worth — is held constant at the most recent Z.1 reading.

**Andrew Smithers (Smithers & Co.)** — publishing since ~2000, recently retired at 87. Same approach, using S&P 500 instead of VTI. Published an internal paid report called "A Monthly Proxy for q Using S&P 500 Data" — the title itself confirms it's numerator-only. Also notable: Smithers publishes "q ex IP" alongside standard q, arguing IP products should be excluded from replacement cost entirely. This is the only denominator distinction either school makes, and it's a binary inclusion/exclusion, not a decomposition.

**The shared assumption:** the denominator doesn't move enough between quarters to matter for a between-release estimate. The market (numerator) is the volatile component; replacement cost of physical assets moves slowly.

### School 2: This analysis

Attempt to update **both sides** of the ratio. The denominator is rolled forward monthly using component-weighted PPI deflators: construction PPI for structures, capital goods PPI for equipment/inventories/IP. Component weights are the time-varying gross-asset shares from the Z.1 sub-series.

The numerator uses the Wilshire 5000 (from Yahoo Finance) scaled from the last quarterly equity market value.

**What this adds that neither school has done publicly:**
- Rolling the denominator between releases (the core novelty)
- Decomposing the denominator into 4 asset components with separate deflators
- Formal validation (MAE, % error, directional accuracy) against subsequent official releases
- Uncertainty band on current estimate
- Open-source Python/FRED implementation (no public GitHub repo for aggregate Q exists anywhere)

---

## The Validation Problem

The 55.8% directional accuracy is the honest finding that complicates the post.

What it means: knowing which way PPI moved last quarter doesn't reliably tell you whether Q went up or down. There are two possible explanations:

**Explanation 1 — Methodology:** The PPI series we're using are imperfect proxies for the BEA's actual replacement cost deflators. The BEA uses its own chain-type price indices (released quarterly in the GDP report), which are based on more granular deflation methodologies than top-level PPI. Our weights (gross asset shares) may also be mismeasured since they're based on the same Z.1 sub-series that includes the noise we're trying to smooth.

**Explanation 2 — Genuine finding:** The denominator (replacement cost of nonfinancial corporate assets) actually doesn't move enough quarter-to-quarter to be predictable from monthly PPI data. If this is true, then the two-school consensus (numerator-only) is not just pragmatic — it may be roughly optimal given available data. In that case, the more interesting question is what drives the *level* of Q over longer horizons (the intangibles/profit margins/market power debate from the literature), not what drives the quarter-to-quarter changes.

These two explanations have different implications for the post:

- If Explanation 1: the post is about improving the proxy methodology (better deflators, better weights)
- If Explanation 2: the post pivots toward the decomposition question — why has Q been elevated for so long, and what does each denominator component tell us about it?

---

## Open Questions Before Writing

1. **What does the error look like by era?** Does the proxy perform better in some periods (e.g., high-inflation 1970s, where PPI is more volatile and asset repricing is faster) than others (post-2010 low-inflation environment)? If the proxy is better in inflationary periods, that's an interesting finding — and potentially relevant right now.

2. **How does numerator-only compare?** We should compute a "dshort baseline" (numerator-only, denominator held constant) and compare its validation stats to our PPI-rolled version. If ours is worse, that's a finding. If ours is better, even by a small margin, that's a different finding. Either is honest and interesting.

3. **Does the IP exclusion matter?** Smithers argues IP should be excluded. The BEA only started capitalizing R&D in 2013, creating a structural break. We could show "Q with IP" vs "Q ex IP" — does the denominator decomposition chart make this visible?

4. **What is the current estimate actually saying?** Proxy Q of 1.953 (Feb 2026) vs official Q of 1.980 (Q3 2025). Our proxy suggests slight compression from the all-time high. Is that signal or noise given our 6.5% average error?

---

## Possible Post Structures

**Option A — Methodology-first**
Lead with the problem (Q is stale), explain the two schools of thought, introduce the PPI rolling approach as a third school, then report validation results honestly including the limitations. Frame the 55.8% directional accuracy as "here's what we learned, and here's what it tells us about the denominator." This is the most intellectually honest structure but requires comfort with a mixed result as the punchline.

**Option B — Decomposition-first**
Lead with the asset decomposition (what's actually in the denominator, and how has its composition changed over time). Let the IP/intangibles story be the hook. The monthly proxy is a methodological tool in service of that question, not the story itself. More accessible, more obviously interesting to a general reader.

**Option C — Split into two posts**
Post 1: The two schools of thought + the decomposition chart (what's in the denominator, how it's changed, the IP break in 2013). This can be published now from what we have.

Post 2: The monthly proxy methodology, validation results, and current estimate. Requires resolving the open questions above — specifically adding the numerator-only baseline comparison.

Option C may be the right call. The decomposition story is clean and publishable. The proxy story needs one more iteration.

---

## Technical State

All code is working. To re-run:
```
cd analysis/tobins-q
uv run python analyze.py --fred-api-key YOUR_KEY
```

Charts are in `public/images/tobins-q/`. Series cached in `analysis/tobins-q/.cache/` (7-day TTL).

The next technical task (if we continue with the proxy post) is adding a numerator-only baseline to the validation step for direct comparison against the PPI-rolled approach.

---

## Files
- `analysis/tobins-q/SPEC.md` — full spec for Post 1
- `analysis/tobins-q/analyze.py` — working analysis script
- `analysis/tobins-q/pyproject.toml` — dependencies (fredapi, yfinance, pandas, matplotlib)
- `public/images/tobins-q/` — 5 charts + 1 CSV
