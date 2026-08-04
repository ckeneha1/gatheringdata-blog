"""
build_exclusions.py — the primer-silence exclusion dataset (brief §2.4, Phase 1.3).

Every card that (a) existed at primer-writing time, (b) is functionally
proximate to a card the primer plays, and (c) goes unmentioned, is an implicit
"below threshold given pool + field" observation. LLM extraction cannot capture
silence — this script builds the negative set by JOINING primer card lists
against the function-similarity index (function_index.py / Post 2 features),
filtered to cards first printed before the primer date.

Inputs (in data/ unless noted; ✗ = gitignored, owner's machine only):
    primers.json          ✓ archetype → {url, source, fetched_at, char_count}
    primer_dates.json     ✓ sidecar: archetype → primer WRITING date (manual fill;
                            run `init-dates` to generate the template). primers.json
                            carries only fetched_at (scrape time), not writing time.
    extractions.json      ✗ slug → {archetype, key_cards: [{card_name, ...}]}
                            (extract.py output) — default source of "cards the
                            primer's deck plays". NOTE: key_cards are the cards the
                            primer singles out, not the full decklist; full-decklist
                            cards omitted from key_cards still route to
                            mentioned_exclusions because forum primers embed their
                            decklist in the scraped text.
    decklists.json        ✓ optional override: archetype → [card names]. When an
                            entry exists it replaces extractions key_cards as the
                            played-cards seed set for that archetype.
    raw/<slug>.txt        ✗ raw primer text (fetch_primers.py) — mention scanning.
    field_snapshots.csv   ✓ optional: build_field_snapshots.py output (field stamp).
    ../mtg-legacy-tournament/data/decks.csv
                          ✗ optional: tournament panel — slot contestedness.
    Scryfall bulk cache   ✗ see function_index.py.

Outputs (data/):
    exclusions.csv            silent exclusions — one row per
                              (excluded_card, comparison_card, primer):
        excluded_card         the functionally-proximate card the primer does
                              NOT play and does NOT mention
        comparison_card       the played card whose neighborhood produced it
        primer_id             slug (matches extract.py custom_id)
        archetype             primer archetype label
        primer_date           writing date (ISO) or empty if undated
        pool_snapshot_date    pool conditioning stamp: primer_date, or fetched_at
                              date for undated primers (upper bound; flagged)
        field_snapshot_date   FK into field_snapshots.csv (latest snapshot ≤
                              pool date); the full composition is the joined rows
        field_top_archetypes  convenience: top-5 shares "Name:0.12|..."
        similarity            cosine of Post 2 feature vectors
        comparison_cmc / excluded_cmc / excluded_released_at
        slot_contestedness    distinct neighborhood cards seen in the panel
                              before the pool date (empty if panel absent)
        confidence_weight     §2.4 composite — see confidence_weight()
        reason_flags          semicolon-joined caveats (see FLAG_* constants)
    mentioned_exclusions.csv  neighbors NOT in the deck but mentioned in the
                              primer text — NOT silent exclusions; routed here
                              with surrounding sentence for later LLM
                              classification (dismissed? considered? meta call?).
                              One row per (primer, excluded_card), keyed to the
                              highest-similarity comparison card.

Confidence weights (§2.4): geometric mean of the available components —
    dated:      1.0 if primer_date known, else UNDATED_CONFIDENCE (the
                conditioning set is fuzzier — weighted down, not dropped)
    contested:  max(0.1, min(1.0, distinct_occupants / CONTESTEDNESS_SATURATION));
                omitted (not zeroed) when the tournament panel is absent
The "omission addressed in text" §2.4 component is a ROUTER, not a weight:
mentioned omissions leave the silent set entirely.

Usage:
    uv run python build_exclusions.py init-dates   # write primer_dates.json template
    uv run python build_exclusions.py build        # build the exclusion dataset
    uv run python build_exclusions.py build --min-cosine 0.6 --cmc-band 1
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from function_index import (
    DEFAULT_CMC_BAND,
    DEFAULT_MIN_COSINE,
    FunctionIndex,
    SchemaError,
    find_oracle_cards_file,
)

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
PRIMERS_JSON = DATA_DIR / "primers.json"
PRIMER_DATES_JSON = DATA_DIR / "primer_dates.json"
EXTRACTIONS_JSON = DATA_DIR / "extractions.json"
DECKLISTS_JSON = DATA_DIR / "decklists.json"
RAW_DIR = DATA_DIR / "raw"
FIELD_SNAPSHOTS_CSV = DATA_DIR / "field_snapshots.csv"
PANEL_DECKS_CSV = Path(__file__).parent.parent / "mtg-legacy-tournament" / "data" / "decks.csv"

EXCLUSIONS_CSV = DATA_DIR / "exclusions.csv"
MENTIONED_CSV = DATA_DIR / "mentioned_exclusions.csv"

# ── tuning constants ───────────────────────────────────────────────────────────
UNDATED_CONFIDENCE = 0.4         # dated component when primer_date is unknown
CONTESTEDNESS_SATURATION = 5     # distinct occupants at which the slot counts as fully contested
CONTESTEDNESS_FLOOR = 0.1        # never-zero: uncontested ≠ worthless observation
MENTION_CONTEXT_CHARS = 300      # max captured context around a mention

# ── reason flags ───────────────────────────────────────────────────────────────
FLAG_UNDATED = "undated_primer"                               # pool date = fetched_at upper bound
FLAG_REPRINT_DATE = "release_date_from_oracle_printing"       # released_at may be a reprint date
FLAG_NO_PANEL = "no_panel_data"                               # contestedness component unavailable
FLAG_NO_FIELD = "no_field_snapshot"                           # field stamp unavailable


def slug(name: str) -> str:
    """Archetype → primer_id. Must match fetch_primers.py / extract.py."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Primer dates sidecar
# ---------------------------------------------------------------------------

DATES_FORMAT_DOC = {
    "description": (
        "Manual primer writing/last-updated dates. primers.json only records "
        "fetched_at (when WE scraped the page), which is NOT the conditioning "
        "date for §2.4 — fill primer_date from the source page (first-post date "
        "of the forum thread, article byline, or last-edited stamp)."
    ),
    "fields": {
        "primer_date": "ISO yyyy-mm-dd, or null if genuinely undatable. Undated "
                       "primers are NOT dropped: their pool snapshot falls back to "
                       "the fetched_at date (an upper bound) and their exclusion "
                       "rows carry the 'undated_primer' flag and a reduced "
                       "confidence weight.",
        "date_basis": "Where the date came from, e.g. 'thread first post', "
                      "'article byline', 'last edited stamp'. null until filled.",
        "notes": "Free text (e.g. 'thread spans 2012-2019; dated to last "
                 "substantive primer edit').",
        "url": "Copied from primers.json for fill-in convenience; not read back.",
    },
}


def write_primer_dates_template(primers_meta: dict, path: Path = PRIMER_DATES_JSON) -> int:
    """
    Create/extend the primer_dates.json sidecar: one null-dated entry per
    archetype that has a fetched primer. Existing entries are preserved.
    Returns the number of entries added.
    """
    existing: dict = {}
    if path.exists():
        existing = json.loads(path.read_text())
    out = {"_format": DATES_FORMAT_DOC}
    out.update({k: v for k, v in existing.items() if not k.startswith("_")})
    added = 0
    for archetype, meta in primers_meta.items():
        if not meta.get("url"):
            continue  # known no-primer gaps (see patch_primers.py)
        if archetype not in out:
            out[archetype] = {
                "primer_date": None,
                "date_basis": None,
                "notes": "",
                "url": meta["url"],
            }
            added += 1
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    return added


def load_primer_dates(path: Path = PRIMER_DATES_JSON) -> dict[str, str]:
    """archetype → ISO primer_date, only for filled entries. Validates dates."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    dates: dict[str, str] = {}
    for archetype, entry in data.items():
        if archetype.startswith("_"):
            continue
        if not isinstance(entry, dict):
            raise SchemaError(
                f"{path}: entry for {archetype!r} must be an object "
                "{primer_date, date_basis, notes, url} — run "
                "`uv run python build_exclusions.py init-dates` to see the template format."
            )
        raw = entry.get("primer_date")
        if raw is None:
            continue
        try:
            dates[archetype] = date.fromisoformat(raw).isoformat()
        except (TypeError, ValueError) as e:
            raise SchemaError(
                f"{path}: bad primer_date for {archetype!r}: {raw!r} "
                "(expected ISO yyyy-mm-dd or null)"
            ) from e
    return dates


# ---------------------------------------------------------------------------
# Played-cards seed sets
# ---------------------------------------------------------------------------

def load_seed_cards(
    extractions_path: Path = EXTRACTIONS_JSON,
    decklists_path: Path = DECKLISTS_JSON,
) -> dict[str, list[str]]:
    """
    archetype-slug → list of played card names.
    decklists.json (full decklists, optional, keyed by archetype name) overrides
    extractions.json key_cards (keyed by slug) per archetype.
    """
    seeds: dict[str, list[str]] = {}

    if not extractions_path.exists():
        raise SchemaError(
            f"Extractions not found: {extractions_path}\n"
            "This file is gitignored and lives on the owner's machine. Produce it with:\n"
            "  cd analysis/mtg-primers && uv run python extract.py run\n"
            "(or provide full decklists in data/decklists.json: {archetype: [card, ...]})"
        )
    extractions = json.loads(extractions_path.read_text())
    for primer_id, extraction in extractions.items():
        if not isinstance(extraction, dict) or "key_cards" not in extraction:
            raise SchemaError(
                f"{extractions_path}: entry {primer_id!r} lacks 'key_cards' — expected "
                "extract.py output: {slug: {archetype, key_cards: [{card_name, ...}], ...}}"
            )
        names = [kc.get("card_name", "").strip() for kc in extraction["key_cards"]]
        seeds[primer_id] = [n for n in names if n]

    if decklists_path.exists():
        decklists = json.loads(decklists_path.read_text())
        for archetype, cards in decklists.items():
            if archetype.startswith("_"):
                continue
            if not isinstance(cards, list):
                raise SchemaError(
                    f"{decklists_path}: entry {archetype!r} must be a list of card names"
                )
            seeds[slug(archetype)] = [str(c).strip() for c in cards if str(c).strip()]

    return seeds


# ---------------------------------------------------------------------------
# Mention scanning
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _name_pattern(card_name: str) -> re.Pattern:
    # Letter-boundary lookarounds instead of \b: card names can end in
    # punctuation ("Oops, All Spells!"), where \b misbehaves.
    return re.compile(
        rf"(?<![a-z]){re.escape(card_name.lower())}(?![a-z])"
    )


def scan_mention(normalized_text: str, card_name: str) -> str | None:
    """
    If `card_name` (or the front face of a split/DFC name) appears in the
    primer text, return the surrounding sentence (≤ MENTION_CONTEXT_CHARS);
    else None.
    """
    names = [card_name]
    if " // " in card_name:
        names.append(card_name.split(" // ")[0])
    for name in names:
        m = _name_pattern(name).search(normalized_text)
        if not m:
            continue
        # Expand to sentence-ish boundaries.
        start = max(m.start() - MENTION_CONTEXT_CHARS // 2, 0)
        end = min(m.end() + MENTION_CONTEXT_CHARS // 2, len(normalized_text))
        chunk = normalized_text[start:end]
        rel = m.start() - start
        left = max((chunk.rfind(p, 0, rel) for p in (". ", "! ", "? ")), default=-1)
        right_candidates = [chunk.find(p, rel) for p in (". ", "! ", "? ")]
        right_candidates = [c for c in right_candidates if c != -1]
        right = min(right_candidates) + 1 if right_candidates else len(chunk)
        return chunk[left + 2 if left != -1 else 0 : right].strip()
    return None


# ---------------------------------------------------------------------------
# Panel-backed slot contestedness
# ---------------------------------------------------------------------------

def load_panel_first_seen(path: Path = PANEL_DECKS_CSV) -> dict[str, str] | None:
    """
    card_name (lowercased) → earliest event_date (ISO) in the tournament panel.
    Returns None (component disabled, NOT an error) when the panel is absent —
    remote sessions can't regenerate it (brief §5).
    """
    if not path.exists():
        return None
    first_seen: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = {"card_name", "event_date"} - set(reader.fieldnames or [])
        if missing:
            raise SchemaError(
                f"{path} is missing expected columns: {sorted(missing)} — expected the "
                "decks.csv schema from analysis/mtg-legacy-tournament/build_dataset.py"
            )
        for row in reader:
            d = (row["event_date"] or "").strip()
            if not d:
                continue
            name = row["card_name"].lower()
            if name not in first_seen or d < first_seen[name]:
                first_seen[name] = d
    return first_seen


def slot_contestedness(
    neighborhood_names: list[str],
    seed_name: str,
    before_date: str,
    panel_first_seen: dict[str, str] | None,
) -> int | None:
    """
    §2.4 "format optimization depth": how many distinct cards historically
    occupied this function-neighborhood (seed + neighbors) in the tournament
    panel before the pool date. None when the panel is unavailable.
    """
    if panel_first_seen is None:
        return None
    count = 0
    for name in [seed_name, *neighborhood_names]:
        seen = panel_first_seen.get(name.lower())
        if seen is not None and seen < before_date:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Field snapshots lookup
# ---------------------------------------------------------------------------

class FieldSnapshots:
    """Lookup: date → (snapshot_date, {archetype: share}) from field_snapshots.csv."""

    def __init__(self, snapshots: dict[str, dict[str, float]]):
        self._snapshots = snapshots
        self._dates = sorted(snapshots)

    @classmethod
    def from_csv(cls, path: Path = FIELD_SNAPSHOTS_CSV) -> "FieldSnapshots | None":
        """None (stamp disabled with a flag, NOT an error) when absent."""
        if not path.exists():
            return None
        snapshots: dict[str, dict[str, float]] = {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = {"snapshot_date", "archetype", "share"} - set(reader.fieldnames or [])
            if missing:
                raise SchemaError(
                    f"{path} is missing expected columns: {sorted(missing)} — regenerate with:\n"
                    "  cd analysis/mtg-primers && uv run python build_field_snapshots.py"
                )
            for row in reader:
                snapshots.setdefault(row["snapshot_date"], {})[row["archetype"]] = float(row["share"])
        return cls(snapshots)

    def lookup(self, iso_date: str) -> tuple[str, dict[str, float]] | None:
        """Latest snapshot dated ≤ iso_date (snapshots only summarize pre-snapshot
        data, so this never leaks post-primer field state)."""
        import bisect
        i = bisect.bisect_right(self._dates, iso_date)
        if i == 0:
            return None
        d = self._dates[i - 1]
        return d, self._snapshots[d]


def format_top_shares(shares: dict[str, float], n: int = 5) -> str:
    top = sorted(shares.items(), key=lambda kv: -kv[1])[:n]
    return "|".join(f"{a}:{s:.3f}" for a, s in top)


# ---------------------------------------------------------------------------
# Confidence weights
# ---------------------------------------------------------------------------

def confidence_weight(dated: bool, contestedness: int | None) -> float:
    """
    §2.4 composite, geometric mean of the AVAILABLE components:
      dated:      1.0 if the primer's writing date is known, else UNDATED_CONFIDENCE
      contested:  max(FLOOR, min(1, n / SATURATION)) — a slot many distinct cards
                  have historically occupied was actively optimized, so silence
                  there is a stronger negative label. Omitted when the panel is
                  unavailable (nullable, per the brief), not treated as zero.
    """
    components = [1.0 if dated else UNDATED_CONFIDENCE]
    if contestedness is not None:
        components.append(
            max(CONTESTEDNESS_FLOOR, min(1.0, contestedness / CONTESTEDNESS_SATURATION))
        )
    prod = 1.0
    for c in components:
        prod *= c
    return round(prod ** (1.0 / len(components)), 4)


# ---------------------------------------------------------------------------
# Core join (pure-ish: all data passed in — unit-testable without files)
# ---------------------------------------------------------------------------

@dataclass
class PrimerRecord:
    primer_id: str
    archetype: str
    primer_date: str | None     # ISO writing date, or None if undated
    fetched_date: str           # ISO date part of primers.json fetched_at
    played_cards: list[str]
    text: str                   # raw primer text


@dataclass
class ExclusionResult:
    silent: list[dict] = field(default_factory=list)
    mentioned: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_exclusions_for_primer(
    primer: PrimerRecord,
    index: FunctionIndex,
    panel_first_seen: dict[str, str] | None = None,
    field_snapshots: FieldSnapshots | None = None,
    min_cosine: float = DEFAULT_MIN_COSINE,
    cmc_band: float = DEFAULT_CMC_BAND,
) -> ExclusionResult:
    """The §2.4 join for one primer. See module docstring for row semantics."""
    res = ExclusionResult()

    dated = primer.primer_date is not None
    pool_date = primer.primer_date or primer.fetched_date
    base_flags: list[str] = [] if dated else [FLAG_UNDATED]

    field_stamp_date, field_top = "", ""
    field_flags: list[str] = []
    if field_snapshots is not None:
        hit = field_snapshots.lookup(pool_date)
        if hit is not None:
            field_stamp_date, shares = hit[0], hit[1]
            field_top = format_top_shares(shares)
        else:
            field_flags.append(FLAG_NO_FIELD)
    else:
        field_flags.append(FLAG_NO_FIELD)

    played_lower = {c.lower() for c in primer.played_cards}
    # Played split/DFC cards also count as "in the decklist" under their front face.
    for c in primer.played_cards:
        if " // " in c:
            played_lower.add(c.split(" // ")[0].lower())

    text_norm = normalize_text(primer.text)
    seen_pairs: set[tuple[str, str]] = set()
    best_mention: dict[str, dict] = {}   # excluded_card → highest-similarity mention row

    for played in primer.played_cards:
        try:
            neighbors = index.neighborhood(
                played, min_cosine=min_cosine, cmc_band=cmc_band, before_date=pool_date
            )
        except KeyError:
            res.warnings.append(
                f"{primer.primer_id}: played card not in catalog, skipped: {played!r}"
            )
            continue
        seed_entry = index.lookup(played)
        neighbor_names = [n.name for n in neighbors]
        contested = slot_contestedness(neighbor_names, played, pool_date, panel_first_seen)

        for n in neighbors:
            if n.name.lower() in played_lower:
                continue  # in the decklist — an inclusion, not an exclusion
            pair = (n.name, played)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            mention = scan_mention(text_norm, n.name)
            if mention is not None:
                # Addressed in text → NOT a silent exclusion. Route for LLM
                # classification; keep the strongest comparison per card.
                prev = best_mention.get(n.name)
                if prev is None or n.similarity > prev["similarity"]:
                    best_mention[n.name] = {
                        "excluded_card": n.name,
                        "comparison_card": played,
                        "primer_id": primer.primer_id,
                        "archetype": primer.archetype,
                        "primer_date": primer.primer_date or "",
                        "pool_snapshot_date": pool_date,
                        "similarity": n.similarity,
                        "mention_context": mention,
                    }
                continue

            flags = list(base_flags) + list(field_flags)
            if n.release_basis != "first_printing":
                flags.append(FLAG_REPRINT_DATE)
            if contested is None:
                flags.append(FLAG_NO_PANEL)

            res.silent.append({
                "excluded_card": n.name,
                "comparison_card": played,
                "primer_id": primer.primer_id,
                "archetype": primer.archetype,
                "primer_date": primer.primer_date or "",
                "pool_snapshot_date": pool_date,
                "field_snapshot_date": field_stamp_date,
                "field_top_archetypes": field_top,
                "similarity": n.similarity,
                "comparison_cmc": seed_entry.cmc if seed_entry else "",
                "excluded_cmc": n.cmc,
                "excluded_released_at": n.released_at or "",
                "slot_contestedness": contested if contested is not None else "",
                "confidence_weight": confidence_weight(dated, contested),
                "reason_flags": ";".join(flags),
            })

    res.mentioned.extend(best_mention.values())
    return res


# ---------------------------------------------------------------------------
# I/O orchestration
# ---------------------------------------------------------------------------

def load_primer_records() -> list[PrimerRecord]:
    if not PRIMERS_JSON.exists():
        raise SchemaError(
            f"Primer index not found: {PRIMERS_JSON} — run "
            "`uv run python fetch_primers.py` first."
        )
    primers_meta = json.loads(PRIMERS_JSON.read_text())
    dates = load_primer_dates()
    seeds = load_seed_cards()

    if not dates:
        print(
            "  WARNING: no primer dates filled in data/primer_dates.json — ALL primers "
            "will be treated as undated (pool date = fetched_at upper bound, reduced "
            "confidence). Run `init-dates` and fill dates from the source pages."
        )

    records: list[PrimerRecord] = []
    for archetype, meta in primers_meta.items():
        if not meta.get("url"):
            continue  # known no-primer gap
        primer_id = slug(archetype)
        raw_path = RAW_DIR / f"{primer_id}.txt"
        if not raw_path.exists():
            print(f"  WARNING: missing raw text {raw_path.name} — primer skipped "
                  "(mention scanning is required for silence labels)")
            continue
        played = seeds.get(primer_id)
        if not played:
            print(f"  WARNING: no played-cards seed set for {archetype!r} "
                  f"(no extractions entry or decklists.json entry) — primer skipped")
            continue
        fetched_at = meta.get("fetched_at") or ""
        if len(fetched_at) < 10:
            print(f"  WARNING: {archetype!r} has no fetched_at in primers.json — primer skipped")
            continue
        records.append(PrimerRecord(
            primer_id=primer_id,
            archetype=archetype,
            primer_date=dates.get(archetype),
            fetched_date=fetched_at[:10],
            played_cards=played,
            text=raw_path.read_text(encoding="utf-8"),
        ))
    return records


SILENT_COLUMNS = [
    "excluded_card", "comparison_card", "primer_id", "archetype", "primer_date",
    "pool_snapshot_date", "field_snapshot_date", "field_top_archetypes",
    "similarity", "comparison_cmc", "excluded_cmc", "excluded_released_at",
    "slot_contestedness", "confidence_weight", "reason_flags",
]
MENTIONED_COLUMNS = [
    "excluded_card", "comparison_card", "primer_id", "archetype", "primer_date",
    "pool_snapshot_date", "similarity", "mention_context",
]


def cmd_build(min_cosine: float, cmc_band: float) -> None:
    print("[1/5] Loading primer records")
    records = load_primer_records()
    n_dated = sum(1 for r in records if r.primer_date)
    print(f"  {len(records)} primers ({n_dated} dated, {len(records) - n_dated} undated)")

    print("[2/5] Building function-similarity index")
    index = FunctionIndex.from_scryfall_file(find_oracle_cards_file())

    print("[3/5] Loading tournament panel (slot contestedness)")
    panel = load_panel_first_seen()
    if panel is None:
        print(f"  Panel not found at {PANEL_DECKS_CSV} — contestedness component "
              "disabled (nullable per brief; rows get flag 'no_panel_data')")
    else:
        print(f"  Panel first-seen dates for {len(panel):,} cards")

    print("[4/5] Loading field snapshots")
    snapshots = FieldSnapshots.from_csv()
    if snapshots is None:
        print(f"  {FIELD_SNAPSHOTS_CSV.name} not found — field stamp disabled "
              "(run `uv run python build_field_snapshots.py`; rows get flag "
              "'no_field_snapshot')")

    print("[5/5] Joining primer silences")
    all_silent: list[dict] = []
    all_mentioned: list[dict] = []
    for rec in records:
        res = build_exclusions_for_primer(
            rec, index, panel, snapshots, min_cosine=min_cosine, cmc_band=cmc_band
        )
        for w in res.warnings:
            print(f"  WARNING: {w}")
        all_silent.extend(res.silent)
        all_mentioned.extend(res.mentioned)
        print(f"  {rec.primer_id}: {len(res.silent)} silent, {len(res.mentioned)} mentioned")

    for path, columns, rows in [
        (EXCLUSIONS_CSV, SILENT_COLUMNS, all_silent),
        (MENTIONED_CSV, MENTIONED_COLUMNS, all_mentioned),
    ]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved {len(rows):,} rows → {path}")


def cmd_init_dates() -> None:
    if not PRIMERS_JSON.exists():
        raise SchemaError(f"Primer index not found: {PRIMERS_JSON}")
    primers_meta = json.loads(PRIMERS_JSON.read_text())
    added = write_primer_dates_template(primers_meta)
    total = sum(1 for k in json.loads(PRIMER_DATES_JSON.read_text()) if not k.startswith("_"))
    print(f"primer_dates.json: {added} entries added ({total} total) → {PRIMER_DATES_JSON}")
    print("Fill primer_date per entry from the source page (see the _format key).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("init-dates", help="write/extend the primer_dates.json template")
    p_build = sub.add_parser("build", help="build exclusions.csv + mentioned_exclusions.csv")
    p_build.add_argument("--min-cosine", type=float, default=DEFAULT_MIN_COSINE)
    p_build.add_argument("--cmc-band", type=float, default=DEFAULT_CMC_BAND)
    args = parser.parse_args()

    try:
        if args.cmd == "init-dates":
            cmd_init_dates()
        elif args.cmd == "build":
            cmd_build(args.min_cosine, args.cmc_band)
        else:
            parser.print_help()
    except SchemaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
