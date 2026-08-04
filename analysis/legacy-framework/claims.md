# Claims Registry — canonical knowledge store

**This file is the canonical storage for the framework's knowledge.** Every
substantive claim lives here as a card-level (or mechanism-level) interaction
claim with provenance and graduation status. `framework.md` and `archetypes/*`
are **rendered views**: human-readable narratives over these claims. When a
view and the registry disagree, the registry wins; fix the view.

## Provenance vocabulary

| Tag | Meaning |
|---|---|
| `data` | Validated against the tournament panel (within-archetype win log-OR or equivalent), n and effect size cited |
| `primer` | Attested by primer corpus / community qualitative judgment |
| `analytical` | Derived from framework reasoning, no direct empirical test |

## Graduation pipeline (brief §2.3)

Claims enter as **HYPOTHESIS** (provenance `primer` and/or `analytical`).
A claim is promoted to **VALIDATED** only by quantitative confirmation
(provenance gains `data`). Primers may generate hypotheses and exclusion
labels; they may not, by themselves, validate. Nothing VALIDATED may depend
solely on primer attestation — that would contaminate the future use of
primers as benchmark/test data.

When evidence contradicts a claim, mark it **REFUTED** and keep it (with the
evidence) — refuted claims are calibration data for the qualitative sources
that produced them.

---

## Mechanism claims (card-level interaction structure)

### C1. Reactive consumable permission anti-synergizes with recursive engine slots — VALIDATED
**Claim:** Cards whose disruption is consumed per use (Force of Will class)
reduce win rate when added to decks whose disruption compounds via recursion
(Life from the Loam + Wasteland class); the slots they occupy should hold
recursive pieces.
**Provenance:** `data` + `analytical`. FoW within Lands: **−0.992** (n=41);
Island within Lands: −1.088 (n=63).
**Scope note:** The data point is archetype-conditioned; the card-level
mechanism (consumable-reactive vs. recursive-compounding slot conflict) is the
claim. Portable to any format with recursion engines.

### C2. Cantrip density compensates per-use card-disadvantage costs in tempo shells — VALIDATED
**Claim:** Decks paying repeated card-disadvantage costs (FoW's 2-for-1)
require maximum-density cheap selection to maintain parity; removing it is
measurably losing.
**Provenance:** `data` + `primer`. Ponder within Delver: **+0.713**
(n=15,404 with; the 94 builds without win significantly less).

### C3. Above-threshold draw engines in optimized cantrip suites are ban-trajectory cards — VALIDATED
**Claim:** When a selection/draw card materially exceeds the incumbent cantrip
threshold in a tempo shell, its within-archetype signal is extreme and it gets
banned.
**Provenance:** `data`. Dig Through Time +1.014 (Delver) / +1.339 (Miracles);
Treasure Cruise +0.676; both banned. Historical: Expressive Iteration banned.

### C4. Fast mana's card-disadvantage cost drags win rate even where structurally required — VALIDATED
**Claim:** Card-cost fast mana (Chrome Mox class) underperforms within the
archetypes that nonetheless need it; the cost caps the archetype's ceiling
rather than making the card a cut.
**Provenance:** `data`. Chrome Mox within Red Prison: **−0.804** (1,405 of
1,430 run it); LED within Oops: −1.785 (n=21, low-n caveat).
**Corollary (hypothesis):** card-cost-free fast mana at the same rate would be
a structural, not incremental, upgrade.

### C5. Self-resilience to your own lock is a real win condition — VALIDATED
**Claim:** Decks deploying symmetric locks (Blood Moon class) win more when
their own mana base is insulated from the lock.
**Provenance:** `data`. Mountain within Red Prison: **+0.642** (the 97
basic-less builds underperform).

### C6. In pure-speed combo, consistency beats resilience — VALIDATED
**Claim:** In archetypes where speed substitutes for permission entirely,
slots spent on redundancy/consistency outperform slots spent on
interaction-resilience.
**Provenance:** `data`. Within Oops: Wild Cantor +0.629, Summoner's Pact
+0.583, Turntimber Symbiosis +0.547 vs. Jack-o'-Lantern −0.479, Fell the
Profane −0.519.

### C7. Zero-cost from-hand protection is the only viable protection shape for speed combo — VALIDATED (low n)
**Claim:** Protection that costs no mana or cards on the combo turn
(Chancellor of the Annex / Grief class) is on-axis for speed combo; anything
costlier is off-axis.
**Provenance:** `data` (weak) + `primer`. Grief within Oops: +0.397 (n=32).

### C8. Speed-optimized mana is anti-synergistic in time-asset archetypes — VALIDATED
**Claim:** Acceleration cards underperform in decks whose value compounds with
game length; they buy the resource the deck least needs.
**Provenance:** `data`. Noble Hierarch within Lands: −0.936 (n=23); Elvish
Spirit Guide: −0.890.

### C9. Defensive insurance conflicts with the clock imperative in tempo — VALIDATED (low n)
**Claim:** Cards bought as insurance against losing board state underperform
in decks whose plan is to end the game before insurance pays off.
**Provenance:** `data`. Seal of Removal within Delver: −1.200 (n=49);
Moonshadow −1.968 (n=20, at threshold).

### C10. Cross-archetype staples converge to field-average win log-OR — VALIDATED (metric property)
**Claim:** For cards in >~20% of the field, win log-OR measures the average
quality of the archetypes running them, not card contribution. Use inclusion
rate + co-occurrence instead.
**Provenance:** `data`. FoW: +0.017 at 54% inclusion.

---

## Hypotheses (not yet empirically tested — do not treat as validated)

### H1. FoW's value is card-dependent, not time-dependent — HYPOTHESIS
**Claim:** Force of Will does not bleed out over game length (countering a
game-winner on turn 15 = turn 3); the time pressure on FoW decks comes from
accumulated card disadvantage and land-light construction, not permission
decay. Daze, by contrast, does decay.
**Provenance:** `analytical` + `primer`.
**Possible test:** game-length-conditioned win rates are unavailable
(no play-by-play data — brief §2.3); a weak proxy could be FoW-deck
performance vs. grind archetypes by event round count. Open.

### H2. Threshold effects are nonlinear near the slot boundary — HYPOTHESIS
**Claim:** Small magnitude differences (Brainstorm's 3-card look vs. a
hypothetical 2) produce discontinuous adoption differences because of
combinatorial search and fetch-shuffle interactions.
**Provenance:** `analytical`. The exclusion dataset (Phase 1.3) is the
designed test: thresholds become estimable decision boundaries.

### H3. Lands' splash failures are about the spells, not the colors — HYPOTHESIS
**Claim:** Island −1.088 / Underground Mortuary −0.937 within Lands reflect
the off-strategy *reason* for splashing (reactive spells), not colored mana
itself; a low-commitment colored source carries no such penalty.
**Provenance:** `analytical` interpretation of `data` observations.
**Note:** the underlying log-OR observations are validated; this causal
reading of them is not. Registered as the live interpretation behind the
Petrified Hamlet call in the Strixhaven post (graded retrodictively only).

### H4. Permission time-profile taxonomy — HYPOTHESIS (organizing scheme)
**Claim:** Disruption divides into reactive-consumable / proactive-permanent /
recursive-compounding / speed-substitute, with distinct time profiles, and
archetype construction follows from which profile a deck adopts.
**Provenance:** `analytical` + `primer`. C1/C6/C8 are consistent with it; the
taxonomy itself is a lens, not a tested claim. Its predictions surface through
the claims above.

### H5. Signal-type priors — VALIDATED AS AVERAGES, weak as priors
**Claim:** Mean win log-OR by extracted signal (lock_piece +0.122 →
combo_piece −0.040, table in `evaluation.md` Q1) ranks which constraint types
the format rewards.
**Provenance:** `data` (averages) over `primer`-derived labels. Caveat: the
labels come from primer extraction (LLM), so this mixes provenance — the
averages are only as good as the labeling. Treat as prior, never verdict.

---

## Registry maintenance

- New primer- or analysis-derived insights enter as HYPOTHESIS with a named
  possible test.
- Promotion requires citing the quantitative evidence inline.
- Views (`framework.md`, `archetypes/*`) cite claim IDs where they rely on
  registry content. New narrative in views that embeds an untagged claim is a
  refactor bug.
