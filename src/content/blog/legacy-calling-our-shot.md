---
title: "Calling Our Shot: Registered Predictions for Legacy's Next Two Sets"
description: "We locked predictions for Marvel Super Heroes and The Hobbit before the results existed — four competing methods, graded in public. Here's the scorecard so far, and the bets we're making next."
pubDate: "2026-08-06"
updatedDate: "2026-08-15"
---

[The last post](./legacy-card-evaluation) built a framework for evaluating new Legacy cards from first principles — constraint sets instead of card lists, "does it beat the card it would replace?" instead of "is it efficient?" But it tested that framework on *Secrets of Strixhaven*, roughly four weeks after release, when adoption was already visible. That's a calibration exercise, not a prediction. It's easy to look smart about a race you watched finish.

So this time we called our shot. We locked predictions for two sets — Marvel Super Heroes and The Hobbit — **before the cards saw competitive play**, committed them to a timestamped git file, and pointed four different prediction methods at the same cards to see which one is actually worth listening to. One set (Marvel) now has seven weeks of results. The other (The Hobbit) hasn't been released yet. This post is the honest scorecard on the first, and the on-the-record bet on the second.

## The setup: four predictors, one question

Every method here is answering the same question, the one the framework post argued is *the* question in a 30-year-optimized format: not "is this card good?" but **"does it beat the specific card it would replace, in a deck that wants what it does?"** Four ways to answer it, from dumbest to most involved:

1. **Abilities-per-mana baseline** — the [Post 2](./mtg-card-power) heuristic. Count a card's abilities, divide by mana cost. Purely mechanical, zero context. The straw man — except it isn't a straw man, because it gets graded honestly alongside everything else.
2. **Expert framework (blind)** — the constraint-set method, applied to card text only, with no community input and no web access. This is the human-judgment predictor.
3. **Community consensus** — what the competitive community flags in early-spoiler discussion. The crowd's read, held out from the framework so it can't contaminate it.
4. **Trained value model** — a machine-learned pairwise ranker.

The framework and the model both lean on one empirical fact, drawn from 87,000 Legacy decks spanning 2011–2026: some *kinds* of cards reliably correlate with winning, and others don't.

![Win log-OR by signal type](/images/legacy-calling-our-shot/signal_priors.png)

Lock pieces, card advantage, cantrips, and mana denial carry positive within-format win log-OR. Combo pieces, free spells, and graveyard effects average out around zero — not because they're bad, but because the category mixes format-defining cards with narrow ones. That's the *prior*. The threshold rule — beat the weakest incumbent in the slot — is the *test*.

The model deserves a specific note, because it's the new toy. It's a logistic pairwise ranker trained on **145,626 preference pairs** extracted from deck primers: for each card a deck played, we pair it against a functionally-similar card the deck *passed over*, and the model learns to rank the first above the second, conditional on the field. Deduplicated and cross-validated, it hits **~0.80 held-out pairwise accuracy** — comfortably above the 0.5 coin-flip. It learns something real. Whether "learns something real" equals "worth trusting" is exactly what a prospective test is for.

## What actually happened: the Marvel scorecard

Marvel Super Heroes released June 26. Seven weeks of tournament data later, the reality is stark: out of 525 new Legacy-legal cards, **exactly two** cleared the noise floor.

![Actual Legacy adoption of new Marvel cards](/images/legacy-calling-our-shot/marvel_adoption.png)

The Fantasticar shows up in **3.4%** of Legacy decks — a format-warping number, in the same neighborhood as Doomsday, complete with ban chatter. Loki, God of Mischief lands at **0.8%**. Everything else is a rounding error. (Reprints like Swords to Plowshares are excluded — a reprint of an already-legal card isn't a new-adoption event, a distinction that matters more in rotating formats but is worth being strict about everywhere.)

Now the part that separates the predictors — who called what:

![Marvel predictor scorecard](/images/legacy-calling-our-shot/marvel_scorecard.png)

Read the columns and a clear story falls out:

- **The community caught the one that mattered.** It called Fantasticar PLAYED. So did the model. The framework and the baseline both said merely FRINGE.
- **The model was bold and noisy.** It also nailed Fantasticar — its single most confident call at P = 0.96 — but it cried PLAYED on *five* cards that went nowhere (Mole Man, Hex Magic, Avengers Disassembled, Elektra, Jennifer Walters). High recall, low precision.
- **The framework was precise but timid.** It correctly rejected every one of the model's false positives — its NOT-PLAYED calls were nearly flawless — but it under-called Fantasticar and its lone PLAYED pick, Mole Man, flopped at 0.1%.
- **Everyone missed Loki.**

Put numbers on it. Of the cards each method was willing to call PLAYED, how many actually were?

| Predictor | PLAYED precision | Caught Fantasticar? | Verdict |
|---|---|---|---|
| **Community** | 1 / 2 (50%) | ✅ | best signal-to-noise |
| **Model** | 1 / 6 (17%) | ✅ | right about the winner, wrong five more times |
| **Framework** | 0 / 1 (0%) | ❌ (called FRINGE) | precise on the noes, missed the yes |
| **Baseline** | 0 / 2 (0%) | ❌ (called FRINGE) | rate without a home |

The lesson isn't "the model is bad." It's that the model and the abilities-per-mana baseline **share a blind spot**: both rate a card's stats against an incumbent, and neither can feel whether a deck actually *wants* the card. The community — made of people who play the format — feels it. That's a genuinely useful thing to have learned before betting on the next set.

(Caveat, stated up front: this is the *preliminary* grade off aggregate play rates, and the full-year denominator understates Marvel cards' true post-release rates. The formal grade — with within-archetype win log-OR — runs August 15. It won't change the qualitative story; Fantasticar is not going to un-warp the format.)

## The shot: The Hobbit

The Hobbit releases August 14. We locked predictions on **August 4 — before the prerelease**, the cleanest prospective test we've run, and the first where the model is pre-registered next to everyone else instead of bolted on afterward. Here's the board.

![The Hobbit predictions, locked pre-release](/images/legacy-calling-our-shot/hobbit_predictions.png)

The headline is agreement: **every method reads this as a low-impact Legacy set.** No predictor calls a single consensus PLAYED. A full sweep of all 207 new cards turns up no free spells, no fast mana, no mana denial, no lock pieces — none of the signal types that historically clear Legacy's bar. It's a tribal/Equipment/Saga set built for Limited and Commander.

Which makes the *disagreements* the whole experiment:

- **Riddles in the Dark** — the consensus pick, and it grades up the more bullish you are: model PLAYED (0.69), framework and community FRINGE, baseline NOT. It's a three-mana Fact or Fiction that fuels the graveyard. If it settles in as an occasional 1-of, the model over-called again — its Marvel pattern, exactly.
- **Bilbo, Thief in the Night** — model **and** community bullish, framework says NOT PLAYED. This is the graveyard-engine bet, and the single most informative card on the board — the "Mole Man" of this set, except the disagreement runs the other way (models optimistic, framework skeptical).
- **Gandalf, Goblins' Bane / Gollum / An Unexpected Party** — community-only FRINGE, everyone else NOT. This is the direct rerun of the Fantasticar test: *does the crowd see something the models structurally can't?*
- **Most Decrepit Old Bird** — the baseline's lone PLAYED, and a textbook abilities-per-mana false positive: a cheap body with keyword soup and no home.

The on-the-record set-level bet, from the framework: **no Hobbit card reaches PLAYED** (≥1% of Legacy decks), no tier-1 deck changes its maindeck, and at most one or two cards see fringe play — Riddles in the Dark the likeliest.

## What would make us more (or less) right

Prediction is only interesting if you say in advance what could break it. Here are the live failure modes, roughly in order of how much they'd move the scorecard:

**The recall problem — our biggest risk.** On Marvel, of the two cards that actually mattered, one (Loki) was on *nobody's* list. That's a 50% miss rate on the cards that counted. Our whole apparatus is good at grading cards once they're named and useless on cards it never named. If The Hobbit has a Loki, all four columns will be silent on it in unison. The empirical screen is supposed to be the safety net that catches these; on Marvel it didn't, and fixing its recall is the open engineering problem behind this whole project.

**New archetypes.** The framework's worst Marvel call — Fantasticar as FRINGE — wasn't bad card evaluation, it was a *category* error: the framework grades cards against the slots that already exist, and Fantasticar made its own slot. Any Hobbit card that spawns a new deck will be systematically under-called by the framework and, if Marvel is any guide, over-called correctly by the community. Bilbo, Thief in the Night is the card most likely to do this.

**Bans.** The Fantasticar is ban-watched. A mid-window B&R action is the single biggest exogenous shock: banning it reshuffles the field, and cards we called NOT PLAYED against the current metagame could become playable against the next one (or vice versa). Our predictions are conditional on "no B&R changes" — stated explicitly in the lock — so a ban doesn't make us wrong, but it does end the clean experiment early.

**Small-sample noise.** Legacy's niche archetypes are thin. Lands is ~3.4% of the field; a card that's a 4-of in *every* Lands deck is still under 1% of all decks. Our ≥1% "PLAYED floor" can miss a card that's genuinely adopted inside a narrow strategy. The within-archetype win log-OR — landing with the formal grade — is the correction: it asks "among decks already playing this strategy, do the ones running this card win more?", which is immune to the archetype being small.

**The graveyard axis.** Both of the models' Hobbit bets — Bilbo Thief and Riddles — want a full graveyard. If a Dragon's Rage Channeler / delve shell rises after The Hobbit, the model-and-community bullishness pays off. If the field stays combo- and tempo-heavy, the framework's NOT holds. This one we'll be able to read directly off the metagame share of graveyard decks at grading time.

## When we find out

No moving the goalposts. The predictions are in git, timestamped before the cards were legal, and the grades run on a schedule — automated cloud jobs that pull the adoption data, grade all four predictors against the locked files, and commit the results.

![Grading timeline](/images/legacy-calling-our-shot/timeline.png)

- **August 15** — Marvel's formal grade: the within-archetype win log-OR and the final four-way scorecard.
- **October 2** — The Hobbit's grade: ~7 weeks of post-release results against the board above.

The honest state of things, seven weeks in: **the crowd beats the models at spotting what will matter, the framework beats the crowd at precision, and everyone has a recall problem.** None of that would be knowable if we'd waited to see the results first and then explained why we were right. Check back in October — the shots are already fired.

---

## Addendum, August 15: they banned it

Four days after this post went up, [Wizards banned The Fantasticar in Legacy](https://magic.wizards.com/en/news/announcements/banned-and-restricted-august-10-2026), effective August 10. It's restricted in Vintage. No written rationale for the Legacy line — just the one-sentence notice.

Start with the sentence that aged worst. Above, in the caveat about the preliminary grade: *"Fantasticar is not going to un-warp the format."* It did not un-warp the format. The format was un-warped for it, by fiat, ninety-six hours later. In context the claim was narrow — that the formal grade wouldn't overturn the qualitative story, which it still won't — but as a standalone prediction about a ban-watched card it's a clean miss, and it stays in the text.

Everything else here got *better*, which is a strange thing to have to report.

**The scorecard's central result is confirmed by the strongest available external referee.** The finding was that community and model called Fantasticar PLAYED while the framework and the baseline said merely FRINGE. A ban is about as emphatic a ruling as exists that PLAYED was the right call — the card wasn't just played, it was format-warping enough that the designers removed it seven weeks after release. The community and model margin over the framework widens.

**The framework's failure diagnosis was right for the reason we said.** The post argued its Fantasticar miss "wasn't bad card evaluation, it was a *category* error: the framework grades cards against the slots that already exist, and Fantasticar made its own slot." WotC skipped the English rationale, but [CoolStuffInc's reporting](https://www.coolstuffinc.com/a/banned-and-restricted-update-08102026) has the substance: the card was banned because a wide variety of *new* archetypes formed around it — Vroomsday, artifact decks, even a fair Dimir build — enabled by Legacy's lands that tap for two, its 0-cost artifacts, and its rituals. That is "it made its own slots," plural, in the format designers' own account. Nice to have the diagnosis corroborated; less nice that the framework needed it.

**The grading window is now 6.5 weeks, not seven.** A banned card stops accruing adoption on its effective date, so any window running past August 10 counts decks that could not have played it and drags both the share numbers and the within-archetype win log-OR toward zero. The harness now enforces the clip rather than trusting us to remember it — a ban-date table that clips the window automatically, which is what the codebase had already been doing by hand for Uro and White Plume Adventurer since the historical roster. Timely: the panel ended August 2 when this was written, so today's re-scrape is the first to reach past the ban.

**And the Hobbit experiment survived — better than survived.** The registered risk was a *mid-window* B&R shock, which would have ended the clean experiment early. Instead the ban landed August 10 and The Hobbit released August 14. The entire grading window sits in one post-ban field. The predictions were locked August 4 against a metagame that included a ~6% Fantasticar axis and no longer exists — that mismatch gets stated, not excused, when we grade — but the field is *stable across the window*, which is the condition the grade actually needs. Two knock-ons for October: the archetype shares in the locked conditioning set are stale as of August 10, and the graveyard-axis read that decides the Bilbo and Riddles bets has to be baselined on post-ban data.

One more thing worth noting for the recall problem, our stated biggest risk: a banned format-definer vacates slots. If The Hobbit produces a card that matters, "it fills a hole the ban just opened" is precisely the kind of card that appears on none of our four lists. We said in advance that a Loki would be invisible to us. We now have a specific reason to expect one.

The predictions are still in git, still timestamped, still ungraded until October 2.
