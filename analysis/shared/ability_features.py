"""
ability_features.py — the Post 2 ("What Does a Mana Cost Buy You?") card
ability-feature extraction, as a shared, stdlib-only module.

Extracted VERBATIM from analysis/mtg-card-power/analyze.py so that other
analyses (the Legacy exclusion dataset, the conditional value model) can
compute the same feature vector without importing analyze.py's heavy chart
dependencies (matplotlib / pandas / gatheringdata.charts).

Two analysis layers (same as Post 2):
  1. Keyword layer:  Scryfall's `keywords` array — structured, no NLP needed.
  2. Semantic layer: regex patterns against stripped oracle text, 18 named
     categories. Keyword names are stripped from oracle text first so the
     two layers don't double-count.

Per brief §2.4 this feature set FAILED as a quality metric but is serviceable
as a SIMILARITY metric: two cards sharing categories + keywords at similar
CMC define a function-at-cost comparison class ("Brainstorm-like at this
cost"). `card_feature_set` + `cosine_similarity` implement exactly that:
cosine on the binary feature vector, where the feature space is the union of
regex-category tags (prefixed "cat:") and lowercased Scryfall keywords
(prefixed "kw:").

PARITY: analysis/mtg-card-power/analyze.py remains the canonical source for
the published Post 2 pipeline; it has not been refactored to import this
module (its outputs back a published post). tests/test_build_exclusions.py
in analysis/mtg-primers contains an AST-based parity test that fails if the
two copies of PATTERNS drift apart — if you edit one, edit both.
"""

import re

# ---------------------------------------------------------------------------
# Semantic layer: regex classification
# (verbatim copy of _PATTERNS in analysis/mtg-card-power/analyze.py)
# ---------------------------------------------------------------------------

PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    # ── Card advantage ──────────────────────────────────────────────────────────
    # FIX: word-spelled numbers ("draw two cards") weren't matched; only \d+ was.
    ("card_advantage", [
        re.compile(r"draw[s]? (?:a|one|two|three|four|five|six|seven|\d+|X) cards?", re.I),
        re.compile(r"\bscry \d+\b", re.I),
        re.compile(r"\bsurveil \d+\b", re.I),
        re.compile(r"look at the top \d+", re.I),
        re.compile(r"reveal the top \d+", re.I),
        re.compile(r"you may play the top", re.I),
        re.compile(r"exile the top .{0,30} and (?:you may )?(?:play|cast) it", re.I),
        re.compile(r"\bcycling\b", re.I),           # Cycling = discard → draw
        re.compile(r"\bforetell\b", re.I),          # Exile to hand for later
        re.compile(r"\bcascade\b", re.I),           # Free spell off the top
        re.compile(r"\binvestigate\b", re.I),       # Creates Clue → draw
        re.compile(r"\blearn\b", re.I),             # Lesson/draw hybrid
        re.compile(r"\bconnive \d+\b", re.I),       # Draw+discard+counter
    ]),
    # ── Removal ─────────────────────────────────────────────────────────────────
    ("removal", [
        re.compile(r"destroy target", re.I),
        re.compile(r"exile target", re.I),
        re.compile(r"return target .{0,60} to .{0,20} (?:owner.s|its owner.s) hand", re.I),
        re.compile(r"puts? .{0,40} into .{0,20} owner.s graveyard", re.I),
        re.compile(r"gets? -\d+/-\d+ until end of turn", re.I),
        re.compile(r"gets? -X/-X", re.I),
        re.compile(r"destroy all", re.I),
        re.compile(r"exile all", re.I),
        re.compile(r"\bdetain\b", re.I),            # Can't attack/block/activate
    ]),
    # ── Direct damage ───────────────────────────────────────────────────────────
    ("direct_damage", [
        re.compile(r"deals? \d+ damage", re.I),
        re.compile(r"deals? X damage", re.I),
        re.compile(r"deals? .{0,30} damage to (?:any target|target (?:player|opponent|creature|planeswalker|battle))", re.I),
        re.compile(r"\bafflict \d+\b", re.I),       # Life loss when blocked
    ]),
    # ── Tokens ──────────────────────────────────────────────────────────────────
    ("tokens", [
        re.compile(r"creates? .{0,60} token", re.I),
        re.compile(r"puts? .{0,60} token .{0,20} (?:onto|into|on) the battlefield", re.I),
        re.compile(r"\bpopulate\b", re.I),          # Copy a token
        re.compile(r"\bamass \d+\b", re.I),         # Put counters on/create Army token
        re.compile(r"\bliving weapon\b", re.I),     # Creates Germ token, equips it
        re.compile(r"\bfabricate \d+\b", re.I),     # N +1/+1 counters OR N 1/1 tokens
    ]),
    # ── Counters ────────────────────────────────────────────────────────────────
    ("counters", [
        re.compile(r"\bproliferate\b", re.I),
        re.compile(r"puts? .{0,20} \+\d+/\+\d+ counter", re.I),
        re.compile(r"puts? .{0,20} -\d+/-\d+ counter", re.I),
        re.compile(r"puts? .{0,20} counter[s]? .{0,30} on", re.I),
        re.compile(r"removes? .{0,20} counter", re.I),
        re.compile(r"\bmodular \d+\b", re.I),       # Enters with N +1/+1 counters, passes on death
        re.compile(r"\bbolster \d+\b", re.I),       # Put N counters on weakest creature
        re.compile(r"\badapt \d+\b", re.I),         # Put N counters if none present
        re.compile(r"\bevolve\b", re.I),            # Gets counter when bigger creature enters
        re.compile(r"\bgraft \d+\b", re.I),         # Enters with N counters, shares them
        re.compile(r"\bmonstrosity \d+\b", re.I),   # Pay cost → put N counters
        re.compile(r"\brenown \d+\b", re.I),        # Deals combat damage → N counters
        re.compile(r"\boutlast\b", re.I),           # {cost}, {T}: put +1/+1 counter
        re.compile(r"\btraining\b", re.I),          # Gets counter when attacks with bigger
        re.compile(r"\bbackup \d+\b", re.I),        # ETB: put N counters, share abilities
        re.compile(r"\bbloodthirst \d+\b", re.I),   # Enters with N counters if opponent hurt
        re.compile(r"\bunleash\b", re.I),           # Enter with +1/+1 counter, can't block
        re.compile(r"\bdevour \d+\b", re.I),        # Sac creatures → N× counters
        re.compile(r"\bscavenge\b", re.I),          # Exile from GY → put counters on creature
        re.compile(r"\bincubate \d+\b", re.I),      # Create Incubator token with N counters
        re.compile(r"\bexalted\b", re.I),           # +1/+1 for each exalted when attacks alone
        re.compile(r"\bsoulbond\b", re.I),          # Pair with another creature for bonuses
    ]),
    # ── Ramp ────────────────────────────────────────────────────────────────────
    # FIX: modern oracle text says "Add {G}", never "add [N] mana". The original
    # pattern required the word "mana", missing every mana dork and rock.
    ("ramp", [
        re.compile(r"\badd[s]? \{[^}]+\}", re.I),  # "Add {G}", "Add {W} or {U}", "{T}: Add {C}"
        re.compile(r"add[s]? [^\n.]{0,40} mana", re.I),  # old-style text, kept for edge cases
        re.compile(r"search .{0,40} library .{0,40} (?:basic )?land card", re.I),
        re.compile(r"costs? \{?\d+\}? (?:generic )?(?:mana )?less", re.I),
        re.compile(r"without paying .{0,20} mana cost", re.I),
        re.compile(r"land .{0,30} additional .{0,30} land", re.I),
        re.compile(r"\bconvoke\b", re.I),           # Tap creatures to pay cost
        re.compile(r"\bdelve\b", re.I),             # Exile GY cards to reduce cost
        re.compile(r"\bimprovise\b", re.I),         # Tap artifacts to pay cost
        re.compile(r"\bemerge\b", re.I),            # Sacrifice creature to reduce cost
        re.compile(r"\baffinity for\b", re.I),      # Cost reduced by count of quality
        re.compile(r"\boverload\b", re.I),          # Pay more to affect all targets
        re.compile(r"\bundaunted\b", re.I),         # Cost reduced per opponent
        re.compile(r"\bbestow\b", re.I),            # Alternative: cast as Aura
        re.compile(r"\bmorph\b", re.I),             # Alternative: cast face-down for {3}
        re.compile(r"\bmegamorph\b", re.I),
        re.compile(r"\bdisguise\b", re.I),          # Ward 2 variant of morph
        re.compile(r"\bmanifest\b", re.I),          # Put face-down as 2/2
        re.compile(r"\bsuspend \d+\b", re.I),       # Exile with counters, cast for free later
    ]),
    # ── Graveyard ───────────────────────────────────────────────────────────────
    ("graveyard", [
        re.compile(r"return[s]? .{0,60} from .{0,20} graveyard", re.I),
        re.compile(r"\bmills?\b \d+", re.I),
        re.compile(r"puts? .{0,30} card[s]? .{0,20} into .{0,20} graveyard from .{0,20} library", re.I),
        re.compile(r"from your graveyard", re.I),
        re.compile(r"exile .{0,30} from .{0,20} (?:your |a |the )?graveyard", re.I),
        re.compile(r"\bflashback\b", re.I),         # Cast from graveyard
        re.compile(r"\bunearth\b", re.I),           # Return from GY temporarily
        re.compile(r"\bembalm\b", re.I),            # Exile from GY → white token copy
        re.compile(r"\beternalize\b", re.I),        # Exile from GY → 4/4 black token
        re.compile(r"\bencore\b", re.I),            # Exile from GY → copy for each opponent
        re.compile(r"\bdisturb\b", re.I),           # Cast from GY as enchantment
        re.compile(r"\bundying\b", re.I),           # Returns from GY with +1/+1 if none
        re.compile(r"\bpersist\b", re.I),           # Returns from GY with -1/-1 if none
        re.compile(r"\bdredge \d+\b", re.I),        # Mill N to return this from GY
        re.compile(r"\brecover\b", re.I),           # Pay cost when another creature dies → return
        re.compile(r"\bhaunt\b", re.I),             # Exile to haunted creature's ability
        re.compile(r"\bretrace\b", re.I),           # Cast from GY by discarding a land
        re.compile(r"\btransmute\b", re.I),         # Discard + pay → tutor same-CMC card
        re.compile(r"\bescape\b", re.I),            # Cast from GY by exiling other cards
        re.compile(r"\bblitz \{", re.I),            # Haste, sac EOT, draw on death
    ]),
    # ── Counterspells ───────────────────────────────────────────────────────────
    ("counterspell", [
        re.compile(r"counter target spell", re.I),
        re.compile(r"counter target .{0,40} spell", re.I),
        re.compile(r"counter that spell", re.I),
        re.compile(r"counter target activated", re.I),
        re.compile(r"counter target triggered", re.I),
        re.compile(r"counters? .{0,20} spell unless", re.I),
    ]),
    # ── Discard ─────────────────────────────────────────────────────────────────
    ("discard", [
        re.compile(r"(?:target player|that player|opponent|each player|each opponent) discards?", re.I),
        re.compile(r"discards? .{0,20} card[s]? (?:at random|of your choice|from hand)", re.I),
        re.compile(r"discards? their hand", re.I),
        re.compile(r"discards? a card", re.I),
    ]),
    # ── Stax ────────────────────────────────────────────────────────────────────
    # FIX: "doesn't untap during its controller's untap step" is the canonical
    # tap-lock oracle phrasing; only "can't untap" variants were previously covered.
    ("stax", [
        re.compile(r"(?:can't|cannot) cast spells", re.I),
        re.compile(r"(?:can't|cannot) cast .{0,40} spells", re.I),
        re.compile(r"(?:can't|cannot) activate abilities", re.I),
        re.compile(r"(?:can't|cannot) attack", re.I),
        re.compile(r"spells? .{0,30} (?:can't|cannot) be cast", re.I),
        re.compile(r"(?:players?|opponents?) (?:can't|cannot) .{0,30} (?:more than|unless)", re.I),
        re.compile(r"doesn.t untap during", re.I),
        re.compile(r"doesn.t untap (?:unless|as long)", re.I),
    ]),
    # ── Tutor ───────────────────────────────────────────────────────────────────
    ("tutor", [
        re.compile(r"search your library for .{0,60} card", re.I),
    ]),
    # ── Life ────────────────────────────────────────────────────────────────────
    ("life", [
        re.compile(r"you gain \d+ life", re.I),
        re.compile(r"gain[s]? \d+ life", re.I),
        re.compile(r"you gain X life", re.I),
        re.compile(r"your life total becomes", re.I),
        re.compile(r"each opponent loses \d+ life", re.I),
    ]),
    # ── Pump ────────────────────────────────────────────────────────────────────
    ("pump", [
        re.compile(r"gets? \+\d+/[+\-]\d+", re.I),
        re.compile(r"gets? \+X/\+\d", re.I),
        re.compile(r"gets? \+\d/\+X", re.I),
        re.compile(r"gets? \+X/\+X", re.I),
        re.compile(r"base power and toughness", re.I),
        re.compile(r"creatures? you control get \+", re.I),
        re.compile(r"\brampage \d+\b", re.I),       # +N/+N for each blocker beyond first
        re.compile(r"\bbushido \d+\b", re.I),       # +N/+N when it blocks or is blocked
        re.compile(r"\bbattle cry\b", re.I),        # Other attackers get +1/+0
        re.compile(r"\bflanking\b", re.I),          # Non-flanking blockers get -1/-1
        re.compile(r"\bmelee\b", re.I),             # Gets +1/+1 for each opponent attacked
        re.compile(r"\bannihilator \d+\b", re.I),   # Attacker forces sac of N permanents
    ]),
    # ── Protection ──────────────────────────────────────────────────────────────
    # NEW category — was in the SPEC taxonomy but never implemented in _PATTERNS.
    # Scryfall stores "Protection" (base keyword) without the qualifier; after
    # stripping, "from red" remains. The stripping pre-pass now handles that, but
    # this pattern catches cards where "protection from X" is an oracle-text effect
    # (granted by another permanent, or on a card not using the keyword form).
    ("protection", [
        re.compile(r"\bprotection from\b", re.I),
        re.compile(r"\bregenerate\b", re.I),        # "Destroy prevention" keyword
        re.compile(r"prevent .{0,30} damage", re.I),
        re.compile(r"ward \d+\b|ward \{", re.I),    # Ward cost left after base-keyword strip
        re.compile(r"(?:can't|cannot) be (?:the target of|targeted by)", re.I),
    ]),
    # ── Evasion ─────────────────────────────────────────────────────────────────
    # NEW category — was in the SPEC taxonomy but never implemented in _PATTERNS.
    # Covers evasion keywords that ARE in Scryfall's keywords array (so keyword_count
    # already counts them) but whose companion oracle text sometimes appears in
    # text_for_regex — and non-keyword unblockable effects.
    ("evasion", [
        re.compile(r"\bhorsemanship\b", re.I),
        re.compile(r"\bshadow\b", re.I),
        re.compile(r"\bskulk\b", re.I),
        re.compile(r"\bninjutsu\b", re.I),
        re.compile(r"\bintimidatem?\b", re.I),
        re.compile(r"\b(?:swamp|forest|mountain|island|plains|land)walk\b", re.I),
        re.compile(r"\bfear\b", re.I),              # Can only be blocked by artifact/black
        re.compile(r"(?:can't|cannot) be blocked(?! except by two)", re.I),
        re.compile(r"\bdash \{", re.I),             # Alternative cost → haste + return to hand
        re.compile(r"\bblitz \{[^}]*\}[^{]", re.I),  # Narrower than graveyard blitz match
    ]),
    # ── Steal ───────────────────────────────────────────────────────────────────
    ("steal", [
        re.compile(r"gain control of target", re.I),
        re.compile(r"gain control of .{0,40} target", re.I),
        re.compile(r"gains? control of (?:target|all|each|that)", re.I),
        re.compile(r"exchange control", re.I),
    ]),
    # ── Copy ────────────────────────────────────────────────────────────────────
    ("copy", [
        re.compile(r"copy target spell", re.I),
        re.compile(r"copy of target", re.I),
        re.compile(r"copy of .{0,40} spell", re.I),
        re.compile(r"becomes? a copy of", re.I),
        re.compile(r"create[s]? a token that.s a copy", re.I),
        re.compile(r"\bstorm\b", re.I),             # Copies for each prior spell this turn
        re.compile(r"\bcipher\b", re.I),            # Encoded spell copies on combat damage
    ]),
    # ── Blink ───────────────────────────────────────────────────────────────────
    ("blink", [
        re.compile(r"exile target .{0,60} you control.{0,20} return it", re.I),
        re.compile(r"exile .{0,40} then return .{0,40} to the battlefield", re.I),
        re.compile(r"phases? out", re.I),
    ]),
]

CATEGORY_NAMES: list[str] = [name for name, _ in PATTERNS]

_REMINDER_RE = re.compile(r'\([^)]+\)')


def strip_reminder_text(text: str) -> str:
    """Remove parenthesized reminder text. (Verbatim from analyze.py.)"""
    return _REMINDER_RE.sub('', text).strip()


def strip_keyword_names(text: str, keywords: list[str]) -> str:
    """
    Remove named keyword strings from oracle text before Layer 2 regex.
    Prevents double-counting abilities already captured by the keywords field.
    (Verbatim from analyze.py — see that file for the full design notes.)
    """
    kw_lower = {kw.lower() for kw in keywords}

    # Pre-pass A: compound qualifier keywords — strip the full phrase, not just the base name
    if "protection" in kw_lower:
        text = re.sub(r"\bprotection from [^\n,;]+", "", text, flags=re.I)
    if "affinity" in kw_lower:
        text = re.sub(r"\baffinity for [^\n,;]+", "", text, flags=re.I)

    # Pre-pass B: parametric keyword abilities — strip "Keyword N" so a bare digit
    # isn't left behind as non-empty, unclassifiable oracle text.
    _PARAMETRIC_KW = re.compile(
        r"\b(?:bloodthirst|modular|bushido|rampage|fabricate|bolster|adapt|renown|"
        r"graft|devour|annihilator|toxic|poisonous|afflict|amplify|fading|vanishing|"
        r"absorb|frenzy|dredge|reinforce|backup|soulshift|connive|incubate|amass|"
        r"ravenous|sunburst|tribute|squad) \d+\b",
        re.I,
    )
    text = _PARAMETRIC_KW.sub("", text)

    # Main pass: strip individual keyword names by word boundary
    for kw in keywords:
        text = re.sub(rf"\b{re.escape(kw)}\b", "", text, flags=re.I)

    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"^[\s,;]+|[\s,;]+$", "", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Post-pass A: drop any line that contains only mana symbols, numbers, and punctuation
    lines = [ln for ln in text.split("\n") if re.search(r"[a-z]{2,}", ln, re.I)]
    text = "\n".join(lines)

    # Post-pass B: drop orphaned trigger clauses whose effect was fully stripped away.
    text = re.sub(
        r"(?m)^(?:when(?:ever)?|at the |as )[^\n]+,\s*(?:\{[^}]*\}\s*|\.?\s*)*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def classify_with_regex(text: str) -> list[str]:
    """
    Return ability category tags matched against oracle text (post-keyword-strip).
    Returns ["other"] for non-empty text with no pattern match.
    Returns [] for blank text (vanilla creatures, lands).
    (Verbatim from analyze.py.)
    """
    if not text.strip():
        return []
    matched = [cat for cat, patterns in PATTERNS if any(p.search(text) for p in patterns)]
    return matched if matched else ["other"]


# ---------------------------------------------------------------------------
# Similarity-metric layer (new — built ON TOP of the Post 2 feature extraction)
# ---------------------------------------------------------------------------

def card_feature_set(oracle_text: str, keywords: list[str], is_land: bool = False) -> frozenset[str]:
    """
    The Post 2 feature vector for one card, as a set of binary feature names:
      - "cat:<category>" for each of the 18 regex categories that match the
        oracle text (after reminder-text and keyword-name stripping);
        the residual "other" bucket is EXCLUDED — it is unclassified text,
        not a shared function.
      - "kw:<keyword>"  for each Scryfall keyword (lowercased).
    Lands get no regex categories (matching Post 2), only keywords.
    """
    stripped = strip_reminder_text(oracle_text or "")
    text_for_regex = strip_keyword_names(stripped, keywords or [])
    categories = [] if is_land else classify_with_regex(text_for_regex)
    feats = {f"cat:{c}" for c in categories if c != "other"}
    feats |= {f"kw:{kw.lower()}" for kw in (keywords or [])}
    return frozenset(feats)


def cosine_similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """
    Cosine similarity between two binary feature vectors represented as sets:
        cos(a, b) = |a ∩ b| / sqrt(|a| * |b|)
    Returns 0.0 if either set is empty (a card with no identified abilities
    has no function-similarity neighborhood).
    """
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / ((len(a) * len(b)) ** 0.5)
