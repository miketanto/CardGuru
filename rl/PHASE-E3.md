# Phase E3 — card-advantage visibility, pip structure, and a text-embedding card channel

Action #3 of `rl/CHECKPOINT-PHASE10.md` §4.3, run against the Phase 8b
conclusion that the card channel is **massively load-bearing but read as
local identifiers** (`rl/PHASE8B-CHANNEL.md`). Three feature groups, three
acceptance gates before any training, then a 512-episode from-scratch
pilot and the 8b scramble diagnostic applied per channel.

Everything here is additive: `rl/e2_features.tsv` is untouched, and the
E2 encoder (cdim 91, sdim 24) still runs exactly as before when
`-Drl.cardFeatures` points at the E2 file and the new dims stay zero.

## 1. What shipped

| group | where | dims | what it makes visible |
|---|---|---|---|
| 1 card-advantage visibility | `StateEncoder.encodeState` s[24-28] | 5 | known top of library (flag / land / creature / mana value) + hand differential |
| 2 card semantics | `rl/e3_features.tsv` dims 68-99 | 32 | oracle-text embedding appended to E2's 68 mechanical dims |
| 3 colored-pip structure | `StateEncoder.forCard` c[17-21] | 5 | generic / specific pips / deepest single-colour requirement / distinct colours / flexible symbols |

Encoder dims: **sdim 24 → 29**, **cdim 91 → 123** (= 22 + 68 + 32 + 1).
The pip group costs nothing in cdim: candidate slots 17-21 were already
allocated and unused, so the whole cdim increase is the text block.

### Group 1 — how "known top of library" is knowable

XMage has no persistent model of what a player knows about their own
library, so `RLPlayer` keeps one. It records every card it is *shown*:

- library-zone card choices (`chooseTarget(Outcome, Cards, TargetCard,
  …)` with `Zone.LIBRARY`) — this is exactly how `PlayerImpl.scry` and
  `doSurveil` present the top N;
- `revealCards(…)` — explore reveals the top card;
- `lookAtCards(…)` — every look-at effect.

The encoder then asks one question: *is the card currently on top one of
those?* Drawing it expires the knowledge for free, and `shuffleLibrary`
clears the set (positions are unknown again). Cards put on the **bottom**
by a scry stay recorded — we did see them — which is a real if tiny
over-claim; a 60-card library at ~17 turns/episode never reaches them.

`knownTopWindows` / `encodeWindows` / `seenRecorded` are reported in
every `RL|summary` line, so the new visibility is measurable as a rate
rather than assumed. That instrumentation turned out to matter (§5).

### Group 3 — why mana value is not enough

`c[6]` carries mana value only, so `{U}{U}` and `{2}{U}` are the same
candidate. That is the difference between holding up two blue sources
and holding up any two lands — the whole of hold-open-mana planning.
c[19] (deepest single-colour requirement) is the dim that separates them.

## 2. The text channel

The feasibility spike (`rl/e3_text_spike.py`) reproduces exactly on a
fresh Forge checkout — 33,308 cards with oracle text, Spell Snare /
Force Spike at cosine .259, Cancel / Counterspell at 1.000.

**Neural embedder first, as instructed — it is not reachable.**
`huggingface.co` is denied at the egress proxy (`CONNECT` → 403; the
proxy's own `recentRelayFailures` names the host and the policy denial),
which rules out sentence-transformers, `model2vec`, and every other
HF-hosted checkpoint. PyPI is reachable, but no pip-installable package
carries usable embedding *weights* (spaCy vector models and gensim's
downloader both fetch from blocked hosts). So the spike's validated
offline fallback is what ships: **TF-IDF → truncated SVD → 32 dims**.

`rl/e3_extract.py` builds it:

1. oracle text straight off the Forge cardsfolder, **parenthetical
   reminder text dropped** (keyword restatement, already covered by the
   mechanical keyword dims, and it swamps short rules text) and
   self-references folded to `CARDNAME`;
2. unigrams + bigrams, mana symbols kept coloured, and **numeric
   bucketing** — the spike's explicit finding was that raw TF-IDF put
   Shock / Lightning Strike at .17 because it over-weights "2" vs "3";
3. TF-IDF (sublinear tf, min_df 5) → randomized SVD → 32 dims,
   L2-normalized to a fixed norm so the block is numerically comparable
   to the sparse binary mechanical half;
4. the 68 mechanical dims are **copied verbatim** out of
   `rl/e2_features.tsv`, never re-derived — the only difference between
   the E2 and E3 channels is the appended text block.

35,390 names, 96.3% with oracle text (the rest — tokens, a few renamed
faces — get a silent zero block). SVD signs are pinned, so the file is
byte-reproducible: two runs give the same md5.

Normalization and width were chosen on the gate metrics, not by taste:

| reminder text | CARDNAME | min_df | dims | Snare/Spike | swap-pair min | swap-pair mean | unrelated |
|---|---|---|---|---|---|---|---|
| kept | no | 2 | 40 | .432 | .140 | .503 | .177 |
| kept | yes | 5 | 40 | .358 | .300 | .534 | .177 |
| dropped | yes | 5 | 48 | .589 | .256 | .660 | .137 |
| **dropped** | **yes** | **5** | **32** | **.537** | **.458** | **.706** | **.172** |
| dropped | yes | 5 | 64 | .625 | .178 | .621 | .119 |

Past 32 dims the analog pairs come apart while Snare/Spike drifts *up* —
the ordering the transfer result depends on degrades in both directions
at once, so 32 (the low end of the spike's 32-48 recommendation) is
where this corpus wants to sit.

## 3. Acceptance gates (`rl/e3_gates.py`) — all PASS

Thresholds are referenced to two measured baselines rather than picked
free-hand: **unrelated** cards (random-pair text cosine, mean .177) is
the floor, and the **near-duplicate band** (Cancel/Counterspell,
Murder/Doom Blade, Shock/Lightning Strike, all ≥ .89) is the ceiling.

### G1 — Spell Snare / Force Spike must separate — PASS

| measure | value |
|---|---|
| E2 mechanical distance | **0.000** (literally the same vector) |
| E3 text cosine | 0.521 |
| E3 full-vector distance | 1.957 |

Below the near-duplicate band, below the analog-pair mean (.702), and
almost two full mechanical-dim flips apart, from a starting point where
no policy could tell them apart at all. They stay *related* — both are
one-mana soft counters — which is correct; what E3 buys is that they are
no longer **identical**.

The nearest-neighbour structure shows what the channel actually learned:

- **Force Spike** → Convolute 1.00, Mindstatic 1.00, Quench 1.00,
  Mana Leak 1.00, Mana Tithe 1.00 — the *pay-N-or-be-countered* family;
- **Spell Snare** → Chilling Screech .97, Sound the Trumpets .96,
  Change the Equation .95, Thoughtbind .91 — the *counter-if-mana-value*
  family.

That is condition breadth, which is the thing §4.3 asked for and the
thing 68 mechanical dims cannot express (both cards are `tgt_spell` +
`api_Counter` and nothing else).

### G2 — P8 swap pairs must stay close — PASS

All 16 (out, in) pairs from `P8SwapInteraction` / `Threats` / `Mixed`
(`rl/p8_swap_pick.py` output, tabled in `PHASE8-TRANSFER.md`), whose
E2 near-identity is what produced perfect zero-shot transfer:

| pair | E2 d | E3 text cos | E3 dist |
|---|---|---|---|
| Bitter Triumph / Go for the Throat | 0 | .462 | 2.075 |
| Requiting Hex / Cut Down | 2 | .475 | 2.490 |
| Shoot the Sheriff / Eliminate | 0 | .778 | 1.334 |
| Spell Snare / Dispel | 0 | .675 | 1.612 |
| We Say Thee Nay! / Don't Make a Sound | 0 | .936 | 0.713 |
| Spell Pierce / Stubborn Denial | 0 | .694 | 1.566 |
| Floodpits Drowner / Zephyr Sentinel | 4 | .616 | 2.659 |
| The Wondrous Wasp / Plumecreed Escort | 1 | .481 | 2.270 |
| Spyglass Siren / Faerie Seer | 2 | .789 | 1.920 |
| Elektra / Fathom Fleet Cutthroat | 0 | .775 | 1.341 |
| Bitter Triumph / Easy Prey | 0 | .439 | 2.119 |
| Shoot the Sheriff / Cradle to Grave | 0 | .866 | 1.037 |
| We Say Thee Nay! / Clash of Wills | 0 | .921 | 0.795 |
| Spell Pierce / Concerted Defense | 0 | .838 | 1.138 |
| Spyglass Siren / Faerie Miscreant | 2 | .610 | 2.262 |
| Elektra / Ravenous Chupacabra | 0 | .875 | 0.998 |

min .439, mean .702 — every pair at least 2.5× the unrelated baseline
(gate: ≥ 2× = .354), the group at 4× it.

**Honest limit:** this is not a *strict ordering* gate. Snare/Spike at
.521 sits below the analog mean but above 4 of the 16 individual pairs
(the two Bitter Triumph rows, Requiting Hex / Cut Down, Wondrous Wasp /
Plumecreed Escort). Those four are pairs the E2 graph called identical
while their rules text genuinely differs — "destroy target creature,
you may pay life" vs "destroy target creature with mana value 2 or
less". A text channel that ranked them *above* Snare/Spike would be
lying about the cards. An ordering gate was written first and rejected
for exactly this reason: it would have forced the channel to be blunter
than the cards are.

### G3 — class structure preserved — PASS

| pair | E3 text cos | band | spike (raw TF-IDF) |
|---|---|---|---|
| Cancel / Counterspell | 1.000 | ≥ .70 | 1.000 |
| Shock / Lightning Strike | 0.939 | ≥ .70 | 0.166 |
| Murder / Doom Blade | 0.970 | ≥ .70 | 0.376 |
| Spell Snare / Essence Scatter | 0.542 | .25-.85 | 0.305 |
| Murder / Shock | 0.058 | ≤ .40 | 0.012 |
| Spell Snare / Murder | 0.285 | ≤ .40 | 0.015 |

Numeric bucketing did exactly what the spike predicted: Shock /
Lightning Strike .17 → **.94**, and the cross-class pairs stay near
zero. No collapse: unrelated-pair cosine mean .177, p95 .516.

```
$ python3 rl/e3_extract.py && python3 rl/e3_gates.py
...
ALL GATES: PASS
```

## 4. The 512-episode pilot

_(filled in below)_

## 5. Is the new channel load-bearing?

_(filled in below)_

## 6. Reproduction

```
python3 rl/e3_text_spike.py            # feasibility spike, unchanged
python3 rl/e3_extract.py               # -> rl/e3_features.tsv (dim 100)
python3 rl/e3_gates.py                 # the three gates, exit 0 = pass
bash    rl/e3_pilot.sh 512 0           # from-scratch pilot (sdim 29 cdim 123)
bash    rl/e3_ablate.sh /tmp/rl_e3_s0/e3_pilot_final.pt 200
```
