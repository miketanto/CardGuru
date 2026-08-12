# Phase 5 C4 (user-directed) — is open-mana timing worth anything here?

## The insight under test

The v3 transcripts showed every seat deploying flash spells at its own
upkeep, never at the opponent's end step: the greedy evaluator taps out
each turn, and nothing in the stack can price "untapped mana + card in
hand" above "the same card on the battlefield." The user's hypothesis:
the evaluator is a bad TIMING teacher, and open-mana play is learnable
value being left on the table.

## Stage 1: measure the value before teaching it

`SearchPlayerHold` (D1h) — the draw-go pole. Identical to D1 except
flash/instant-speed cards are NEVER cast at sorcery speed: the search
candidate list and the D0 fallback both hold them, so the mana stays
open and the v3 instant-speed branches (opponent end step, counters,
ninjutsu) fire with mana available. One flag, both decision layers.

## Result (500g each, BenchDimir mirror, seed block 960000)

| match | win rate | reference |
|---|---|---|
| **D1h vs D1** | **.504 (CI [.46, .55])** | dead even |
| **D1h vs D0** | **.596 (CI [.55, .64])** | D1 vs D0 = .614 — indistinguishable |

Zero stalls anywhere; node counts normal (2.8/decision).

## VERDICT: draw-go timing is worth ~0.000 against this opposition —
## and the reason matters more than the number

Holding mana pays through two channels, and BOTH are dead here:

1. **Information**: you see the opponent's turn before committing. But
   a 1-ply materialist search cannot USE information — its instant-
   speed choices score the same material sum either way.
2. **Threat of interaction**: represented mana changes how a thinking
   opponent plays. But D0 and D1 do not model the opponent's held mana
   AT ALL — they play identically into open blue mana as into a
   tapped-out board. There is nobody to bluff.

So the greedy deploy-at-first-window line is not a mistake against
this ecosystem - it is optimal-enough, because no opponent punishes
tapping out and none respects held mana. The user's insight about the
evaluator is CONFIRMED (it structurally cannot represent option
value), but the missing term has no cash value until the opposition
adapts.

## Consequence for "teaching open mana" (stage 2 - awaiting decision)

- Teaching students the timing (D1h as BC teacher, or option-value
  shaping Φ) CANNOT show up as win rate vs D0/D1 - stage 1 just
  measured that ceiling at zero. It would optimize a behavior with no
  reward gradient against the available graders.
- The timing becomes value-bearing only against opponents that react
  to held mana: self-play/league (students punishing each other's
  tap-outs is exactly how the behavior gets priced), or a search
  opponent whose evaluator penalizes acting into open mana (an
  evaluator-v2 instrument).
- Cheap intermediate if desired: an exploit probe - a scripted
  opponent that sandbags its best spell whenever the agent is tapped
  out, to measure how exploitable the greedy line is in principle
  (upper-bounds what an adaptive league would extract).

Stage 2 not started, per instruction. Options for the decision:
(a) accept the null and archive C4 here; (b) build the exploit probe
(one scripted player + 500g, ~1h) to measure the latent vulnerability;
(c) go straight at the real fix - self-play league where timing can
earn its value (Track B, the big build).
