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

Takes ~1 minute, writes ~6 MB. The optional `--canonical index.json`
join (Scryfall-derived canonical names) improves name matching but
nothing in the test suite depends on it.

Environment knobs (only needed if paths differ from the defaults):
- `CARDGURU_DATASET` — dataset path (default `data/dataset.jsonl.gz`)
- `CARDGURU_TOKENSCRIPTS` — tokenscripts dir (default
  `/home/user/forge-src/forge-gui/res/tokenscripts`; set this on a new
  machine or token-aware tests/features degrade gracefully)

## 4. Verify

```bash
python -m pytest tests/        # 91 tests; integration goldens auto-skip
                               # if the dataset is missing - build first
python benchmark/run.py        # 20-query golden benchmark
```

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
