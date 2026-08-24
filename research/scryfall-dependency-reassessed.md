# Correction — the grammar never needed Scryfall

**Six of the oracle-grammar notes end with "blocker unchanged: `api.scryfall.com`
is still 403". That framing was wrong on both halves, and this note supersedes
it.** Scryfall is not required for any of the grammar work, and the coverage
argument it was supposed to unblock was never the strong argument anyway.

## Where the oracle text actually comes from

Forge's card scripts carry an `Oracle:` line. `cardguru/forge_parser.py:114`
captures it and `Face.to_record()` writes it into every dataset row. So the
34,519 faces the grammar has been parsing across five cycles — every number in
M0 through cycle 5 — came out of the Forge sparse clone. **No measurement in this
line of work has ever touched Scryfall.**

That is not a workaround; it is the reason the parallel corpus exists at all
(`research/oracle-grammar-m0.md`). Aligned (oracle text, hand-authored graph)
pairs require both to come from the same source.

## What the earlier claim assumed, and why it was wrong

The claim was: the grammar exists to cover cards Forge hasn't scripted; oracle
text for those cards must come from Scryfall; Scryfall is blocked; therefore the
work is preparation rather than delivery.

Two things are wrong with that.

**1. Forge is itself a live, reachable oracle-text feed.** It is on GitHub, and
GitHub works from this environment — that is how the corpus was cloned in the
first place. Measured between the project pin and current master:

| | |
|---|---|
| pin `670429bf` | 2026-08-06 |
| master `d6465382` | 2026-08-24 |
| new card scripts added in 18 days | **92** |
| existing scripts modified | 49 |

Roughly five new cards a day, continuously, from a source that is already
reachable. The window in which a card exists but Forge has not scripted it is
small and self-closing. "Re-pull Forge" is the whole fix.

**2. Coverage was the weak argument all along.** Phase 1 measured Forge at 98.9%
of faces scripted and ≳99% of tournament-playable cards. A grammar that unlocked
the remaining 1.1% would be a rounding error.

The strong argument is the one `research/phase1-cardscripts.md` §6 made and this
work then confirmed with numbers: **rules ontology versus implementation
ontology.** `DB$ ChangeZone` conflates destroy, bounce, tuck and exile; `Pump`
conflates P/T changes with ability grants. Those are Forge's execution
vocabulary, not the rules'.

And the payoff showed up exactly there. Of 15 counterspells where the grammar
called the target restricted and Forge called it unrestricted, **14 were the
grammar being right** — Dispersal Shield, Ertai's Trickery, Hindering Light and
Jaded Response cannot counter any kind of spell, and Forge says `ValidTgts: Card`
only because it implements the condition outside the target selector. That
finding needed no new cards at all.

## What Scryfall is still genuinely wanted for

None of these are grammar blockers, and none belong to the mechanical-search
tier:

- **Format legality.** Forge's cardsfolder has no legality fields, so
  `plan/uncertainties.md` §5's legality-weighted coverage number is still
  unavailable, and any "is this Standard legal" product behaviour needs a real
  source.
- **Official rulings**, for the accuracy spot-check `plan/eval.md` gates on.
- **Card images** — `plan/architecture.md` §5 specifies Scryfall image URIs
  rather than rehosting, for Fan Content Policy reasons.
- **Canonical names and printings.** The build currently joins against a
  vendored MTGJSON-derived index of, in phase 1's own words, "unknown freshness".

Worth noting for whoever picks that up: `raw.githubusercontent.com` returns 200
from this environment while `mtgjson.com` and `api.scryfall.com` do not. A
GitHub-hosted mirror is a plausible route to most of the above without an
allowlist change at all — untested, but cheap to test.

## Consequence for the project's justification

The oracle grammar should be justified as a **second, independent derivation for
fidelity and QA**, not as a coverage tool. Everything measured supports the first
framing:

- 14 of 15 disagreements on counterspell target restrictions resolved in the
  grammar's favour
- the cost/target layer at 94–99% agreement with Forge, usable as a
  cross-derivation check
- `derivation` now stamped on both sides so disagreements are addressable

And nothing measured supports the second, because the second was never tested —
no card outside Forge's pool has been parsed in any cycle.

The six notes that end with the Scryfall line should be read as superseded by
this one. Their measurements are unaffected; only the closing sentence was wrong.
