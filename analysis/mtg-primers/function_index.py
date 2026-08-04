"""
function_index.py — function-at-cost similarity index over the Scryfall catalog.

Builds the Post 2 ability-feature vector for every card in the Scryfall
oracle-cards bulk file (via the shared analysis/shared/ability_features.py
module) and answers the query at the heart of the exclusion dataset
(brief §2.4): given a card a primer plays, which other cards are
"the same function at the same-or-adjacent cost"?

Similarity metric (simple and inspectable, per the brief):
  - Feature space: binary union of 18 regex ability categories + Scryfall
    keywords (see shared/ability_features.card_feature_set).
  - Similarity:    cosine on the binary vector = |A∩B| / sqrt(|A|·|B|).
  - Cost filter:   |CMC(neighbor) − CMC(seed)| ≤ cmc_band (default 1).
  - Pool filter:   neighbor's first release date < before_date, when given.

Data interfaces (read-only; nothing here hits the network):
  - Oracle cards: the local Scryfall bulk cache shared with Post 1/2 —
      analysis/mtg-distributions/.cache/oracle_cards--<timestamp>.json
      analysis/mtg-card-power/.cache/oracle_cards--<timestamp>.json
    (produced by `uv run python analyze.py build` in analysis/mtg-card-power).
  - First-print dates: all_cards--<timestamp>.json in the same cache dirs,
    streamed with ijson and memoized to .cache/first_release--<stem>.json.
    The oracle_cards file's `released_at` is the release date of ONE chosen
    printing (often a reprint), so it is only a fallback; when used, the
    affected observation is flagged `release_date_from_oracle_printing`.

Usage:
    from function_index import FunctionIndex, find_oracle_cards_file
    index = FunctionIndex.from_scryfall_file(find_oracle_cards_file())
    for n in index.neighborhood("Brainstorm", before_date="2019-06-01"):
        print(n.name, n.similarity, n.cmc, n.released_at)
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

_ANALYSIS_DIR = Path(__file__).resolve().parent.parent
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

from shared.ability_features import card_feature_set, cosine_similarity  # noqa: E402

# ── paths ──────────────────────────────────────────────────────────────────────
LOCAL_CACHE_DIR = Path(__file__).parent / ".cache"

# Same search order as analysis/mtg-card-power/analyze.py: the Post 1 cache
# first, then mtg-card-power's local cache, then our own.
SCRYFALL_CACHE_DIRS = [
    _ANALYSIS_DIR / "mtg-distributions" / ".cache",
    _ANALYSIS_DIR / "mtg-card-power" / ".cache",
    LOCAL_CACHE_DIR,
]

# Layouts excluded from the catalog (same set as analyze.py)
EXCLUDED_LAYOUTS = {"token", "emblem", "art_series", "reversible_card"}

DEFAULT_MIN_COSINE = 0.5
DEFAULT_CMC_BAND = 1


class SchemaError(RuntimeError):
    """Raised when an expected data file is missing or malformed."""


def find_oracle_cards_file() -> Path:
    """Locate the newest cached Scryfall oracle_cards bulk file."""
    candidates: list[Path] = []
    for d in SCRYFALL_CACHE_DIRS:
        candidates.extend(d.glob("oracle_cards--*.json"))
    if not candidates:
        searched = "\n  ".join(str(d) for d in SCRYFALL_CACHE_DIRS)
        raise SchemaError(
            "No Scryfall oracle_cards bulk file found. Searched:\n"
            f"  {searched}\n"
            "Expected a file named oracle_cards--<timestamp>.json. Produce one with:\n"
            "  cd analysis/mtg-card-power && uv run python analyze.py build"
        )
    # Filename embeds the Scryfall updated_at timestamp — lexicographic max = newest.
    return max(candidates, key=lambda p: p.name)


def find_all_cards_file() -> Path | None:
    """Locate the newest cached Scryfall all_cards bulk file, if any."""
    candidates: list[Path] = []
    for d in SCRYFALL_CACHE_DIRS:
        candidates.extend(d.glob("all_cards--*.json"))
    return max(candidates, key=lambda p: p.name) if candidates else None


def _front_face_text_and_mana(card: dict) -> tuple[str, str]:
    """Oracle text and mana cost, using the front face for DFCs (as analyze.py)."""
    mana_cost = card.get("mana_cost", "") or ""
    oracle_text = card.get("oracle_text", "") or ""
    faces = card.get("card_faces")
    if faces:
        front = faces[0]
        if not mana_cost:
            mana_cost = front.get("mana_cost", "") or ""
        if not oracle_text:
            oracle_text = front.get("oracle_text", "") or ""
    return oracle_text, mana_cost


def compute_first_release_dates(all_cards_path: Path) -> dict[str, str]:
    """
    oracle_id → earliest released_at (ISO date) across ALL printings.
    Streams the (large) all_cards bulk file with ijson; memoized to
    .cache/first_release--<stem>.json so this runs once per bulk update.
    """
    LOCAL_CACHE_DIR.mkdir(exist_ok=True)
    memo = LOCAL_CACHE_DIR / f"first_release--{all_cards_path.stem}.json"
    if memo.exists():
        return json.loads(memo.read_text())

    import ijson  # local import: only needed on the slow path

    print(f"  Computing first-release dates from {all_cards_path.name} (streaming, one-time)...")
    first: dict[str, str] = {}
    with open(all_cards_path, "rb") as f:
        for card in ijson.items(f, "item"):
            oid, released = card.get("oracle_id"), card.get("released_at")
            if oid and released and (oid not in first or released < first[oid]):
                first[oid] = released
    memo.write_text(json.dumps(first))
    print(f"  Saved first-release dates for {len(first):,} oracle ids → {memo.name}")
    return first


@dataclass(frozen=True)
class CardEntry:
    name: str
    oracle_id: str
    cmc: float
    type_line: str
    is_land: bool
    features: frozenset[str]
    released_at: str | None       # first release date (ISO), or oracle-printing fallback
    release_basis: str            # "first_printing" | "oracle_printing" | "unknown"


@dataclass(frozen=True)
class Neighbor:
    name: str
    similarity: float
    cmc: float
    released_at: str | None
    release_basis: str


class FunctionIndex:
    """Feature-vector index over the card catalog with neighborhood queries."""

    def __init__(self, cards: list[CardEntry]):
        self.cards = cards
        # name (lowercased) → entry; also register the front face of split/DFC
        # names ("Fire // Ice" → "fire") since decklists often use face names.
        self.by_name: dict[str, CardEntry] = {}
        for c in cards:
            self.by_name.setdefault(c.name.lower(), c)
            if " // " in c.name:
                self.by_name.setdefault(c.name.split(" // ")[0].lower(), c)
        # Inverted index: feature → list of card positions sharing it.
        self._postings: dict[str, list[int]] = {}
        for i, c in enumerate(cards):
            for feat in c.features:
                self._postings.setdefault(feat, []).append(i)

    # ── constructors ─────────────────────────────────────────────────────────
    @classmethod
    def from_card_dicts(
        cls,
        raw_cards: list[dict],
        first_release: dict[str, str] | None = None,
        release_basis_fallback: str = "oracle_printing",
    ) -> "FunctionIndex":
        """
        Build from Scryfall-shaped card dicts. Required keys per card:
        name, oracle_id, type_line, cmc (or mana_value), oracle_text/card_faces,
        keywords, released_at, layout.
        `first_release` maps oracle_id → first-printing date; cards missing
        from it fall back to their own released_at (flagged).
        """
        if not isinstance(raw_cards, list) or (raw_cards and not isinstance(raw_cards[0], dict)):
            raise SchemaError(
                "Oracle cards data must be a JSON array of card objects "
                "(Scryfall oracle_cards bulk format)."
            )
        first_release = first_release or {}
        entries: list[CardEntry] = []
        for card in raw_cards:
            if card.get("layout") in EXCLUDED_LAYOUTS:
                continue
            name = card.get("name")
            if not name:
                continue
            type_line = card.get("type_line", "") or ""
            is_land = "Land" in type_line and "Artifact" not in type_line
            oracle_text, _ = _front_face_text_and_mana(card)
            keywords = card.get("keywords") or []
            cmc = float(card.get("cmc") or card.get("mana_value") or 0.0)
            oid = card.get("oracle_id", "") or ""

            if oid in first_release:
                released, basis = first_release[oid], "first_printing"
            elif card.get("released_at"):
                released, basis = card["released_at"], release_basis_fallback
            else:
                released, basis = None, "unknown"

            entries.append(CardEntry(
                name=name,
                oracle_id=oid,
                cmc=cmc,
                type_line=type_line,
                is_land=is_land,
                features=card_feature_set(oracle_text, keywords, is_land),
                released_at=released,
                release_basis=basis,
            ))
        return cls(entries)

    @classmethod
    def from_scryfall_file(cls, oracle_path: Path) -> "FunctionIndex":
        """Build from a cached oracle_cards bulk file (+ all_cards if available)."""
        print(f"Loading catalog from {oracle_path.name}...")
        try:
            raw_cards = json.loads(oracle_path.read_text())
        except json.JSONDecodeError as e:
            raise SchemaError(f"{oracle_path} is not valid JSON: {e}") from e

        all_cards_path = find_all_cards_file()
        if all_cards_path is not None:
            first_release = compute_first_release_dates(all_cards_path)
        else:
            print(
                "  NOTE: no all_cards--*.json bulk file found in any cache dir — "
                "falling back to oracle_cards released_at (may be a reprint date; "
                "affected rows get flag 'release_date_from_oracle_printing')."
            )
            first_release = {}

        index = cls.from_card_dicts(raw_cards, first_release)
        print(f"  Indexed {len(index.cards):,} cards "
              f"({sum(1 for c in index.cards if c.features):,} with ability features)")
        return index

    # ── queries ──────────────────────────────────────────────────────────────
    def lookup(self, name: str) -> CardEntry | None:
        return self.by_name.get(name.strip().lower())

    def neighborhood(
        self,
        seed_name: str,
        min_cosine: float = DEFAULT_MIN_COSINE,
        cmc_band: float = DEFAULT_CMC_BAND,
        before_date: str | None = None,
        include_lands: bool = False,
    ) -> list[Neighbor]:
        """
        Function-at-cost neighborhood of `seed_name`: cards whose Post 2
        feature vector has cosine ≥ min_cosine with the seed's, at CMC within
        ±cmc_band of the seed, optionally first-released strictly before
        `before_date` (ISO yyyy-mm-dd string — Scryfall dates compare
        lexicographically). The seed itself is never returned.
        Returns neighbors sorted by similarity desc, then name.
        """
        seed = self.lookup(seed_name)
        if seed is None:
            raise KeyError(f"Card not in catalog: {seed_name!r}")
        if not seed.features:
            return []

        # Candidates = cards sharing ≥1 feature with the seed (inverted index).
        candidate_ids: set[int] = set()
        for feat in seed.features:
            candidate_ids.update(self._postings.get(feat, ()))

        out: list[Neighbor] = []
        for i in candidate_ids:
            c = self.cards[i]
            if c.name == seed.name:
                continue
            if c.is_land and not include_lands:
                continue
            if abs(c.cmc - seed.cmc) > cmc_band:
                continue
            if before_date is not None:
                if c.released_at is None or not (c.released_at < before_date):
                    continue
            sim = cosine_similarity(seed.features, c.features)
            if sim >= min_cosine:
                out.append(Neighbor(c.name, round(sim, 4), c.cmc, c.released_at, c.release_basis))
        out.sort(key=lambda n: (-n.similarity, n.name))
        return out
