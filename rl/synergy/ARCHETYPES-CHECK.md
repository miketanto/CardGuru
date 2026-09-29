# How far is the graph from FRA's 10 draft archetypes?

Written 2026-09-29, against the current graph (`full_knn`, after
`SYNERGY-GRAPH.md` §11). Cluster numbering follows `eval.json`
(`profiles.full_knn`).

## 0. Answer

**4 of 10 archetypes recovered cleanly, 2 partly, 4 missed.** The
recovered ones are the archetypes whose theme is a single primitive
with its own trigger: surveil, lifegain, Empower, +1/+1 counters. The
misses come from three causes, each fixable in the method (§3):

- a mechanic the vocabulary can't hear: BR's "opponent was dealt
  noncombat damage";
- the rarity weighting turns Prepare's two enablers into hubs, and those
  hubs pull three archetypes' commons into one cross-colour Prepare
  cluster;
- signals too generic to cluster on: UB self-mill, RG ramp.

## 1. Ground truth and its limits

Source: web search result summaries only. Page fetches to draftsim.com and
magic.wizards.com are **blocked by the container's network policy**, so
I could not read the guides in full. Themes as reported:

| pair | name | theme | signpost |
|---|---|---|---|
| WU | Fatehold | surveil aggro | Desperate Futurescribe |
| UB | Theorix | graveyard value / self-mill | Recursive Recruitment |
| BR | Stingerquill | burn aggro | Grim Repriser |
| RG | Konstrari | ramp via Heartwood tokens | Craftwork Crusher |
| GW | Vigorbloom | lifegain + +1/+1 counters | Bloombrute |
| WB | Liliana | attrition / sacrifice | Edgar, Ancient Bloodlord |
| UR | Chandra | noncreature spells (prowess) | Saheeli, Jewel of Avishkar |
| BG | Garruk | graveyard / creature value | Hapatra, the Desert Fang |
| RW | Mabel | +1/+1 counters aggro | Mabel, Valley Hero |
| GU | Kiora | Empower Jace (planeswalkers) | Kiora of Salt and Sand |

- The allied signposts are named directly in search results.
- For enemy pairs, the results name the Echoed Pair characters; I used
  each pair's gold uncommon from the Forge data as its signpost.
- Sources disagree on two themes: WB ("sacrifice" vs "graveyard
  attrition") and BG ("graveyard value" vs "creature value").

Sources: [Draftsim archetypes](https://draftsim.com/mtg-fra-draft-archetypes/),
[Dork guide](https://readdork.com/gaming/magic-the-gathering-reality-fracture-draft-archetypes-guide-d7d4a0b1b5),
[TheGamer](https://www.thegamer.com/magic-the-gathering-reality-fracture-draft-archetypes/),
[Yahoo prerelease guide](https://tech.yahoo.com/gaming/articles/mtg-reality-fracture-prerelease-guide-165049869.html),
[mtg.wiki](https://mtg.wiki/page/Reality_Fracture).

## 2. Scorecard

Two tests per archetype:

- **(a) Signpost:** is it in a cluster whose dominant primitive matches
  the theme?
- **(b) Gold cards:** where do the pair's gold cards land (cards whose
  colours are exactly the pair)? n = 4–7 per pair, so these are counts,
  not rates.

| pair | signpost's cluster | (a) | gold cards: plurality cluster | verdict |
|---|---|---|---|---|
| WU | C7 surveil | ✓ | C7 surveil 6/7 | **recovered** |
| GW | C4 lifegain | ✓ | C4 lifegain 6/7 | **recovered** (lifegain half; the counters half sits in C5) |
| GU | C1 Empower/PW | ✓ | C1 4/6 | **recovered** |
| RW | C5 +1/+1 & target-own | ✓ | C5 2/4 | **recovered** |
| WB | C6 death/sac | ✓ | spread 1/1/1/1 | partial: the signpost matches, the pair doesn't cohere |
| BG | C0 recursion | ✓ (on the "graveyard value" reading) | C0 2/4 | partial |
| UR | C0 recursion | ✗ | C3 draw 2/4 | missed: the noncreature-spell theme exists only inside C2 (30% `cast`, Geist's noncreature cost reduction) |
| UB | C5 counters | ✗ | C2 Prepare 3/7 | missed: no graveyard cluster |
| BR | C0 recursion | ✗ | C2 Prepare 4/7 | missed: no burn cluster |
| RG | C3 draw/discard | ✗ | C2 Prepare 3/7 | missed: no ramp cluster |

The graph also has three clusters that are *not* colour-pair
archetypes. Each is a cross-colour mechanic:

- **C2 Prepare**: 40 cards, 12 of the 21 Prepare cards;
- **C0 recursion / self-ETB**: 61 cards, B/R/G;
- **C8 lands**: 13 cards.

## 3. Why the misses happen, and what would fix them

In priority order. None of these fixes has been tried yet.

1. **Prepare hub effect (UB, BR, RG).** Prepare is designed as exactly
   3 cards in each allied pair (GW, UW, BU, BR, GR 3 each; 6 mono).
   Only two cards can re-prepare: Codie, Ravenous Codex (rare) and
   Infinite Coursework (common). Every Prepare card listens for them,
   and a listener with 2 enablers scores near-maximal rarity. So each
   Prepare card gets strong edges to the same two hubs, whatever its
   colour. In WU and GW the pair's own primitive (surveil, lifegain) is
   stronger and wins: 4 Prepare cards sit in surveil, 2 in lifegain. In
   UB, BR and RG nothing pair-specific outweighs it, so those commons
   fall into C2. **Candidate fix:** damp rarity for hub-and-spoke
   enablers (e.g. rarity from the listener side only, or cap an
   enabler's total contribution), run as a new A/B scheme.
2. **BR burn is invisible.** Whiplash Wordsmith's payoff is
   `CheckSVar$ X` with `X:PlayerCountOpponents$HasPropertywasDealtNonCombatDamageThisTurn`.
   That is not a `Count$` expression, so it is never parsed. 35 cards
   emit `damage`, but **no card listens for it**. **Fix:** map
   `wasDealtNonCombatDamageThisTurn`-style player properties to a
   `damage` (noncombat, to opponent) listener, and split damage
   emissions by target (player vs creature).
3. **UB self-mill is drowned.** The `tograve` listener (graveyard size,
   threshold) is satisfied by 131 emissions, including every instant and
   sorcery resolving. Its rarity weight is therefore near 0, and the 8
   real Mill cards can't stand out. **Fix:** stop counting "a spell
   resolves to the graveyard" as an intrinsic `tograve` emission, or
   weight Library→Graveyard (mill/surveil) separately.
4. **RG ramp never forms a cluster.** Resource edges carry about 8% of
   the within-cluster weight, even in the cluster holding the Heartwood
   makers (C0: Aerid Konstrari, Tenured Tethermage). The signpost
   Craftwork Crusher is tied to recursion cards via its self-ETB
   trigger, not to mana. **Fix:** cluster on a resource-weighted
   variant, or give resource edges a weight scale comparable to state
   edges. Either is a judgment the pre-registration should state first.
5. **WB / UR partial coherence** needs no separate fix; the
   pair-specific primitives exist (`die`; `cast` noncreature). Expected
   to improve if (1) frees the Prepare commons.

## 4. What this check cannot support

- The ground truth is second-hand summaries, not the guides themselves.
- 4–7 gold cards per pair is too few for a rate. The verdicts are
  qualitative calls on counts.
- Archetypes are colour pairs; the graph never reads colour for state
  edges. A mechanic-first cluster that crosses colours (Prepare,
  Empower) is not wrong about synergy. It is answering a different
  question than "what are the draft decks".
