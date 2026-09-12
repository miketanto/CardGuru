# Gameplay sample from the 5b recordings (2026-09-12)

Echo policies (`rl/wire_echo_server.py`) on the RL seat against XMage's
heuristic AI, 8 decks x 3 policies x 14 games (rounds 1-2, 336 games).
The policies are deliberate non-players (p1 = first non-pass candidate,
p99 = last candidate, sf = spell-first): they exist to exercise the wire,
not to win.

## Outcomes (games / wins; no per-deck level is claimed under 100 games)

| deck | p1 | p99 | sf | mean turns (p1/p99/sf) |
|---|---|---|---|---|
| W0Base | 14/0 | 14/0 | 14/0 | 11.3 / 12.9 / 11.6 |
| W1Fly | 14/0 | 14/0 | 14/0 | 11.9 / 11.1 / 11.4 |
| W3Sorc | 14/0 | 14/0 | 14/0 | 12.7 / 11.6 / 11.9 |
| W4Inst | 14/0 | 14/0 | 14/0 | 13.1 / 14.4 / 12.6 |
| W5Trick | 14/0 | 14/0 | 14/0 | 11.9 / 11.6 / 11.1 |
| B1Fast | 14/0 | 14/0 | 14/0 | 14.0 / 12.0 / 12.7 |
| BenchDimir | 14/4 | 14/2 | 14/2 | 21.9 / 19.3 / 26.9 |
| P8Faeries | 14/4 | 14/4 | 14/1 | 24.9 / 20.1 / 22.3 |

Pooled per policy, Wilson 95 %: p1 8/112 = 0.071 [0.037, 0.135];
p99 6/112 = 0.054 [0.025, 0.112]; sf 3/112 = 0.027 [0.009, 0.076].
The only wins come from the two decks with flyers and counterspells,
where the heuristic AI cannot block and the game runs 20+ turns.

## Puzzle: 5b_P8Faeries_p1, game 6, turn 32, consult 110 (ATTACK, 18 candidates)

Life: me 20, opponent 7. Opponent: two untapped 1/1 flyers (Spellstutter
Sprite, Spectral Sailor), 2 cards in hand, 10 untapped mana. Me: Restless
Reef 4/4 (tapped), and eight untapped flyers with 12 power in total:
Quickling 2/2 x2, Pestermite 2/1 x2, Faerie Vandal 1/2 x2, Spellstutter
Sprite 1/1, Spectral Sailor 1/1.

Candidate row (WIRE §2f ATTACK, de-normalised):

| k | attackers | damage dealt | their kills | my losses | lethal | opp life after |
|---|---|---|---|---|---|---|
| 1 (chosen by p1) | Spectral Sailor | 0 | 1 | 1 | 0 | 7 |
| 9 | Sailor, Sprite, Pestermite, Vandal | 4 | 2 | 2 | 0 | 3 |
| 13 | Sailor, Sprite, Quickling, Pestermite, Vandal | 6 | 1 | 1 | 0 | 1 |
| 14 | seven of the eight (no second Vandal) | 11 | 0 | 0 | **1** | **-4** |
| 17 | all eight | 12 | 0 | 0 | **1** | **-5** |

Two of the 17 attack subsets are lethal; the first-non-pass policy chose
the single 1/1 (it chose index 1 on all 21 ATTACK consults of the game).
Trajectory: opponent life 20 -> 19 (turn 10) -> 7 (turn 31) -> 2 (turn
40); the game was won on turn 48 with the RL seat at 4 life, sixteen
turns after the first lethal attack was on the wire. This is the kind of
consult the trained policy is meant to get right; the candidate features
already say which row wins.
