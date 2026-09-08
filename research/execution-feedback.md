# Execution feedback in the compile loop: what fired, what didn't

Follows `docs/handoff.md` §4 ("the retry loop never executes the query") and
`research/agent-compiler-round2.md`, which measured the plain zero-result signal
at 18/20 → 19/20 with no goldens leaked. Round 2 established that the signal
works; this note is about which *version* of it is safe to wire into production.

Two candidate signals were built, then measured against the 37 hand-vetted
reference queries in `benchmark/compiled_questions.json` — queries known to
satisfy their goldens. The question each measurement answers is **how often does
this signal complain about a query that is already right?** A signal with a high
false-positive rate does not merely waste calls; it spends retries arguing a
correct query into a worse one.

Method: replay each reference query through the live compile path with a stub
client that re-emits it, and count checker verdicts. (`--source reference` in
`benchmark/eval_compile.py` scores the same queries but skips the loop.)

## 1. Zero results → per-clause diagnosis. Shipped, default on.

`diagnose` executes every branch independently and marks branches that are empty
*on their own* while sitting inside an `all`. Six of the seven failures in the
handoff were one bad conjunct inside an `all`, so the tree names the culprit
instead of making the model re-guess the whole query.

| | |
|---|---|
| complains about known-good queries | **0 / 37** |
| API calls for 37 questions | **37** (no overhead) |

A query that returns nothing is unambiguously not an answer, so this needs no
threshold. Nothing was invented to make it work.

## 2. Over-narrow parameter → relaxation ranking. **Measured and rejected.**

`near_misses` drops one parameter predicate at a time and ranks by how much
relaxing it unlocks, on the theory that the parameter doing nearly all the
filtering is the over-narrow one. At its shipped ≥2× threshold:

| | |
|---|---|
| complains about known-good queries | **24 / 37 (65%)** |
| API calls for 37 questions | **61** (+65%) |

Raising the threshold does not fix it, and that is the substantive finding.
Maximum single-parameter unlock ratios on **known-good** queries:

| ratio | query | base → reachable |
|---:|---|---|
| 267× | `sac-outlet-that-refills` | 5 → 1,338 |
| 206× | `global-untap-denial` | 166 → 34,125 |
| 123× | `exile-from-graveyard-as-cost` | 277 → 34,125 |
| 58× | `sacrifice-artifact-as-cost` | 147 → 8,526 |
| … | median of the 24 | 10.6× |

The real defect it was built for — handoff #7, `ChangeType` filtered on the
category word `"Land"` when Forge writes `"Plains,Island"` — measures **61×**
(1 → 61 cards). That is *below* three known-good queries. **No threshold
separates them**, and in hindsight that is the expected result: a correct
precise predicate is supposed to do most of the filtering.

The ranking is kept for the human-facing diagnosis (`serve` already shows it on
a suspiciously small result, which is what it was built for). It triggers
nothing automatically.

## 3. Dead predicate → the part of the same computation with no judgement in it

The one thing `near_misses` computes that carries no opinion: whether a
predicate matches **none** of the values its parameter actually takes among
reachable cards. That is wrong the way an out-of-ontology token is wrong.

| | |
|---|---|
| complains about known-good queries | **0 / 37** |
| API calls for 37 questions | **37** |

Mostly subsumed by signal 1 — a dead predicate usually zeroes its own clause —
but not always. Under an `any`, a dead branch is silent, and `DSL_SPEC` actively
encourages `any` ("query both when unsure"), so a dead branch costs recall with
no symptom at all. Available as `--signals full`; not the default, because its
value on live compiles is unmeasured and it costs up to 6 extra corpus scans per
accepted query.

## What this cost, and the general lesson

The over-narrow trigger looked obviously right — the handoff names `near_misses`
as computing "exactly the right signal", and it does compute the right
*explanation*. What it does not carry is a decision boundary. The threshold that
made it useful for a human reading a diagnosis (≥2×, so the list isn't noise)
is 30× too loose to gate a retry, and no value of it works.

This is the same failure the last session's lesson names from the other side:
don't add a convention where a fact could be mined. Here the fact could not be
mined — the reference set says the boundary does not exist — and the honest move
was to drop the signal rather than pick a number that looked reasonable.

## Not built: "suspiciously many results"

The handoff lists two such failures (1,170 and 4,470 hits). Both came from
`similar.py`'s signature ranking rather than this compiler, and by the same
argument as §2 no "too broad" threshold survives contact with the reference set —
`global-untap-denial` legitimately returns 166 and `activate-repeatedly-no-tap`
2,307. Left out until there is something to derive it from.

## Reproducing

```bash
python benchmark/eval_compile.py --source reference    # 36/37, no API key needed
python benchmark/eval_compile.py --signals off         # live A/B arm: validate-only
python benchmark/eval_compile.py --signals zero        # live A/B arm: + execution
```

`--signals` is part of the compile cache key, so the arms never serve each
other's cached answers.
