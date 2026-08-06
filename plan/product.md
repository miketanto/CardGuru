# CardGuru — customer-facing product design

Everything below is grounded in capabilities that already run in this repo. Where a surface
needs data or infrastructure we don't have yet, that dependency is called out explicitly.

## The through-line

Every competitor is either a **text search** (Scryfall), a **co-occurrence statistic**
(EDHREC: "people who play X play Y"), or a **language model guessing** (judgebots). CardGuru's
differentiation on every surface is the same sentence: *it knows what cards actually do,
structurally, and it can prove claims by executing them.* Every recommendation, verdict, and
answer ships with a machine-readable WHY — the matched subgraph, the computed interaction, or
an engine-executed scenario — never "trust me."

## Surfaces

### 1. Omnibar search (the front door)
One input, three query tiers routed automatically (architecture §2): attribute queries hit the
Scryfall-compatible layer; mechanical queries compile NL → query DSL (validated against the
ontology, shown to the user before running — the compiled query is a *feature*, teaching power
users the DSL); interaction questions route to the adjudicator. Results show "why it matched"
chips rendering the matched trigger→effect chain in plain English.

*Status: DSL + compiler + validation built; needs LLM credentials for NL and a web frontend.*

### 2. Card page
For any card: oracle text and printings (Scryfall data), the **ability graph rendered as a
diagram** (trigger → effect chains — genuinely novel; no site shows card structure), CR
citations per ability (from `cr_mapping`), verified interactions from the corpus that involve
this card, and implementation status (engine-verifiable / unfinished / unimplemented) so
adjudication expectations are set before asking.

*Status: all data exists; needs frontend.*

### 3. Judge (the adjudicator)
Board-state builder (drag cards into zones — internally builds the scenario JSON) plus NL
input compiled to scenarios. Output: final state, step-by-step game log, CR citations, and the
trust label — **Simulated** (engine-executed, XMage version shown) / **Best-effort** (engine
couldn't run it; retrieval-only answer with visible uncertainty). The Lindblum session showed
the fallback path working: unfinished card → partial verification via substitute scenario +
rules citations, labeled as such.

*Status: scenario spec/driver/citations built; NL compilation needs credentials; frontend needed.*

### 4. Commander Workbench (the growth product)
**Why this wins vs EDHREC:** co-occurrence can only recommend what's already popular — it's
circular (popular cards get recommended, staying popular), collapses for new commanders
(day-one sets have no data), and can't explain itself beyond "78% of decks run this."
CardGuru's engine reads the commander's ability graph, detects **synergy hooks** (what it
does), and runs complement queries (what connects to it), each with a mechanical WHY.

Prototype results (`cardguru recommend`, built this session):

- **Rhys the Redeemed** → hook `makes_tokens` → token-doubling (Anointed Procession, Divine
  Visitation — 19 in-color), anthems (67), token payoffs.
- **Oloro** → hook `gains_life` → 66 in-color lifegain payoffs (Ajani's Pridemate, Archangel
  of Thune).
- **Teysa Karlov** → hooks `amplifies_death_triggers` + `buffs_tokens` → 696 death triggers,
  209 sac outlets, 1,295 token makers. (Her hook is a `Panharmonicon`-mode static — the graph
  understands trigger-doubling *as a mechanic*, which co-occurrence fundamentally cannot.)

Product shape:
- **Deck analysis**: paste a decklist → hook coverage matrix (which synergy axes the deck
  commits to; where it's thin), interaction-class curve (targeted removal / sweepers /
  counters / recursion counts vs format baselines), and *verified combo lines* — card pairs
  in-deck whose interaction exists in the scenario corpus, badge-linked to the engine run.
- **Recommendation feed**: per hook, ranked complements with WHY strings ("Cathars' Crusade
  triggers once per token entering; Rhys's activation makes 1–20 tokens").
- **Day-one coverage**: new set drops → Forge scripts land → recommendations exist
  immediately, before any human has built a deck. This is a structural moat vs EDHREC.
- **Honest layering (v2)**: mechanical synergy is necessary but not sufficient (it can't rank
  *power*). The ranking model is `mechanical-fit × card-quality prior`, where the quality
  prior comes from play data (EDHREC rank / winrates) when available. Mechanics propose,
  popularity re-ranks — never the reverse.

*Status: hooks + complements + color identity + CLI built. Needs: more hook types (~20 covers
the common archetypes), ranking prior, decklist parser, frontend.*

### 5. Meta Lab (sideboard answers) — feasibility TESTED, works
Input: a threat (or a meta deck list). Output: an **answer matrix** — for each answer class
(targeted destroy/exile/damage/-X-X/edict/bounce/sweeper/counter), which cards in your colors
*actually work*, with the blocking reason when they don't:

Real output from this session (`cardguru answers`):

- **Sheoldred, the Apocalypse**, red answers: only **97/543** damage spells kill her
  (Lightning Bolt correctly excluded: "3 damage < toughness 5"; Chandra's Defeat included).
- **Darksteel Colossus**: destroy 0/637 ("indestructible: destroy fails"), damage 0/891,
  exile 358/358 ✓, -X/-X 93/310 ✓, bounce ✓.
- **Carnage Tyrant**: all 637 targeted-destroy blocked ("hexproof"), edicts conditional,
  sweepers 193/193 ✓.

**Deep-interaction test — Dress Down vs Urza's Saga (the acid test, passed).** The engine
reads Urza's Saga's graph (a land, so creature-only answer classes are suppressed and
removal is retargeted to lands/permanents), follows its `TokenScript` edge to the Construct
token script, sees the token is base 0/0 with size granted *by its own static ability*, and
therefore adds an **ability-removal** answer class: Dress Down surfaces as the top mass
answer with the reason "the Construct Tokens it creates are base 0/0 and get +X/+X from
their own static ability — remove abilities and they die as 0/0s (CR 704.5f)". The verdict
layer also distinguishes Witness Protection-style effects (removes abilities *but sets base
P/T to 1/1* → conditional, token neutralized but alive) and single-target Auras (only hit
one token). In blue: 19 ability-removal candidates found, 8 cleanly working. Neither text
search nor co-occurrence can derive this — it requires composing threat graph → token
script → CDA analysis → answer graph.

**And the verdicts are engine-verifiable.** Five claims have been executed in XMage,
all VERIFIED: Bolt fails vs Sheoldred (she survives), Terminate kills her, Wrath of God
sweeps a Grizzly Bears but leaves Darksteel Colossus standing (106–630ms each), and the
Dress Down pair — chapter II makes a Construct on turn 3, B flashes Dress Down, the token
dies to state-based actions (Construct count 0); the control run without Dress Down shows
it surviving as a 1/1. The product
badge: ⚡ *Engine-verified* on any verdict backed by a corpus scenario; one click shows the
game state. No other tool can do this — a sideboard guide where the advice has been *played
out by a rules engine*.

Meta-deck mode (needs external data: meta decklists from MTGGoldfish/Melee — network-gated):
aggregate the answer matrix across a deck's key threats, weight by meta share, output "best
15-slot coverage" suggestions.

*Status: answer engine + verdict logic + engine verification built and demonstrated. Known
gaps (be honest in-product): ward is flagged but not cost-evaluated; edicts are conditional
on board state; static-based protections on the threat's controller's other permanents
(e.g. their own Leyline) aren't modeled yet — these become scenario templates.*

## MVP sequencing

1. **Meta Lab CLI → simple web page** (answers engine is done; smallest surface, sharpest
   demo, screenshots itself)
2. **Commander Workbench** (recs engine done; needs hook library expansion + decklist input)
3. **Omnibar + card pages** (needs frontend investment + LLM credentials)
4. **Judge** (needs NL→scenario compiler maturity; ship the board-builder input first, NL later)

## Constraints

- **Fan Content Policy: non-commercial.** No paywalls on rules content; card images via
  Scryfall URIs, not rehosted. If commercialization is ever considered, that's a WotC
  licensing conversation, not a product tweak.
- Trust labels are load-bearing product surface everywhere: **Simulated / Derived-from-graph /
  Best-effort** must be visually distinct; never blur them.
- Every answer states its version tuple (CR effective date, engine version, data snapshot) in
  the footer — cheap to render, builds the "this thing is serious" brand.
