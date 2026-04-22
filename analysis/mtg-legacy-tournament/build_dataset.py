"""
build_dataset.py — MTG Legacy Tournament Dataset Builder

Reads all cached raw files produced by fetch_data.py and outputs:
  data/decks.csv        — master flat table, one row per (deck_id, card_name, zone)
  data/card_metrics.json — per-card aggregated metrics under 4 weighting schemes

Run:  uv run build_dataset.py
      uv run build_dataset.py --skip-csv   (skip decks.csv, just recompute metrics)
"""

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR  = DATA_DIR / "raw"

BANLIST_PATH     = DATA_DIR / "banlist.json"
DECKS_CSV_PATH   = DATA_DIR / "decks.csv"
METRICS_PATH     = DATA_DIR / "card_metrics.json"


# ---------------------------------------------------------------------------
# Step 1: Load raw data
# ---------------------------------------------------------------------------

def load_events() -> list[dict]:
    """Load all events_{year}.json files into a flat list of event dicts."""
    events = []
    for path in sorted(RAW_DIR.glob("events_*.json")):
        year_events = json.loads(path.read_text())
        events.extend(year_events)
    print(f"  Loaded {len(events)} events from {len(list(RAW_DIR.glob('events_*.json')))} files")
    return events


def load_deck(deck_id: int) -> dict | None:
    path = RAW_DIR / f"deck_{deck_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_banlist() -> list[str]:
    """Return sorted list of currently banned card names."""
    if not BANLIST_PATH.exists():
        print("  WARNING: banlist.json not found — all cards treated as legal")
        return []
    data = json.loads(BANLIST_PATH.read_text())
    return data.get("banned", [])


# ---------------------------------------------------------------------------
# Step 2: Parse event dates
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> date | None:
    """Parse DD/MM/YY format from MTGTop8."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%y").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Step 3: Build legality index
#
# The banlist from Scryfall is the *current* list only. We don't have dated
# ban/unban history, so we use a conservative approximation: a card is treated
# as legal unless it appears in the current banned list.
#
# Known limitation: cards banned or unbanned mid-period will be incorrectly
# marked. The SPEC.md §8 open question documents this. For post purposes this
# is acceptable — the banlist mainly affects fringe Legacy cards (Lurrus,
# Ragavan, White Plume, Mox Emerald/Jet/Pearl/Ruby/Sapphire, etc.) and the
# gap analysis uses only legal rows.
# ---------------------------------------------------------------------------

def build_legality_fn(banned_names: list[str]):
    """Return a function: card_name -> bool (is legal / not currently banned)."""
    banned_set = {n.lower() for n in banned_names}
    def is_legal(card_name: str) -> bool:
        return card_name.lower() not in banned_set
    return is_legal


# ---------------------------------------------------------------------------
# Step 4: Assemble master flat table
# ---------------------------------------------------------------------------

def build_flat_table(events: list[dict], is_legal) -> pd.DataFrame:
    """Assemble one row per (event_id, deck_id, card_name, quantity, zone)."""
    rows = []
    missing_deck_ids = 0

    for event in events:
        event_id    = event["event_id"]
        event_name  = event.get("event_name", "")
        date_str    = event.get("date_str", "")
        player_count = event.get("player_count", 0)
        star_count  = event.get("star_count", 0)
        event_date  = parse_date(date_str)

        for deck_ref in event.get("decks", []):
            placement  = deck_ref.get("placement", 0)
            deck_id    = deck_ref["deck_id"]
            archetype  = deck_ref.get("archetype_name", "")

            deck = load_deck(deck_id)
            if deck is None:
                missing_deck_ids += 1
                continue

            for zone in ("mainboard", "sideboard"):
                for entry in deck.get(zone, []):
                    card_name = entry["card_name"]
                    quantity  = entry["quantity"]
                    rows.append({
                        "event_id":      event_id,
                        "event_name":    event_name,
                        "event_date":    event_date,
                        "player_count":  player_count,
                        "star_count":    star_count,
                        "placement":     placement,
                        "deck_id":       deck_id,
                        "archetype_name": archetype,
                        "card_name":     card_name,
                        "quantity":      quantity,
                        "zone":          zone,
                        "legal":         is_legal(card_name),
                    })

    if missing_deck_ids:
        print(f"  WARNING: {missing_deck_ids} deck refs had no cached file — run fetch_data.py --decks-only")

    df = pd.DataFrame(rows)
    print(f"  Flat table: {len(df):,} rows, {df['deck_id'].nunique():,} decks, {df['card_name'].nunique():,} unique cards")
    return df


# ---------------------------------------------------------------------------
# Step 5: Compute card metrics under 4 weighting schemes
# ---------------------------------------------------------------------------

def placement_weight(placement: int) -> float:
    """8 for 1st place, 1 for 8th, 0 for unplaced (placement=0 or >8)."""
    if placement <= 0 or placement > 8:
        return 0.0
    return float(9 - placement)


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    For each card and zone, compute prevalence under 4 weighting schemes.

    prevalence(card, scheme) = weighted_copies(card) / total_weight(all decks)

    Schemes:
      flat      weight = 1
      placement weight = max(0, 9 - placement)
      prestige  weight = star_count
      combined  weight = (9 - placement) * star_count
    """
    # Work only on legal rows
    legal = df[df["legal"]].copy()

    # Add weight columns per deck (one row per card; weights are deck-level attributes)
    legal["w_flat"]      = 1.0
    legal["w_placement"] = legal["placement"].apply(placement_weight)
    legal["w_prestige"]  = legal["star_count"].astype(float)
    legal["w_combined"]  = legal["w_placement"] * legal["w_prestige"]

    schemes = ["flat", "placement", "prestige", "combined"]
    weight_cols = {s: f"w_{s}" for s in schemes}

    # Total weight per scheme = sum of weights over all decks (not cards)
    # Each deck contributes its weight once, regardless of how many cards it has.
    # So we deduplicate to one row per deck first.
    deck_weights = legal.drop_duplicates(subset=["deck_id"])[
        ["deck_id"] + list(weight_cols.values())
    ]
    total_weights = {s: deck_weights[weight_cols[s]].sum() for s in schemes}
    print(f"  Total deck weights: { {s: f'{v:.0f}' for s, v in total_weights.items()} }")

    # Warn if prestige or combined are all zeros (all events are 0-star)
    for s in ("prestige", "combined"):
        if total_weights[s] == 0:
            print(f"  WARNING: total weight for '{s}' scheme is 0 — all events have star_count=0. "
                  f"This scheme will produce all-NaN prevalence.")

    metrics = {}

    for zone in ("mainboard", "sideboard"):
        zone_df = legal[legal["zone"] == zone].copy()

        # weighted_copies(card, scheme) = sum over decks containing card of weight * quantity
        for s in schemes:
            zone_df[f"wc_{s}"] = zone_df[weight_cols[s]] * zone_df["quantity"]

        card_agg = zone_df.groupby("card_name").agg(
            deck_count=("deck_id", "nunique"),
            total_copies=("quantity", "sum"),
            **{f"wc_{s}": (f"wc_{s}", "sum") for s in schemes},
        ).reset_index()

        for s in schemes:
            tw = total_weights[s]
            card_agg[f"prevalence_{s}"] = (
                card_agg[f"wc_{s}"] / tw if tw > 0 else float("nan")
            )

        for _, row in card_agg.iterrows():
            name = row["card_name"]
            if name not in metrics:
                metrics[name] = {}
            metrics[name][zone] = {
                "deck_count":   int(row["deck_count"]),
                "total_copies": int(row["total_copies"]),
                **{f"prevalence_{s}": round(float(row[f"prevalence_{s}"]), 6)
                   for s in schemes},
            }

        print(f"  {zone}: {len(card_agg):,} unique cards with metrics")

    return metrics


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build MTG Legacy dataset from raw cache")
    parser.add_argument("--skip-csv", action="store_true",
                        help="Skip writing decks.csv (faster if only metrics needed)")
    args = parser.parse_args()

    print("\n[1/4] Loading raw data")
    events     = load_events()
    banned     = load_banlist()
    is_legal   = build_legality_fn(banned)
    print(f"  Banlist: {len(banned)} currently banned cards")

    print("\n[2/4] Assembling flat table")
    df = build_flat_table(events, is_legal)

    if not args.skip_csv:
        print("\n[3/4] Writing decks.csv")
        df.to_csv(DECKS_CSV_PATH, index=False)
        print(f"  Saved → {DECKS_CSV_PATH}")
    else:
        print("\n[3/4] Skipping decks.csv (--skip-csv)")

    print("\n[4/4] Computing card metrics")
    metrics = compute_metrics(df)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"  Saved {len(metrics):,} cards → {METRICS_PATH}")

    print("\nDone.")


if __name__ == "__main__":
    main()
