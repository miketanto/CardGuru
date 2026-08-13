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

Groups 1 and 3 are gated behind **`-Drl.e3=on` (default off)** so this
build still reproduces every pre-E3 phase exactly — see §6.

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

`rl/e3_pilot.sh`: from-scratch `lstmattn`, self-play against its own
snapshot pool, BenchDimir mirror, lr 1e-4, 64-episode chunks, fast path
(persistent driver JVM, `RL_CONC=4`, per-worker policy connections),
~19 episodes/min. No teacher, no BC init — the net starts from random
weights, which is the only way to see whether the E3 input shape trains
at all.

| trained | vs D0 (100g) | vs D1 (100g) |
|---|---|---|
| 256 | .120 | .080 |
| 512 | **.410** | **.230** |
| 512 (200g re-probe) | **.455** | **.240** |

The encoder trains. sdim 29 / cdim 123 negotiates cleanly through the
hello handshake, no stalls in ~2,300 games, and the curve is alive
rather than flat — the 256→512 jump is the usual scratch-line takeoff
(Phase 7b's scratch lstmattn needed 6,144 episodes to reach Elo 1101,
so .455 vs D0 at 512 episodes is on-trend, not a result).

### Matched E2 control arm

`E3_ARM=e2` reruns the identical lane on E2's encoder — same `lstmattn`
arch, same lr, same seeds, same 64-episode chunks, same snapshot-pool
schedule, same deck, same probes — with only the encoder swapped
(sdim 24 / cdim 91, `rl.e3` off). Seed 0, both arms:

| trained | E2 vs D0 | E3 vs D0 | E2 vs D1 | E3 vs D1 |
|---|---|---|---|---|
| 256 (100g) | .100 | .120 | .010 | .080 |
| 512 (100g) | .300 | .410 | .160 | .230 |
| **512 (200g)** | **.280** | **.455** | **.170** | **.240** |

At 200g the D0 gap is **+.175 ± .093** — outside the CI — and the D1 gap
is +.070 ± .081, inside it. The two arms also play differently: the E2
net takes 44.0 actions/ep against E3's 22.7 on 102.8 vs 158.1 consults,
i.e. it acts on a larger share of the windows it sees.

**One seed each, so this is a lead, not a result.** Phase 7b/7c/8b all
found single scratch runs noisy enough to need replication, and the
standing project convention is 5 seeds; a second seed is running (§7).
Read as-is it says the E3 encoder is at least not *worse* to train from
scratch — the honest worry with +32 mostly-uninformative dims and a
wider state vector — and may be learning faster early. It does **not**
say the text channel is why: §5 shows the pilot can lose that block
entirely without a win-rate cost, so any real E3 advantage at this
budget more likely comes from the pip dims (read, §5) or simply from a
wider input layer.

## 5. Is the new channel load-bearing? (`rl/e3_ablate.sh`)

The 8b protocol, applied per channel: corrupt one block of the feature
file (or zero one group of encoder dims) at eval time and re-probe the
pilot net. 200 games vs D0 per condition, BenchDimir, seed 950000,
sequential, a fresh driver JVM per condition (both the feature table and
the ablation masks are read in `StateEncoder`'s static initializer, and
`RLDriverServer` now pins them so a stale warm JVM fails loudly instead
of ignoring the flag).

Two readouts, because at 200g the win-rate CI on a *difference* is
±.10 and a 512-episode net has little headroom:

- **win rate** — the 8b measure;
- **behaviour** — mean relative change across turns/ep, actions/ep,
  consults/ep, blocks declared and flash casts. This needs a null, and
  two are available: a baseline **replicate** (identical config, fresh
  JVM: .460 vs .455, behaviour distance **.010**) and `ablate_top` on
  BenchDimir, which is an *input-identical no-op* there because those
  dims are already zero in every window (behaviour distance **.007**).
  XMage is not bit-deterministic across processes, so **.010 is the
  jitter band** and only movement well above it is a read.

| condition | win rate | Δ | ±95% | behaviour | reading |
|---|---|---|---|---|---|
| baseline (D0) | .455 | — | — | — | reference |
| baseline (D1) | .240 | −.215 | .091 | .113 | — |
| **text_scrambled** | .520 | +.065 | .098 | **.065** | read, no cost |
| **text_zeroed** | .530 | +.075 | .098 | **.070** | read, no cost |
| **mech_scrambled** | .325 | **−.130** | .095 | .209 | read, load-bearing |
| **all_scrambled** | .175 | **−.280** | .087 | .265 | read, load-bearing |
| ablate_top (dark here) | .460 | +.005 | .098 | .007 | null control |
| ablate_hand | .480 | +.025 | .098 | .015 | marginal |
| ablate_pips | .435 | −.020 | .097 | .031 | read, no cost |

Read straight:

1. **The E2 mechanical block is load-bearing at 512 episodes**:
   scrambling it costs −.130 (>1.96σ), and scrambling the whole row
   costs −.280 — the same collapse 8b measured on a fully trained net
   (.640 → .260). The E3 file reproduces the 8b diagnostic, so the
   instrument is intact.
2. **The new text block is READ but not yet load-bearing.** Corrupting
   it moves play 6-7× the jitter band — the net's actions/ep swing from
   22.7 to 25.9 (scrambled) and its consults/ep from 158 to 178
   (zeroed) — but the win rate does not drop; if anything it drifts up
   (+.065/+.075, both inside the CI). After 512 episodes on a single
   deck, 32 semantic dims are input the net has learned to *use* but not
   yet input it *needs*: on the mirror, identifiers suffice, and the
   text block is currently a mild distractor.
3. **The pip dims are read** (.031, 3× the band) at no win-rate cost.
4. **The hand-differential dim is marginal** (.015 vs a .010 band) —
   expected, since `s[2]`/`s[3]` already carry both hand sizes and the
   differential is a linear function of them. It is cheap and it makes
   the card-advantage scoreboard explicit rather than implied; it is not
   doing work yet.

### Group 1 needed its own deck to be testable at all

On BenchDimir the known-top dims are **dark**: `knownTopWindows = 0` out
of 31,624 encode windows over 200 games, and `seenRecorded` is 34 — the
deck's only filtering source is Kaito's surveil, and the pilot never
activates it. That is precisely the observability gap §4.3 describes,
now measured rather than asserted, and it means an ablation on this deck
tests nothing (which is why `ablate_top` serves as the null control).

`rl/E3ScryProbe.dck` (BenchDimir with 3 Islands → Temple of Deceit, so
the land drops themselves scry) makes the group live and proves the
mechanism end-to-end:

| deck | condition | knownTop / encode windows | win rate | behaviour |
|---|---|---|---|---|
| BenchDimir | baseline | 0 / 31,624 (0.00%) | .455 | — |
| E3ScryProbe | baseline | **1,449 / 31,839 (4.55%)** | .480 | reference |
| E3ScryProbe | ablate_top | 0 / 31,821 (0.00%) | .490 | .014 |
| E3ScryProbe | ablate_hand | 1,526 / 31,836 (4.79%) | .485 | .026 |

So the plumbing works — scry lands feed the seat real knowledge of its
next draw in ~4.6% of decisions — and this net does not use it (+.010,
behaviour at the jitter band). It never could have: the pilot trained on
a deck where the signal was constantly zero.

## Verdict

- **All three acceptance gates pass**, and the text channel groups cards
  by the *condition* on their effect (Force Spike with the tax counters,
  Spell Snare with the mana-value counters) — the axis 68 graph dims
  provably cannot express, since E2 gives those two the same vector.
- **The E3 encoder trains from scratch** (.455 vs D0 at 512 episodes)
  and reproduces the 8b scramble collapse, so the channel diagnostics
  transfer to it unchanged.
- **The new dims are read but not yet load-bearing.** Text: 6-7× the
  jitter band in behaviour, no win-rate cost. Pips: 3×, no cost. Hand
  differential: marginal. Known-top: verified live at 4.6% of decisions
  on a deck that filters, unused by this net.
- That is the *expected* result at this budget, and it is exactly the
  8b story from the other side: on one deck, identifier-style use of the
  mechanical block is sufficient, so semantic dims cannot pay yet.
  **E3 should be A/B'd where 8b said the mechanism lives — deck
  diversity from initialization** (the Phase 10 flagship), not on the
  BenchDimir mirror. What this session establishes is that the channel
  is correct, gated, reproducible, cheap, read by the net, and safe to
  put in that run.

### What would settle it

1. Matched E2-vs-E3 arms inside the Phase 10 flagship (deck diversity
   from episode 0, gated PFSP league), rated on the mirror + the 7c
   robustness matrix. That is where "condition breadth" can pay.
2. Re-run this battery on the flagship's champion: the same table on a
   .60+ net has the headroom for a −.10 text-scramble effect to show.
3. Group 1 needs a deck that filters (P8Meta/archetype pools have scry
   lands and surveil) — or Kaito activation to emerge. Its 4.6%
   live-window rate on E3ScryProbe is the instrument for that.
4. Everything here is one seed. 5-seed replication remains the standing
   project gate for conventions.

### Honest limits

- 200g per condition: only |Δ| > ~.10 is claimable, and the pilot's
  .455 leaves limited room below.
- The behaviour readout is a *sensitivity* measure, not a *usefulness*
  measure: it proves the dims reach the policy's output, not that they
  help.
- No matched E2 arm was trained at 512 episodes, so no E3-vs-E2 claim is
  made anywhere in this document.
- The 512-episode pilot is a single from-scratch seed on one deck.

## 6. Reproduction

Setup is the standard spawn kit (XMage pin `7554968c` +
`rl/engine-patches/phase9-engine.patch`, overlay `rl/xmage-src/` and
`benchmark/xmage/src/`, `mvn -pl Mage.Tests -am install -DskipTests`,
decks copied into `Mage.Tests`), plus a Forge checkout for the oracle
text (`git clone --depth 50 https://github.com/Card-Forge/forge.git
~/forge-src`) and `pip install torch scikit-learn`.

```
python3 rl/e3_text_spike.py            # feasibility spike, unchanged
python3 rl/e3_extract.py               # -> rl/e3_features.tsv (dim 100)
python3 rl/e3_gates.py                 # the three gates, exit 0 = pass
bash    rl/e3_pilot.sh 512 0           # from-scratch pilot (sdim 29 cdim 123)
bash    rl/e3_ablate.sh /tmp/rl_e3_s0/e3_pilot_final.pt 200

# the two controls the battery is read against
E3_OUT=/tmp/rl_e3_ablate_rep  E3_CASES="baseline" \
    bash rl/e3_ablate.sh /tmp/rl_e3_s0/e3_pilot_final.pt 200
E3_OUT=/tmp/rl_e3_ablate_scry E3_DECK=E3ScryProbe.dck \
    E3_CASES="baseline ablate_top ablate_hand" \
    bash rl/e3_ablate.sh /tmp/rl_e3_s0/e3_pilot_final.pt 200

python3 rl/e3_ablate_report.py /tmp/rl_e3_ablate/results.txt \
    --null /tmp/rl_e3_ablate_rep/results.txt
python3 rl/e3_ablate_report.py /tmp/rl_e3_ablate_scry/results.txt --band 0.010
```

Using the channel in a lane: `-Drl.e3=on
-Drl.cardFeatures=rl/e3_features.tsv` with `policy_server.py --sdim 29
--cdim 123`.

**The hand-built groups are behind `-Drl.e3=on`, default OFF.** Both of
them would otherwise silently invalidate every frozen instrument on this
build: group 1 changes sdim 24 → 29, and group 3 fills candidate slots
17-21 that were always zero for every checkpoint the project has trained
(ck_6144, attn_desp, e0_champ, the scripted ladder's comparability).
With the flag off this encoder is byte-identical to the pre-E3 one, so a
Phase ≤10 lane runs unchanged on the same jar. `RLDriverServer` pins
`rl.e3` alongside `rl.cardFeatures`, so a warm JVM cannot serve a job
under the wrong encoder — it refuses the job instead.

The flag was added after the numbers above were collected, so the
baseline was re-measured through it: **.455 win rate, turns 20.1,
actions 22.7** against the original .455 / 20.1 / 22.7 (consults 158.4
vs 158.1, blocks 243 vs 244, flash 567 vs 562 — all inside the .010
jitter band). The gated path is the path that was measured.
