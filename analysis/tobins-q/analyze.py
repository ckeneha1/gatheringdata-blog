"""
Tobin's Q — Monthly Proxy Analysis
===================================
Builds a monthly-updated Tobin's Q estimate by rolling the official Z.1
quarterly data forward using monthly PPI deflators and equity market data.

Steps (matching SPEC.md):
  1. Reconstruct official Q from Z.1 component series
  2. Decompose the denominator into asset-type components
  3. Build the monthly proxy
  4. Validate proxy against official quarterly releases
  5. Produce the current estimate and all charts

Run:
    uv run python analyze.py [--output-dir PATH] [--fred-api-key KEY]

FRED API key: free at https://fred.stlouisfed.org/docs/api/api_key.html
Without a key the script uses anonymous access (120 req/min limit — sufficient
for this analysis since we cache all fetched series to .cache/).
"""

from __future__ import annotations

import argparse
import json
import os
import warnings
from pathlib import Path
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "public" / "images" / "tobins-q"
_CACHE_DIR = Path(__file__).parent / ".cache"

OUTPUT_DIR: Path = _DEFAULT_OUTPUT_DIR  # overridden by --output-dir at runtime

# ---------------------------------------------------------------------------
# Plot style — matches MTG post aesthetic
# ---------------------------------------------------------------------------
STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.color": "#e5e5e5",
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": True,
    "font.family": "sans-serif",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
}

ACCENT = "#2563eb"    # blue
ORANGE = "#ea580c"
GRAY   = "#6b7280"
RED    = "#dc2626"

# ---------------------------------------------------------------------------
# FRED series IDs
# ---------------------------------------------------------------------------
SERIES = {
    # Official Q components
    "equity_mktval":   "NCBEILQ027S",       # numerator: equity market value
    "net_worth":       "TNWMVBSNNCB",       # denominator: current-cost net worth

    # Denominator components (for decomposition + weighted deflation)
    "structures":      "RCSNNWMVBSNNCB",    # nonresidential structures, current cost
    "equipment":       "BOGZ1LM105015205Q", # equipment, current cost
    "inventories":     "BOGZ1LM105020015Q", # inventories, current cost
    "ip_products":     "BOGZ1LM105013765Q", # IP products, current cost

    # Monthly deflators
    "ppi_capital":     "WPUFD49207",        # PPI: final demand finished goods
    "ppi_construction":"WPUSI012011",       # PPI: construction
    "sp500":           "SP500",             # S&P 500 index (numerator proxy)
}

# ---------------------------------------------------------------------------
# Data fetching — FRED + Yahoo Finance, with file-based caching
# ---------------------------------------------------------------------------

def _cache_path(key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def _fetch_fred(series_id: str, api_key: str | None) -> pd.Series:
    """Fetch a FRED series, using local cache to avoid re-fetching."""
    cache = _cache_path(f"fred_{series_id}")
    if cache.exists():
        cached = json.loads(cache.read_text())
        # Invalidate if cache is older than 7 days
        age_days = (datetime.now(timezone.utc).timestamp() - cached["fetched_at"]) / 86400
        if age_days < 7:
            s = pd.Series(
                cached["values"],
                index=pd.to_datetime(cached["dates"]),
                name=series_id,
                dtype=float,
            )
            print(f"  [cache] {series_id} ({len(s)} obs)")
            return s

    print(f"  [fetch] {series_id} from FRED...")
    try:
        from fredapi import Fred
        key = api_key or os.environ.get("FRED_API_KEY")
        fred = Fred(api_key=key)
        s = fred.get_series(series_id)
    except ImportError:
        raise SystemExit("fredapi not installed. Run: uv sync")

    # Cache result
    valid = s.dropna()
    cache.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).timestamp(),
        "dates": [d.isoformat() for d in valid.index],
        "values": list(valid.values),
    }))
    s.name = series_id
    print(f"  [fetch] {series_id} done ({len(valid)} obs)")
    return s


def _fetch_yahoo(ticker: str, start: str = "1970-01-01") -> pd.Series:
    """Fetch monthly closing price from Yahoo Finance, with caching."""
    key = f"yahoo_{ticker.replace('^', '')}"
    cache = _cache_path(key)
    if cache.exists():
        cached = json.loads(cache.read_text())
        age_days = (datetime.now(timezone.utc).timestamp() - cached["fetched_at"]) / 86400
        if age_days < 7:
            s = pd.Series(
                cached["values"],
                index=pd.to_datetime(cached["dates"]),
                name=ticker,
                dtype=float,
            )
            print(f"  [cache] {ticker} ({len(s)} obs)")
            return s

    print(f"  [fetch] {ticker} from Yahoo Finance...")
    try:
        import yfinance as yf
    except ImportError:
        raise SystemExit("yfinance not installed. Run: uv sync")

    df = yf.download(ticker, start=start, interval="1mo", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    s = df["Close"].squeeze()
    s.index = s.index.tz_localize(None)
    s.name = ticker

    valid = s.dropna()
    cache.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).timestamp(),
        "dates": [d.isoformat() for d in valid.index],
        "values": list(valid.values),
    }))
    print(f"  [fetch] {ticker} done ({len(valid)} obs)")
    return s


def load_all_series(api_key: str | None) -> dict[str, pd.Series]:
    """Load all required series, returning a dict keyed by friendly name."""
    print("\nLoading data series...")
    data: dict[str, pd.Series] = {}
    for name, series_id in SERIES.items():
        data[name] = _fetch_fred(series_id, api_key)

    # Wilshire 5000 via Yahoo Finance (preferred total-market proxy)
    # Falls back to S&P 500 (already loaded above) if unavailable
    try:
        wilshire = _fetch_yahoo("^W5000")
        data["market_index"] = wilshire
        data["market_index_source"] = "Wilshire 5000 (^W5000)"
    except Exception:
        print("  [warn] Wilshire 5000 unavailable — using S&P 500 as numerator proxy")
        data["market_index"] = data["sp500"]
        data["market_index_source"] = "S&P 500 (SP500)"

    return data


# ---------------------------------------------------------------------------
# Step 1: Reconstruct official Q
# ---------------------------------------------------------------------------

def compute_official_q(data: dict[str, pd.Series]) -> pd.Series:
    """
    Official Tobin's Q = equity market value / current-cost net worth.
    Both series are in millions of USD, so no unit conversion needed.
    """
    num = data["equity_mktval"].dropna()
    den = data["net_worth"].dropna()
    q = (num / den).dropna()
    q.name = "Q_official"
    return q


# ---------------------------------------------------------------------------
# Step 2: Decompose the denominator
# ---------------------------------------------------------------------------

def compute_denominator_decomposition(data: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Align the four component series (structures, equipment, inventories, IP).
    Components are gross assets; net worth = gross assets - liabilities.
    Shares are computed relative to total measured gross assets.
    """
    component_keys = ["Structures", "Equipment", "Inventories", "IP Products"]
    components = {
        "Structures":  data["structures"],
        "Equipment":   data["equipment"],
        "Inventories": data["inventories"],
        "IP Products": data["ip_products"],
    }
    df = pd.DataFrame(components).dropna(how="all")

    df["Total Net Worth"] = data["net_worth"].reindex(df.index)
    df["Total Gross Assets (measured)"] = df[component_keys].sum(axis=1)

    # Shares relative to total measured gross assets (components sum to 100%)
    for col in component_keys:
        df[f"{col} Share"] = df[col] / df["Total Gross Assets (measured)"]

    return df


# ---------------------------------------------------------------------------
# Step 3: Build the monthly proxy
# ---------------------------------------------------------------------------

def to_month_end(s: pd.Series) -> pd.Series:
    """Resample any series to month-end frequency."""
    return s.resample("ME").last()


def _to_month_end_index(s: pd.Series) -> pd.Series:
    """Shift a series whose index is 'first of month' to month-end."""
    s = s.copy()
    s.index = s.index + pd.offsets.MonthEnd(0)
    return s


def compute_monthly_proxy(
    data: dict[str, pd.Series],
    q_official: pd.Series,
    decomp: pd.DataFrame,
) -> pd.DataFrame:
    """
    Roll the official Z.1 quarterly values forward on a monthly basis.

    Numerator: scale last quarterly equity market value by the change in the
    market index since that quarter-end.

    Denominator: scale each measured component (structures, equipment,
    inventories, IP) separately by the relevant monthly PPI deflator.
    Land + financial residual is held at its last quarterly value.
    """
    # Shift Z.1 quarterly series from first-of-month index to month-end.
    # Z.1 reports e.g. 2025-10-01; our monthly index is 2025-10-31.
    net_worth_me   = _to_month_end_index(data["net_worth"]).dropna()
    equity_me      = _to_month_end_index(data["equity_mktval"]).dropna()
    structures_me  = _to_month_end_index(data["structures"]).dropna()
    equipment_me   = _to_month_end_index(data["equipment"]).dropna()
    inventories_me = _to_month_end_index(data["inventories"]).dropna()
    ip_me          = _to_month_end_index(data["ip_products"]).dropna()
    q_official_me  = _to_month_end_index(q_official).dropna()

    ppi_cap     = to_month_end(data["ppi_capital"]).dropna()
    ppi_con     = to_month_end(data["ppi_construction"]).dropna()
    idx_monthly = to_month_end(data["market_index"]).dropna()

    # All available quarter-end dates (month-end aligned)
    q_dates = net_worth_me.index.tolist()

    # Build full monthly index
    start = max(ppi_cap.first_valid_index(), idx_monthly.first_valid_index(), q_dates[1])
    end   = min(ppi_cap.index[-1], idx_monthly.index[-1])
    all_months = pd.date_range(start, end, freq="ME")

    result = pd.DataFrame(index=all_months, dtype=float)
    result["Q_proxy"]    = np.nan
    result["Q_official"] = q_official_me.reindex(all_months)

    def _get(series: pd.Series, date) -> float:
        """Safely retrieve a value; return NaN if missing."""
        try:
            v = series[date]
            return float(v) if not pd.isna(v) else np.nan
        except KeyError:
            return np.nan

    def _fill_segment(anchor: pd.Timestamp, months: pd.DatetimeIndex) -> None:
        """
        For each month in `months`, project Q from `anchor` using PPI and
        market-index changes since that quarter-end.
        """
        nw0  = _get(net_worth_me,   anchor)
        eq0  = _get(equity_me,      anchor)
        s0   = _get(structures_me,  anchor)
        e0   = _get(equipment_me,   anchor)
        inv0 = _get(inventories_me, anchor)
        ip0  = _get(ip_me,          anchor)

        gross0 = s0 + e0 + inv0 + ip0
        if any(pd.isna(x) for x in [nw0, eq0, gross0]) or gross0 == 0:
            return

        w_s  = s0   / gross0
        w_e  = e0   / gross0
        w_i  = inv0 / gross0
        w_ip = ip0  / gross0

        ppi_cap0 = _get(ppi_cap,     anchor)
        ppi_con0 = _get(ppi_con,     anchor)
        idx0     = _get(idx_monthly, anchor)

        if any(pd.isna(x) for x in [ppi_cap0, ppi_con0, idx0]):
            return

        for m in months:
            pc  = _get(ppi_cap,     m)
            pco = _get(ppi_con,     m)
            im  = _get(idx_monthly, m)
            if any(pd.isna(x) for x in [pc, pco, im]):
                continue

            # Weighted deflator ratio: structures → construction PPI, rest → capital goods PPI
            deflator = w_s * (pco / ppi_con0) + (w_e + w_i + w_ip) * (pc / ppi_cap0)
            result.at[m, "Q_proxy"] = (eq0 * (im / idx0)) / (nw0 * deflator)

    # For each pair of consecutive quarters: anchor at q[i-1], project through q[i]
    # This is the honest approach — at q[i] the proxy is a genuine one-quarter forecast,
    # not a tautological reset, so validation errors are real.
    for i in range(1, len(q_dates)):
        anchor   = q_dates[i - 1]
        next_q   = q_dates[i]
        seg      = all_months[(all_months > anchor) & (all_months <= next_q)]
        _fill_segment(anchor, seg)

    # Project from the last official quarter forward (current estimate window)
    last_q     = q_dates[-1]
    future_seg = all_months[all_months > last_q]
    _fill_segment(last_q, future_seg)

    return result


# ---------------------------------------------------------------------------
# Step 4: Validate
# ---------------------------------------------------------------------------

def compute_validation(proxy_df: pd.DataFrame) -> pd.DataFrame:
    """
    At each quarter-end where we have an official Q reading, compare it to
    the proxy value for that same month.
    """
    val = proxy_df[["Q_official", "Q_proxy"]].dropna()
    val = val[val["Q_official"].notna() & val["Q_proxy"].notna()].copy()
    val["error"] = val["Q_proxy"] - val["Q_official"]
    val["abs_error"] = val["error"].abs()
    val["pct_error"] = val["error"] / val["Q_official"] * 100
    val["direction_match"] = (
        val["Q_official"].diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        ==
        val["Q_proxy"].diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    )
    return val


# ---------------------------------------------------------------------------
# Charting
# ---------------------------------------------------------------------------

def _apply_style() -> None:
    plt.rcParams.update(STYLE)


def _save(name: str) -> None:
    path = OUTPUT_DIR / name
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [chart] saved {path.name}")


def chart_official_q(q_official: pd.Series) -> None:
    """Chart 1: Official Tobin's Q, full history with mean and current."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 5))

    geo_mean = np.exp(np.log(q_official[q_official > 0]).mean())
    current  = q_official.iloc[-1]
    current_date = q_official.index[-1]

    ax.fill_between(q_official.index, q_official, geo_mean, where=(q_official >= geo_mean),
                    alpha=0.15, color=RED, label="_nolegend_")
    ax.fill_between(q_official.index, q_official, geo_mean, where=(q_official < geo_mean),
                    alpha=0.15, color=ACCENT, label="_nolegend_")
    ax.plot(q_official.index, q_official, color=ACCENT, linewidth=1.8, label="Official Q (Z.1)")
    ax.axhline(geo_mean, color=GRAY, linestyle="--", linewidth=1.2,
               label=f"Geometric mean ({geo_mean:.2f})")
    ax.axhline(1.0, color="#9ca3af", linestyle=":", linewidth=1.0, label="Q = 1.0")

    # Annotate current
    ax.annotate(
        f"Q = {current:.2f}\n({current_date.strftime('%b %Y')})",
        xy=(current_date, current),
        xytext=(-80, -40),
        textcoords="offset points",
        fontsize=9,
        color=ACCENT,
        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2),
    )

    ax.set_title("Tobin's Q — U.S. Nonfinancial Corporations, 1945–present", fontsize=13, pad=12)
    ax.set_ylabel("Q ratio (market value / replacement cost)")
    ax.legend(fontsize=9)
    _save("q_official.png")


def chart_decomposition(decomp: pd.DataFrame) -> None:
    """Chart 2: Gross asset component shares over time."""
    _apply_style()
    share_cols = [
        "Structures Share",
        "Equipment Share",
        "Inventories Share",
        "IP Products Share",
    ]
    colors = [ACCENT, ORANGE, "#16a34a", "#9333ea"]
    labels = ["Structures", "Equipment", "Inventories", "IP Products"]

    df = decomp[share_cols].dropna()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.stackplot(df.index, [df[c] for c in share_cols], labels=labels, colors=colors, alpha=0.85)
    ax.set_title("Gross Asset Composition: Nonfinancial Corporations, 1945–present", fontsize=13, pad=12)
    ax.set_ylabel("Share of measured gross assets")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    _save("q_decomposition.png")


def chart_proxy_vs_official(proxy_df: pd.DataFrame, market_index_source: str) -> None:
    """Chart 3: Monthly proxy vs. official quarterly Q, full backtest."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 5))

    official = proxy_df["Q_official"].dropna()
    proxy    = proxy_df["Q_proxy"].dropna()

    ax.plot(proxy.index, proxy, color=ACCENT, linewidth=1.5,
            label="Monthly proxy (this analysis)", alpha=0.9)
    ax.scatter(official.index, official, color=ORANGE, s=18, zorder=5,
               label="Official Q (Z.1, quarterly)", linewidths=0)

    ax.set_title("Monthly Q Proxy vs. Official Quarterly Q", fontsize=13, pad=12)
    ax.set_ylabel("Q ratio")
    ax.legend(fontsize=9)

    note = f"Numerator proxy: {market_index_source}. Denominator rolled forward with PPI for capital goods and construction."
    ax.annotate(note, xy=(0.01, 0.02), xycoords="axes fraction", fontsize=7.5, color=GRAY)

    _save("q_proxy_vs_official.png")


def chart_validation_error(val: pd.DataFrame) -> None:
    """Chart 4: Distribution of proxy error at quarter-ends."""
    _apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Error over time
    ax = axes[0]
    ax.bar(val.index, val["pct_error"], color=ACCENT, alpha=0.7, width=60)
    ax.axhline(0, color=GRAY, linewidth=1)
    ax.set_title("Proxy Error Over Time (% of official Q)", fontsize=11)
    ax.set_ylabel("Error (%)")
    mae = val["abs_error"].mean()
    mpct = val["pct_error"].abs().mean()
    ax.annotate(f"MAE: {mae:.3f}  |  Mean abs % error: {mpct:.1f}%",
                xy=(0.02, 0.96), xycoords="axes fraction", fontsize=9, color=GRAY,
                verticalalignment="top")

    # Error distribution histogram
    ax2 = axes[1]
    ax2.hist(val["pct_error"], bins=30, color=ACCENT, alpha=0.75, edgecolor="white")
    ax2.axvline(0, color=ORANGE, linewidth=1.5, linestyle="--")
    ax2.set_title("Error Distribution", fontsize=11)
    ax2.set_xlabel("Proxy − Official (% of official)")
    ax2.set_ylabel("Count (quarters)")

    direction_accuracy = val["direction_match"].mean() * 100
    ax2.annotate(f"Direction accuracy: {direction_accuracy:.0f}%",
                 xy=(0.97, 0.96), xycoords="axes fraction", fontsize=9, color=GRAY,
                 horizontalalignment="right", verticalalignment="top")

    plt.tight_layout()
    _save("q_proxy_error.png")


def chart_current_estimate(proxy_df: pd.DataFrame, val: pd.DataFrame) -> None:
    """Chart 5: The money chart — full history + proxy with uncertainty band."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 5))

    official = proxy_df["Q_official"].dropna()
    proxy    = proxy_df["Q_proxy"].dropna()

    # Uncertainty band: ±1 std of historical proxy percentage error
    std_pct = val["pct_error"].std() / 100
    upper = proxy * (1 + std_pct)
    lower = proxy * (1 - std_pct)

    # Find the last date where we have official data
    last_official_date = official.index[-1]

    # Shade the "current window" where only proxy data is available
    ax.axvspan(last_official_date, proxy.index[-1], alpha=0.07, color=ACCENT, label="_nolegend_")

    ax.fill_between(proxy.index, lower, upper, alpha=0.15, color=ACCENT, label="±1 std proxy error")
    ax.plot(proxy.index, proxy, color=ACCENT, linewidth=1.8, label="Monthly proxy")
    ax.scatter(official.index, official, color=ORANGE, s=18, zorder=5,
               label="Official Q (Z.1)", linewidths=0)

    geo_mean = np.exp(np.log(official[official > 0]).mean())
    ax.axhline(geo_mean, color=GRAY, linestyle="--", linewidth=1.1,
               label=f"Geometric mean ({geo_mean:.2f})")

    current_proxy = proxy.iloc[-1]
    current_date  = proxy.index[-1]
    ax.annotate(
        f"Proxy: {current_proxy:.2f}\n({current_date.strftime('%b %Y')})",
        xy=(current_date, current_proxy),
        xytext=(-90, -35),
        textcoords="offset points",
        fontsize=9,
        color=ACCENT,
        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2),
    )

    ax.set_title("Tobin's Q — Official (Quarterly) and Monthly Proxy", fontsize=13, pad=12)
    ax.set_ylabel("Q ratio")
    ax.legend(fontsize=9)
    ax.annotate("Shaded region: most recent quarter, proxy only (no official Z.1 data yet)",
                xy=(0.01, 0.02), xycoords="axes fraction", fontsize=7.5, color=GRAY)

    _save("q_current_estimate.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Tobin's Q proxy charts")
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR,
                        help="Directory to write chart PNGs")
    parser.add_argument("--fred-api-key", type=str, default=None,
                        help="FRED API key (optional — anonymous access used if omitted)")
    return parser.parse_args()


def main() -> None:
    global OUTPUT_DIR
    args = parse_args()
    OUTPUT_DIR = args.output_dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Load ---
    data = load_all_series(args.fred_api_key)

    # --- Step 1: Official Q ---
    print("\nStep 1: Computing official Q...")
    q_official = compute_official_q(data)
    print(f"  Q range: {q_official.index[0].date()} → {q_official.index[-1].date()}")
    print(f"  Current official Q: {q_official.iloc[-1]:.3f}")

    # --- Step 2: Decomposition ---
    print("\nStep 2: Decomposing denominator...")
    decomp = compute_denominator_decomposition(data)
    avg_gross = decomp["Total Gross Assets (measured)"].mean()
    avg_nw    = decomp["Total Net Worth"].mean()
    print(f"  Avg gross assets: ${avg_gross/1e6:.1f}T  |  Avg net worth: ${avg_nw/1e6:.1f}T")

    # --- Step 3: Monthly proxy ---
    print("\nStep 3: Building monthly proxy...")
    proxy_df = compute_monthly_proxy(data, q_official, decomp)
    current_proxy = proxy_df["Q_proxy"].dropna().iloc[-1]
    current_date  = proxy_df["Q_proxy"].dropna().index[-1]
    print(f"  Current proxy Q: {current_proxy:.3f} ({current_date.strftime('%b %Y')})")

    # --- Step 4: Validation ---
    print("\nStep 4: Validating proxy...")
    val = compute_validation(proxy_df)
    print(f"  Quarters validated: {len(val)}")
    print(f"  Mean absolute error: {val['abs_error'].mean():.4f}")
    print(f"  Mean abs % error:    {val['pct_error'].abs().mean():.2f}%")
    print(f"  Direction accuracy:  {val['direction_match'].mean():.1%}")

    # --- Step 5: Charts ---
    print("\nStep 5: Generating charts...")
    market_source = data.get("market_index_source", "S&P 500")
    chart_official_q(q_official)
    chart_decomposition(decomp)
    chart_proxy_vs_official(proxy_df, market_source)
    chart_validation_error(val)
    chart_current_estimate(proxy_df, val)

    # --- Export data ---
    csv_path = OUTPUT_DIR / "q_monthly_proxy.csv"
    proxy_df[["Q_official", "Q_proxy"]].round(4).to_csv(csv_path)
    print(f"\n  [data] exported {csv_path.name}")

    print(f"\nDone. Charts written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
