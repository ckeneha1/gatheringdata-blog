"""
join_features.py — Join tournament card stats with LLM primer value-signal labels.

Reads:
  data/card_stats.csv                           (from build_features.py)
  ../mtg-primers/data/extractions.json          (from extract.py)

Writes:
  data/card_features.csv  — master card feature table:
      card_name, total_decks, top8_rate, top4_rate, top1_rate, avg_placement,
      top8_decks, top4_decks, top1_decks,
      has_primer_label, signal_count, archetype_count, archetypes,
      sig_free_spell, sig_mana_denial, sig_mana_acceleration, sig_cantrip,
      sig_tutor, sig_combo_piece, sig_lock_piece, sig_graveyard,
      sig_resilience, sig_protection, sig_hate_piece, sig_card_advantage,
      sig_tempo, sig_archetype_synergy

Usage:
    uv run python join_features.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

DATA_DIR      = Path(__file__).parent / "data"
EXTRACTIONS   = Path(__file__).parent.parent / "mtg-primers" / "data" / "extractions.json"

VALUE_SIGNALS = [
    "free_spell",
    "mana_denial",
    "mana_acceleration",
    "cantrip",
    "tutor",
    "combo_piece",
    "lock_piece",
    "graveyard",
    "resilience",
    "protection",
    "hate_piece",
    "card_advantage",
    "tempo",
    "archetype_synergy",
]

CARD_STATS_COLS = [
    "card_name", "total_decks",
    "top1_decks", "top2_decks", "top4_decks", "top8_decks",
    "win_rate", "final_rate", "semi_rate", "qf_rate",
    "win_log_or",
]

OUT_COLS = CARD_STATS_COLS + [
    "has_primer_label",
    "signal_count",
    "archetype_count",
    "archetypes",
] + [f"sig_{s}" for s in VALUE_SIGNALS]


def load_extractions(path: Path) -> dict[str, dict]:
    """Returns card_name -> {signals: set[str], archetypes: set[str]}."""
    data = json.loads(path.read_text())
    card_info: dict[str, dict] = defaultdict(lambda: {"signals": set(), "archetypes": set()})
    for arch_key, arch in data.items():
        arch_name = arch["archetype"]
        for card in arch["key_cards"]:
            name = card["card_name"]
            card_info[name]["signals"].update(card["value_signals"])
            card_info[name]["archetypes"].add(arch_name)
    return dict(card_info)


def main():
    print("Loading card stats...")
    stats = list(csv.DictReader(open(DATA_DIR / "card_stats.csv")))
    print(f"  {len(stats):,} cards")

    print("Loading primer extractions...")
    if not EXTRACTIONS.exists():
        print(f"  ERROR: {EXTRACTIONS} not found — run extract.py collect first")
        return
    card_labels = load_extractions(EXTRACTIONS)
    print(f"  {len(card_labels):,} labeled cards from primers")

    # Build output rows
    rows = []
    matched = 0
    for stat in stats:
        name = stat["card_name"]
        label = card_labels.get(name)

        row = {col: stat[col] for col in CARD_STATS_COLS}

        if label:
            matched += 1
            sigs = label["signals"]
            archs = sorted(label["archetypes"])
            row["has_primer_label"] = 1
            row["signal_count"]     = len(sigs)
            row["archetype_count"]  = len(archs)
            row["archetypes"]       = "; ".join(archs)
            for s in VALUE_SIGNALS:
                row[f"sig_{s}"] = 1 if s in sigs else 0
        else:
            row["has_primer_label"] = 0
            row["signal_count"]     = 0
            row["archetype_count"]  = 0
            row["archetypes"]       = ""
            for s in VALUE_SIGNALS:
                row[f"sig_{s}"] = 0

        rows.append(row)

    print(f"\n  {matched:,} / {len(stats):,} cards matched to primer labels")
    print(f"  {len(card_labels) - matched:,} labeled cards not in tournament stats (too rare, sideboard-only, etc.)")

    out = DATA_DIR / "card_features.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nWrote {len(rows):,} rows → {out}")

    # Quick summary: win log-odds ratio by signal
    print("\n=== Win log-odds ratio by signal (labeled cards only) ===")
    sig_lor   = defaultdict(list)
    nosig_lor = []
    for row in rows:
        lor = float(row["win_log_or"]) if row["win_log_or"] else 0
        if int(row["has_primer_label"]):
            for s in VALUE_SIGNALS:
                if row[f"sig_{s}"]:
                    sig_lor[s].append(lor)
        else:
            nosig_lor.append(lor)

    baseline = sum(nosig_lor) / len(nosig_lor) if nosig_lor else 0
    print(f"  Baseline (unlabeled, n={len(nosig_lor)}):  log-OR={baseline:.3f}")
    print()
    for s in sorted(sig_lor, key=lambda s: -sum(sig_lor[s]) / len(sig_lor[s])):
        vals = sig_lor[s]
        avg  = sum(vals) / len(vals)
        print(f"  {s:<25}  n={len(vals):>3}  mean log-OR={avg:+.3f}")


if __name__ == "__main__":
    main()
