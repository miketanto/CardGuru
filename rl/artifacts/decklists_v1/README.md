# decklists_v1 — decklist corpus for deck-context pretraining (v7 L1)

Built by `rl/decklists/build_corpus.py` from `raw/mtgo/*.json` (`rl/decklists/fetch_mtgo.py`, mtgo.com published event decklists) plus the repo's own lists. Card ids index `cards_v1`.

| count | value |
|---|---|
| events fetched | 583 |
| lists, total | 13085 |
| lists, unique mainboards | 8430 |
| **unique constructed lists with every name resolved (the gate)** | **8035** |
| of which held out (10%, by event) | 845 |
| mainboard card slots unresolved | 757 / 512439 (0.15%) |
| distinct unresolved names | 31 (top in `unresolved.tsv`) |

## Per format (unique lists)

| format | lists |
|---|---|
| modern | 3027 |
| pauper | 1336 |
| legacy | 1152 |
| standard | 1045 |
| pioneer | 635 |
| premodern | 587 |
| vintage | 465 |
| duel-commander | 108 |
| xmage-ladder | 37 |
| pioneer-rc | 21 |
| modern-rc | 14 |
| limited-rc | 3 |

**Gate 0c: GO** — 8035 ≥ 3000: True. Masked-card-in-deck (1c, 2b) is in.

Fields: see the module docstring of `rl/decklists/build_corpus.py`. `constructed` = 60–80-card, non-singleton format; `clean` = constructed and fully resolved. Player handles are not stored.
