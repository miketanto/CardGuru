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
| D1 vs D0 | 1-ply search | pending |
| CP7 vs D0 | depth-6 alpha-beta, 5000 nodes | pending |

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

**Seat.** Our agent's .782 is measured in the *agent* seat; CP7 runs in
the *opponent* seat with the rate inverted. The control says the
opponent seat scored .460, i.e. the agent seat scored .540 — inside
noise, but if it is real it means CP7's number is mildly *understated*
and the comparison is conservative in the direction that matters.

**n.** CP7 at 60 games is ±.13 at p=.5. That is wide enough to leave the
"neither" branch genuinely possible, which is why it is written down as
a branch rather than a footnote.

**One seed.** Our .782 is seed 0 alone. If the pooled figure across
seeds moves materially, this test is re-run against the pooled interval,
not quietly kept.
