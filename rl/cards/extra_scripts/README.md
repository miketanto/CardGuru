# Post-pin card scripts (overlay on the Forge pin)

Forge scripts for cards that XMage decks in `rl/` use but that entered
Forge after the dataset pin `670429bf` (2026-08-06). Each file is copied
verbatim from Forge commit `639f8d98` (master, 2026-09-10),
`forge-gui/res/cardsfolder/upcoming/`. `rl/cards/build_index.py` parses
this directory after the dataset and registers the faces with
`file = extra/<script>`.

| script | card | needed by |
|---|---|---|
| defense_force_agressor.txt | Defense Force Aggressor (TRC:161) | rl/R0Novel.dck |
| head_of_security.txt | Head of Security (TRC:133) | rl/W1Fst.dck |

Moving the pin forward makes this directory empty, not wrong.
