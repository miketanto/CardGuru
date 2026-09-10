# decklists_v1 — decklist corpus for deck-context pretraining (v7 L1)

Built by `rl/decklists/build_corpus.py` from `raw/mtgo/*.json` (`rl/decklists/fetch_mtgo.py`, mtgo.com published event decklists) plus the repo's own lists. Card ids index `cards_v1`.

| count | value |
|---|---|
| events fetched | 1008 |
| lists, total | 21654 |
| lists, unique mainboards | 13354 |
| **unique constructed lists with every name resolved (the gate)** | **12612** |
| of which held out (10%, by event) | 1236 |
| mainboard card slots unresolved | 1229 / 815512 (0.15%) |
| distinct unresolved names | 35 (top in `unresolved.tsv`) |

## Per format (unique lists)

| format | lists |
|---|---|
| modern | 4788 |
| standard | 1903 |
| pauper | 1868 |
| legacy | 1828 |
| pioneer | 1032 |
| premodern | 820 |
| vintage | 763 |
| duel-commander | 263 |
| xmage-ladder | 36 |
| modern-rc | 30 |
| pioneer-rc | 20 |
| limited-rc | 3 |

**Gate 0c: GO** — 12612 ≥ 3000: True. Masked-card-in-deck (1c, 2b) is in.

Fields: see the module docstring of `rl/decklists/build_corpus.py`. `constructed` = 60–80-card, non-singleton format; `clean` = constructed and fully resolved. Player handles are not stored.
