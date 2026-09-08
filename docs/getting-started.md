# Getting started on a fresh machine

Goal: get the mechanical search tool (and the analysis commands built on
it) running from a clean clone. Everything is stdlib-only Python 3.11+ —
no pip installs needed for the core; `pytest` is the only dev dependency.

## 1. Clone and check out the working branch

```bash
git clone <this-repo>
cd CardGuru
git checkout claude/mtg-rules-search-feasibility-05siv8   # or main after merge
```

## 2. Get the ontology source (Forge card scripts)

The dataset is NOT in the repo (`/data/` is gitignored) — it is built
from Forge's cardsfolder, which is the ontology this whole project mines.

```bash
git clone --depth 50 https://github.com/Card-Forge/forge.git ~/forge-src
cd ~/forge-src && git checkout 670429bf   # the pin all research was done against
```

Only two directories matter:
- `forge-gui/res/cardsfolder/` — 34.5k card scripts (parser input)
- `forge-gui/res/tokenscripts/` — token definitions (used by the
  answer-finder's ability-removal reasoning; optional but recommended)

## 3. Build the dataset

```bash
cd CardGuru
python -m cardguru build \
    --cardsfolder ~/forge-src/forge-gui/res/cardsfolder \
    --pin 670429bf \
    --out data/dataset.jsonl.gz
```

Takes ~5 seconds, writes ~6 MB. The `--canonical index.json` flag is the
older MTGJSON-derivative name join and is superseded by the Scryfall card
store in step 3b — skip it.

Environment knobs (only needed if paths differ from the defaults):
- `CARDGURU_DATASET` — dataset path (default `data/dataset.jsonl.gz`)
- `CARDGURU_TOKENSCRIPTS` — tokenscripts dir (default
  `/home/user/forge-src/forge-gui/res/tokenscripts`; set this on a new
  machine or token-aware tests/features degrade gracefully)

## 3b. Build the Scryfall card store (the attribute tier)

Needs network access to `api.scryfall.com` / `data.scryfall.io`. Downloads the
`oracle-cards` bulk file (~24 MB gzipped) and builds a SQLite store (~115 MB):

```bash
python -m cardguru cardstore --download
python -m cardguru join            # match report, writes data/join_report.json
```

The store is a *separate artifact* from `dataset.jsonl.gz` on purpose: Forge
and Scryfall refresh on different cadences, and `forge_commit` /
`oracle_data_date` are independent axes of the version tuple
([architecture §4](../plan/architecture.md)). Nothing in the graph-search path
requires the store — `CardStore.open()` returns `None` when it is absent and
callers degrade gracefully.

Current join rate against pin `670429bf`: **99.83%** (34,461 / 34,519 faces).
The 58 unmatched faces are left unjoined and labeled, not aliased:

| class | n | why |
|---|---|---|
| `alchemy-rebalance` | 17 | `A-<name>` is a mechanically *different* card; inheriting the paper card's oracle text would be wrong |
| `absent` | 41 | Universes Beyond names Scryfall lists under their Universes Within counterpart, plus cards from the upcoming-set branch the Forge pin tracks |

`data/aliases.json` is optional and empty by default. Only rows with
`status: "confirmed"` are ever applied; `cardguru join --resolve-misses`
generates *candidates* from Scryfall's fuzzy endpoint for human review, and
that endpoint returns near-name false positives (`Drake Stone` → `Stone
Drake`), so nothing is auto-applied.

## 4. Verify

```bash
python -m pytest tests/        # 120 tests; integration goldens auto-skip
                               # if the dataset is missing - build first
python benchmark/run.py        # 20-query golden benchmark
```

## 4b. Try it in a browser

```bash
python -m cardguru serve
```

Then open <http://127.0.0.1:8000>. Loads the index once (~0.6 s) and answers
from memory, so queries return in milliseconds.

- **Question library** — the compiled benchmark questions
  (`benchmark/compiled_questions.json`), click to run. Rows marked `partial`
  show what the query does *not* capture, rather than pretending to be a
  complete answer.
- **Query box** — hand-written DSL, validated against the ontology before it
  runs; rejects name the offending token.
- **English box** — needs `ANTHROPIC_API_KEY`. Without it the box is disabled
  and says so; everything else still works.

Bound to `127.0.0.1` deliberately: it is an unauthenticated query endpoint.

**Debugging an empty result.** A query returning 0 cards is the least
informative answer possible, so it explains itself: every branch is re-run
independently and the clause responsible is named.

```bash
python -m cardguru serve --verbose   # logs each query, the compiled DSL, and the diagnosis
```

```
all                                                          0
  node api="Counter"                                       514
  card types contains "Blue"                                 0  <- KILLER (zero, inside an all)
```

A single zero-hit branch inside an `all` forces the whole query to zero no
matter how healthy the rest is — that is the common failure and it is
invisible without this. When *no* branch is empty but the result still is, the
diagnosis says so instead: the clauses are individually fine and simply never
describe the same card.

**Two Forge field traps this exists to catch.** `types` is only the type line
(`Instant`, `Creature Human Wizard`) and never contains a color; colour lives
in `manaCost` (`U U`, `1 U`). And mana value is not numerically comparable —
`manaCost` is a plain string with no `cmc` field and no `<=` operator.

## 5. Use the tools

```bash
# mechanical search (the core product)
python -m cardguru search queries/q1_combat_damage_token.json --explain
python -m cardguru show "Enduring Curiosity"

# NL -> DSL compiler (needs ANTHROPIC_API_KEY; uses claude-opus-5)
python -m cardguru ask "sagas whose chapters tutor a card onto the battlefield"

# analysis layer built on the graph
python -m cardguru answers "Kaito, Bane of Nightmares"
python -m cardguru windows "Combustion Technique"
python -m cardguru threats "Kaito, Bane of Nightmares" --list decks/dimir_deck.txt
python -m cardguru fingerprint --list decks/jeskai_deck.txt
python -m cardguru gaps --top 20

# commander synergy — color identity comes from the card store (step 3b);
# --ci-index is optional now, needed only for the printing-count prior
python -m cardguru recommend "Teysa Karlov"
```

## 6. Optional: engine adjudication (not needed for search)

Scenario receipts run inside an XMage checkout (pin 1.4.60, master
2026-08-06): drop `driver/CardGuruScenarioRunner.java` into
`Mage.Tests`, then `python -m cardguru adjudicate scenarios/...json`.
See [scenario-spec.md](scenario-spec.md). Skip this entirely until you
need engine-verified claims.

## 7. Where to take the search tool next

Priorities if search is the first product surface (see
[../plan/roadmap.md](../plan/roadmap.md) and
[../plan/architecture.md](../plan/architecture.md) for the full picture):

1. **NL compiler hardening** — the validate/retry loop is tested
   offline; widen the compiled-query eval set (`eval/nl_questions_*`)
   and keep the RulesGuru corpus frozen (do not burn eval IDs —
   `eval/rulesguru_burned_ids.json`).
2. **Serve it** — the index loads in ~2 s and queries run in ms; a thin
   HTTP wrapper around `SearchIndex` + the DSL evaluator is enough for a
   first UI. Evidence spans (`--explain`) are the differentiator: always
   return them.
3. **Dataset refresh discipline** — rebuilds are pinned
   (`--pin <forge-sha>`); treat a Forge bump as a versioned data release
   and rerun the benchmark + goldens before shipping it.
