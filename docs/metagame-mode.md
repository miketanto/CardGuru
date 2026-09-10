# Meta Lab meta-deck mode

Sideboard planning against a real metagame, rather than against a single card.
This is the surface `plan/product.md` listed as blocked on "meta decklists from
MTGGoldfish/Melee — network-gated". It is unblocked because MetaSurf supplies
the data instead of an aggregator.

## The pipeline

```
MetaSurf                                        CardGuru
────────                                        ────────
MTGODecklistCache -> Postgres
  rules classifier -> archetype labels
  scripts/export_meta.py ──► meta.json ──►  cardguru metagame
    - archetype + meta share                  - key threats per archetype
    - centroid-representative decklist          (centrality + enabler weight)
    - card play-rate prior                    - find_answers per threat
                                              - weight by meta share
                                              - greedy N-slot sideboard
```

Neither repo imports the other. The contract is one JSON file.

## Producing the snapshot (MetaSurf)

```bash
python scripts/export_meta.py --start 2025-05-01 --end 2025-06-09 \
    --top 12 --out meta-modern.json
```

The representative decklist is the deck **closest to its archetype's centroid**
over the window, not the most recent or the best-finishing one: the typical
list is what a mechanical "what does this deck do" reading should see.

## Consuming it (CardGuru)

```bash
python -m cardguru metagame --meta meta-modern.json --colors WU \
    --on-board --slots 15 --json plan.json
```

- `--colors` restricts candidates to your colors
- `--on-board` drops stack-only answers (counterspells) — see the saturation
  limitation below
- `--any-card` disables the play-rate prior (mechanical-only; noisy by design)

## What the play-rate prior is for

`plan/product.md` §4 already identified the gap: *"the ranking model is
`mechanical-fit × card-quality prior` … mechanics propose, popularity
re-ranks — never the reverse."* This is that prior.

Without it the ranking is unusable, and the reason is structural: mechanically,
**every bounce spell ever printed answers every creature**. Measured on the
Modern snapshot, the unfiltered WU top-5 was `Erode`, `Pongify`,
`Rapid Hybridization`, `Alchemist's Retrieval`, `Banishing Knack` — a tie
between cards nobody has ever sleeved. With the prior, the same query returns
`Static Prison`, `Into the Flood Maw`, `Portable Hole`, `Leyline Binding`.

The prior is a **format-legality and viability filter first**, a ranking signal
second. It is circular by construction (popular cards stay popular), which is
exactly why it may only re-rank and never propose: the graph decides what
*works*, the prior decides what is *real*.

## Two limitations, stated

**1. The coverage metric saturates.** A counterspell answers every threat in
the field, so every catch-all ties at the maximum coverage and the ordering
below the tie is carried entirely by play rate. `--on-board` is a partial
remedy — it separates "I can stop this" from "I can deal with this once it has
resolved", which is usually the question a sideboard slot is answering — but
the metric still cannot rank among genuine catch-alls. Fixing this properly
needs a notion of answer *cost* and *timing*, not just whether an answer exists.

**2. Key-threat selection skews toward mana.** `analyze_opponent` weights
enablers (mana amplifiers, ramp engines, cost reducers) by how many later drops
they unlock, so `Utopia Sprawl` and `Talisman of Impulse` surface as Eldrazi's
top "threats". That is a defensible read — killing the accelerant does collapse
the curve — but it is not what a player would name first, and it pushes the
answer search toward artifact/enchantment removal.

## Not modelled

Matchup win rates (answering a threat is not winning the matchup), mana costs
and curve fit, how many copies to run, and what comes *out* when you sideboard
in. This ranks mechanical answer coverage weighted by metagame share, and
nothing more.

## A note on `all_answers` vs `answers`

`analyze_opponent`'s `surgical[i]["answers"]` is a **5-card display list**
sorted by `_playable_key` (spells first, then cheapest). Anything that ranks or
aggregates must use `surgical[i]["all_answers"]`, which is untruncated —
consuming the display list silently biases results toward one-mana filler.
`tests/test_metagame.py::test_ranking_uses_untruncated_answer_sets` guards this.
