# cards_v1 — card index for the v7 shared embedder

Built by `rl/cards/build_index.py` from `data/dataset.jsonl.gz` (Forge pin `670429bf`) and the Forge tokenscripts.

| count | value |
|---|---|
| card faces (ids) | 34642 |
| token scripts (ids) | 836 |
| of which post-pin overlay faces (rl/cards/extra_scripts) | 123 |
| card names shared by >1 card script (Variant/basic reprints) | 0 |
| resolvable names | 37094 |
| name collisions (later face kept) | 801 |

## Decklist gate (plan §2, 0b: 0 unknown)

| deck | cards | unknown |
|---|---|---|
| decks/dimir_deck.txt | 19 | 0 |
| decks/dimir_midrange_v2.txt | 22 | 0 |
| decks/jeskai_deck.txt | 19 | 0 |
| decks/selesnya_deck.txt | 20 | 0 |
| rl/B0Base.dck | 10 | 0 |
| rl/B0Twin.dck | 10 | 0 |
| rl/B1Fast.dck | 10 | 0 |
| rl/B1FastTwin.dck | 10 | 0 |
| rl/B1Narrow.dck | 10 | 0 |
| rl/B2Mid.dck | 10 | 0 |
| rl/B3Open.dck | 10 | 0 |
| rl/B3Twin.dck | 10 | 0 |
| rl/B4Card.dck | 10 | 0 |
| rl/BenchDimir.dck | 22 | 0 |
| rl/E3ScryProbe.dck | 22 | 0 |
| rl/HoldoutBurn.dck | 11 | 0 |
| rl/HoldoutControl.dck | 11 | 0 |
| rl/HoldoutMidrange.dck | 10 | 0 |
| rl/P8Faeries.dck | 19 | 0 |
| rl/P8SwapInteraction.dck | 22 | 0 |
| rl/P8SwapMixed.dck | 22 | 0 |
| rl/P8SwapThreats.dck | 22 | 0 |
| rl/R0Base.dck | 10 | 0 |
| rl/R0Novel.dck | 10 | 0 |
| rl/R0Twin.dck | 10 | 0 |
| rl/W0Base.dck | 10 | 0 |
| rl/W0Twin.dck | 10 | 0 |
| rl/W1Ctrl.dck | 10 | 0 |
| rl/W1Fly.dck | 10 | 0 |
| rl/W1Fst.dck | 10 | 0 |
| rl/W1Lif.dck | 10 | 0 |
| rl/W1Vig.dck | 10 | 0 |
| rl/W2Ctrl.dck | 10 | 0 |
| rl/W2FlyLif.dck | 10 | 0 |
| rl/W3Sorc.dck | 10 | 0 |
| rl/W3Twin.dck | 10 | 0 |
| rl/W4Inst.dck | 10 | 0 |
| rl/W5Trick.dck | 10 | 0 |

**Gate: PASS** — cards ≥ 33000: True; unknown names: 0.

Files: `index.json` (meta + name→id), `oracle.jsonl.gz`, `fields.jsonl.gz` (schema in `index.json.field_schema`). Graph readout = `rl/e2_extract.py` FEATURES (68 cols).

Consumer notes:
- Token names are not unique across tokenscripts (e.g. three `Elemental Token` scripts); a bare token name resolves to the alphabetically first script, `token:<script>` is exact.
- Back faces of transform cards have `mana_cost = null`, `mv = null`; the embedder's data layer decides whether to inherit the front face's.
- Rebuild: `python3 rl/cards/build_index.py` (5 s) after `python3 -m cardguru build ...` (docs/getting-started.md §3).
