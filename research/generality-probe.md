# Generality probe: does the depth matter on the breadth surfaces?

The question behind this probe (raised while backlogging adjudication deepening):
judge-level interactions are impressive, but *how often does deep graph knowledge
actually come up* on the surfaces most users touch — Commander deck-building and
Meta Lab answers? Measured over the full pool, not cherry-picked demos. Data:
`research/data/generality_probe.json`.

## A) Commander: the hooks generalize — 62% of ALL legendary creatures

With the hook library expanded from 7 to **25 hooks** (spellslinger, landfall,
reanimator, self-mill, plays-from-graveyard, blink, copies, discard/draw/attack
matters, lifedrain, artifacts/enchantments/equipment matter, tribal lords,
untappers, three Panharmonicon-family amplifiers, ...):

- **2,316 of 3,753 legendary creatures (61.7%) get at least one synergy hook.**
  This is not a demo trick — the majority of every possible commander is covered.
- The distribution is Zipfian, topped by makes_tokens (612), puts_counters (610),
  attacks_matter (601), gains_life (297) — the archetypes people actually build.
- Idiom coverage was validated against a 20-commander golden set spanning 17
  archetypes (Krenko, Muldrotha, Gitrog, Isshin, Brago, Urza, Sythis, Wyleth,
  ...): **20/20** after fixing 7 detector idioms found by reading the misses'
  actual Forge scripts (Gitrog's `ChangesZoneAll`, Isshin's Panharmonicon-over-
  attack-modes, Muldrotha's `MayPlay`+`AffectedZone$ Graveyard`, Brago's
  `Origin$ All` return, Urza's `tapXType<1/Artifact>` cost, ...).
- The remaining 38% of legends: mostly keyword-only/vanilla designs plus hooks
  not yet modeled — a demand curve for future hooks, not a wall.

Deck analysis is now live end-to-end (`cardguru deck "Teysa Karlov" --list
deck.txt`): parses standard decklist formats, produces the hook coverage matrix
(sac outlets vs death triggers vs token makers, each card placed correctly),
flags thin hooks, and lists cards connecting to no hook — on the Teysa sample
those were exactly the goodstuff staples (Sol Ring, Counterspell, Swords).

## B) Meta Lab: the hypothesis is half right — and the half that's wrong is the top of the meta

Across all 18,878 creatures:

- **Verdict-changing defensive features appear on only 4.4%** (CDA power/
  toughness 1.3%, ward 1.1%, protection 1.0%, hexproof/shroud 0.7%,
  indestructible 0.4%). So yes — for the *median* creature, "destroy it" just
  works, and deep defense knowledge is unnecessary. The user's intuition is
  confirmed for the long tail.
- But the caveats run the other way:
  1. **Threats aren't sampled uniformly.** Cards become sideboard targets
     *because* they're hard to answer — Sheoldred (toughness gate), Carnage
     Tyrant (hexproof), Darksteel Colossus (indestructible), Urza's Saga
     (token-CDA) are all in the 4.4%. Play-weighted, the tail is the head.
     (Unmeasurable offline — needs meta decklist data, network-gated.)
  2. **Effect-side structure is used in 100% of verdicts** regardless of the
     threat: damage amounts vs toughness (printed toughness exists on 99.1% of
     creatures), destroy vs exile vs bounce vs -X/-X, cost-vs-effect sacrifice,
     single-target vs mass. That's the part text search can't compute with.
  3. The exotic compositions are rare but concentrated at the top: only **23
     cards** make ability-defined 0/0 tokens (the Dress Down vulnerability) —
     and one of them is Urza's Saga, a format-defining card.

## Product conclusion

- **Commander Workbench is the right lead surface**: the depth pays off on a
  majority of the entire commander pool, day one, with mechanical WHYs.
- **Meta Lab's pitch should be sharpened**, not weakened: routine verdicts are
  table stakes (any structured DB can gate damage on toughness); the
  differentiation is (a) the 4.4% tail that *is* the competitive meta, (b)
  effect-side verdict computation, and (c) engine verification — which the
  RulesGuru probe measured at 100% precision.
- Adjudication deepening stays backlogged per plan/roadmap.md; nothing in this
  probe argues for reviving it ahead of the breadth surfaces.
