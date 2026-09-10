# v7 validation — gate readouts

*Every phase gate in `V7-IMPLEMENTATION-PLAN.md` §2 appends its numbers
here. A gate is a number in this file, never a sentence in chat. Append
only; corrections are marked as corrections.*

## 0b — card index `rl/artifacts/cards_v1` (Lane A, 2026-09-10)

Source: Forge pin `670429bf` (2026-08-06) → `data/dataset.jsonl.gz`
(34,519 faces, 7 s) → `rl/cards/build_index.py` (5 s).

| gate | required | measured | result |
|---|---|---|---|
| card faces indexed | ≥ 33,000 | 34,642 (34,519 pin + 123 post-pin overlay; first build the same day read 34,521 with a 2-script overlay) | pass |
| token scripts indexed | resolved via tokenscripts | 836 | pass |
| unknown names across every `.dck` in `rl/` and list in `decks/` | 0 | 0 of 38 decks (1,540 lines) | pass |
| card names shared by >1 card script | (report) | 0 | — |
| faces with a non-zero graph readout | (report) | 34,218 / 35,357 | — |

Caveats recorded in `rl/artifacts/cards_v1/README.md`: 123 cards postdate
the pin (two of them, `Defense Force Aggressor` and `Head of Security`,
are in XMage ladder decks; the rest let 2026 MTGO lists resolve) and come
from Forge `639f8d98` via `rl/cards/extra_scripts/` (its README lists them); token names
are not unique across tokenscripts (bare name → first script,
`token:<script>` is exact); transform back faces carry `mv = null`.

## 1a — embedder data layer `rl/cardemb/data.py` (Lane A, 2026-09-10)

| gate | required | measured | result |
|---|---|---|---|
| ladder cards round-trip the printed channel (`printed_decode(printed_encode(f)) == printed_expected(f)`) | every card in the 38 decks | 491 / 491 distinct deck lines; also 35,478 / 35,478 faces | pass |
| held-out split written to disk | 10 % by name (script-grouped for multi-face) | `rl/artifacts/card_emb_v1/split.json`: 3,532 / 35,478 = 10.0 %, faces of one script never straddle | pass |
| text channel carries no raw number and no self-name | all faces checked (first 5,000 in the unit test) | 0 violations | pass |

Channel dims: text = string (type line + bucketed oracle), printed = 83
floats (`PRINTED_DIM`), graph = 68 floats (`rl/e2_extract.py`).
Test: `python -m pytest tests/test_cardemb_data.py` (5 passed, 5 s).

