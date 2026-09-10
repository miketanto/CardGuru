# v7 validation — gate readouts

*Every phase gate in `V7-IMPLEMENTATION-PLAN.md` §2 appends its numbers
here. A gate is a number in this file, never a sentence in chat. Append
only; corrections are marked as corrections.*

## 0b — card index `rl/artifacts/cards_v1` (Lane A, 2026-09-10)

Source: Forge pin `670429bf` (2026-08-06) → `data/dataset.jsonl.gz`
(34,519 faces, 7 s) → `rl/cards/build_index.py` (5 s).

| gate | required | measured | result |
|---|---|---|---|
| card faces indexed | ≥ 33,000 | 34,521 (34,519 pin + 2 post-pin overlay) | pass |
| token scripts indexed | resolved via tokenscripts | 836 | pass |
| unknown names across every `.dck` in `rl/` and list in `decks/` | 0 | 0 of 38 decks (1,540 lines) | pass |
| card names shared by >1 card script | (report) | 0 | — |
| faces with a non-zero graph readout | (report) | 34,218 / 35,357 | — |

Caveats recorded in `rl/artifacts/cards_v1/README.md`: two cards
(`Defense Force Aggressor`, `Head of Security`, set TRC) postdate the pin
and come from Forge `639f8d98` via `rl/cards/extra_scripts/`; token names
are not unique across tokenscripts (bare name → first script,
`token:<script>` is exact); transform back faces carry `mv = null`.

