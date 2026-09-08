# The benchmark was the bottleneck: pooling, adjudication, and a ceiling that wasn't

Follows `research/families.md`, which measured a mined intervention at "+1.9pp
recall, not significant" and could not say more. This note is about why it
could not say more, and it ends with the reference queries — the thing every
run has been measured against — scoring **40.5%**.

## 1. The benchmark was saturated, not noisy

The working theory was seed noise. It was wrong. Across six runs (3 control,
3 families) of 37 scorable questions:

| | |
|---|---|
| questions passing in **every** run | 19 |
| questions failing in **every** run | 16 |
| questions whose verdict ever changed | **2** |

Two questions carried the entire ±1 spread in the headline. Adding seeds to a
benchmark with a dynamic range of two questions buys nothing — 35 of 37
questions would return the same verdict however many you ran.

The cause is density. The eval set judged **145 cards over 37 questions**, about
four each, so a question was decided by three `expect_present` cards and one
`expect_absent`. "Found 2 of 3" and "found 0 of 3" score identically.

## 2. One golden was simply wrong, and it was worth 1 question

`removal-that-never-says-destroy` listed **Pongify** in `expect_present`.
Pongify's Forge node is `SP$ Destroy` and its oracle text opens "Destroy target
creature", so it cannot satisfy "without ever saying destroy". This was flagged
in `compiled_questions.json` `judgment_calls` when the harness was built and
left pending an owner decision.

Moved to `expect_absent`. The reference ceiling went **36/37 → 37/37**. It was
the only thing between the vetted queries and a perfect score, which is the
first hint that a perfect score was the problem.

## 3. Pooling

Standard IR practice (TREC): run several systems, take the union of what they
return, judge that pool, and treat unjudged cards as unjudged rather than as
negatives. `benchmark/pool.py` does this over the six runs plus the reference.

| band | cards | used? |
|---|---|---|
| unanimous, unjudged | 4,889 | **no** — a card every system returns cannot separate them, and adding thousands of easy cards would push every arm toward 100% and *reduce* resolution |
| contested (some systems, not all) | 5,203 | **yes** — this is where the resolution lives |
| singleton (one system only) | 4,005 | no — usually one system misfiring |

Capped at 30 per question, deterministically spread over the name-sorted pool:
**562 cards** for adjudication.

### What the assessors could and could not see

Question text, its `trap` and `notes`, and each card's name, type line and
oracle text. **Not** any query, **not** which system returned the card, **not**
the vote count. An assessor who can see the vote ratifies the majority instead
of reading the card, and the goldens would then only ever confirm what the
current compiler already does. `tests/test_pool.py` asserts the task file leaks
none of it.

`unclear` was a first-class verdict. **74 of 562 (13%)** came back unclear;
those stay out of scoring entirely. A card the question's wording does not
decide is a fact about the *question*, and forcing it to a side would invent a
golden.

Result: `expect_present` **106 → 302**, `expect_absent` **39 → 331**.

## 4. The instrument got better, and my prediction of how was wrong

I predicted variance would fall as 1/√n. **It rose sharply** — the contested
band is by construction where runs disagree, so densifying with it adds exactly
the high-variance cards. Raw sd is the wrong figure of merit:

| golden set | arm gap | pooled sd | **seeds/arm needed to call it** |
|---|---|---|---|
| original 106 | +1.9pp | 1.85pp | **16** |
| dense 302 | +8.6pp | 5.44pp | **7** |

Signal grew 4.5×, noise grew 2.9×. The benchmark is now **2.3× cheaper to draw
a conclusion from**, despite being noisier. Splitting the two bands shows where
that came from:

| cards | control | families | gap |
|---|---|---|---|
| original 106 (consensus core) | 75.2% | 77.0% | +1.9pp |
| **added 196 (contested band)** | 58.8% | **71.1%** | **+12.2pp** |

The old goldens were dominated by cards every system already finds. They were
measuring the saturated part of the problem.

> The all-or-nothing pass metric moves the *other* way (discriminating
> questions 2 → 1, always-fail 15 → 27), because needing 8 of 8 cards is
> strictly harder than 3 of 3. With dense goldens the pass count is the wrong
> headline; recall is.

## 5. Validating the adjudication

The reference queries never saw the adjudication, so they are an independent
check:

| | agreement |
|---|---|
| assessor said **absent** | **278/292 (95%)** |
| assessor said **present** | 103/196 (53%) |

95% on absent says the assessors are calibrated — a loose assessor would
over-call present *and* under-call absent. So the 53% is about the reference,
not the assessors. Spot-checking the worst case, `attack-trigger-makes-token`
("creatures that spit out a token whenever they attack"), the 20 cards the
assessor added and the reference misses include:

- **Flamerush Rider** — "Whenever Flamerush Rider attacks, create a token that's
  a copy of another target attacking creature"
- **Furnace-Blessed Conqueror** — "Whenever ~ attacks, create a tapped and
  attacking token that's a copy of it"
- **Ghired, Conclave Exile** — "Whenever Ghired attacks, populate"

These are textbook matches. The reference query says `{"api": "Token"}`; these
cards create tokens through **`CopyPermanent`**. That is precisely the
disjunctive-family failure `research/families.md` was built for, and it is
covered by the mined `[create] Token, CopyPermanent, Amass` line.

## 6. The ceiling was an artifact

| reference queries scored against | result |
|---|---|
| original goldens | **37/37 (100%)** |
| pooled, blind-adjudicated goldens | **15/37 (40.5%)**, recall 69.2% |

The handoff calls the reference "the ceiling every live run is measured
against". It is not a ceiling. Its 100% was earned on 106 cards it was
effectively co-designed with; on cards chosen without reference to it, it has
large recall gaps of exactly the kind it was supposed to bound.

**The compiler already beats it.** On the dense goldens the families arm scores
73.2% recall against the reference's 69.2%.

This also re-reads the families result. On `attack-trigger-makes-token` the
arms measure control **0.0 / 20** and families **13.3 / 20** — a question the
old benchmark scored 0/6 for *both* arms, because none of its three goldens was
a `CopyPermanent` card. The intervention was doing something the instrument
could not see.

## 7. Limits, stated plainly

- **Pool bias.** These goldens are valid for comparing systems that contributed
  to the pool. A new system that finds *different* correct cards is penalised
  for cards nobody judged. This is the known TREC pool-bias problem and the
  mitigation is the standard one: re-pool and re-adjudicate when a materially
  different system is evaluated.

  It was then measured on the eight runs added for the 7-seed test, none of
  which contributed to the pool: **judged fraction of returned cards 4.7% in
  both arms, difference 0.0pp**. Absolutely the bias is large (95% of returned
  cards are unjudged, which is why *recall* and not precision is the headline)
  but it is symmetric, so arm comparisons hold.
- **Seven seeds, not three.** ✅ **Run, and the prediction held.** At 7 seeds
  the families effect is **+9.8pp recall, exact permutation p = 0.017** on
  these goldens and **still not significant (p=0.156) on the old ones**, from
  the identical 14 runs. The old benchmark would have needed ~20 seeds per arm.
  See `research/families.md` §9.
- **74 unclear cards** are a measurement of the *questions*. Where they cluster
  (`cast-from-graveyard-permanents`, `play-lands-from-graveyard`,
  `pay-life-activation-cost`) the wording genuinely does not decide, and
  rewording is better value than more adjudication.
- **Capped at 30 per question**, so the pool is sampled, not exhausted.
  `removal-that-never-says-destroy` alone had 3,780 contested cards.
- **Assessors were LLM agents**, one per question, no double-judging. There is
  no inter-assessor agreement number. The 95%-on-absent check above is the only
  external validation, and it is indirect.
- **Nothing was retired.** Retiring the underdetermined questions was the
  original plan; it would have cut the question count and *reduced* power.
  Densifying them was strictly better.

## 8. Reproducing

```bash
python benchmark/pool.py benchmark/agent_runs/*_s*.json --out benchmark/pool.json
python benchmark/adjudicate.py tasks          # -> benchmark/adjudication/*.md
#   assessors write benchmark/adjudication/verdicts/<id>.json
python benchmark/adjudicate.py merge          # -> candidate_questions.dense.json

python benchmark/rescore.py benchmark/agent_runs/*_s*.json \
    --baseline benchmark/candidate_questions.json \
    --questions benchmark/candidate_questions.dense.json

python benchmark/eval_compile.py --source reference \
    --questions benchmark/candidate_questions.dense.json
```

The dense set is **not** the default. `candidate_questions.json` still is, so
every number in `docs/handoff.md` §4b and `research/families.md` remains
reproducible; pass `--questions` to use the pooled goldens.
