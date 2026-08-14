# Rung 0 ceiling test — decision rule, written before the result

The rung-0 agent plateaus at **.782 [.720, .834]** vs D0 (seed 0, 200
games, Wilson 95%), flat from 1919 episodes. The question is whether
that is the game's variance ceiling or the agent's own limit — a mirror
match on identical 60-card decks is decided by opening hand and draw
order some fraction of the time no matter how well either side plays.

This file fixes what each outcome means **before** the number arrives,
because the temptation to read either result as good news afterwards is
obvious.

## The instrument

Players of known, different strength, in the same seat, against the same
D0, on `W0Base`:

| row | strength | status |
|---|---|---|
| D0 vs D0 | symmetric — must return ~.5 | **.460 [.366, .557]**, 0 stalls, 12.9 turns ✅ |
| D1 vs D0 | 1-ply search | **.410 [.319, .508]** |
| CP7 vs D0 | depth-6 alpha-beta, 5000 nodes | **.650 [.524, .758]** (n=60) |

The control passed: symmetric play returns a rate whose interval
contains .5, at the turn count the gate measured (12.9 vs 13.2). The
harness is behaving.

## The rule

Compare CP7's interval to **our agent's [.720, .834]**.

- **Overlaps it** → the strongest AI XMage ships is *not distinguishable*
  from our agent in this seat. The ceiling belongs to the deck.
  **Rung 0 is solved.** Cut the sweep to 3 seeds — enough to state the
  plateau with replication — and move the white branch to rung 1.

- **Lower bound clears .834** → CP7 is strictly better and rung 0 has
  real headroom. **The plateau is ours, not the game's.** Run all 5
  seeds, and rung 0 becomes a question about method (terminal reward, no
  search, a fixed opponent) rather than a rung to be passed.

- **Neither** (interval straddles .834) → not resolvable at n=60.
  Raise n before deciding rather than picking the reading that suits.

## Caveats that apply whichever way it lands

**Seat — this caveat was wrong and is withdrawn.** I worried that our
.782 came from the *agent* seat while CP7 ran in the *opponent* seat,
and read the control's .460/.540 split as a possible seat effect.
`EpisodeRunner` sets `agentOnPlay = (i % 2 == 0)`: **seats alternate
every episode**, so over an even number of games each role gets exactly
half the play draws. There is no seat asymmetry to correct for, in any
row of this table or anywhere else in the project, and the control's
.460 is ordinary sampling noise. Left in rather than deleted because
the pre-registered rule was written under the mistaken version.

**n.** CP7 at 60 games is ±.13 at p=.5. That is wide enough to leave the
"neither" branch genuinely possible, which is why it is written down as
a branch rather than a footnote.

**One seed.** Our .782 is seed 0 alone. If the pooled figure across
seeds moves materially, this test is re-run against the pooled interval,
not quietly kept.

---

## Result: reading A, by the rule as written

```
D0  vs D0    .460 [.366, .557]     control
D1  vs D0    .410 [.319, .508]     1-ply search
CP7 vs D0    .650 [.524, .758]     depth-6 alpha-beta
our agent    .782 [.720, .834]     peak, 1919 episodes
```

CP7's interval **overlaps** our agent's, in `[.720, .758]`. By the rule
above that is reading A: the strongest AI XMage ships is not
distinguishable from our agent in this seat, and **the ceiling belongs
to the deck.** Action taken: sweep cut from 5 seeds to 3, white branch
moves to rung 1 after.

Two things the rule did not anticipate, both worth stating.

**CP7 came back BELOW our agent, not above.** The rule was written
expecting the strong instrument to sit at or above us; it landed at
.650 against our .782. The overlap branch still applies — the intervals
touch — but the direction means our learned agent is, at peak, the
strongest player measured on this deck. That is the first time in this
project an agent has come out ahead of XMage's shipped AI at anything,
and it is on a deck built to be simple.

**This supports the variance-ceiling hypothesis without proving it.**
Nothing we can construct exceeds ~.78, and both search-based
instruments do *worse* than the learned agent. In a low-variance game a
much stronger player should approach 1.0 against a weak one, and
depth-6 alpha-beta with a 5,000-node budget manages .65. That is
consistent with the mirror imposing a real ceiling well below 1.0. It
is not proof: CP7's evaluator (life + permanents + hand size) may
simply be a poor fit for a vanilla-creature mirror, and a genuinely
optimal player might do better. The oracle described in
`CURRICULUM-LADDER.md` §4 — minimax over the no-instants combat
subgame — is what would settle it, and rungs 0-3 are exactly where it
is computable.

## What this does NOT license

`D1 vs D0 = .410` means 1-ply search is **weaker than the heuristic** on
this deck, where on BenchDimir it was the stronger instrument and the
whole Elo ladder is built with D0 at 1000 and D1 above. So "the agent
beat 1-ply search at 512 episodes" is not the Phase 4 bar being cleared.
On W0Base that bar sits below D0. Phase 4 stands.
