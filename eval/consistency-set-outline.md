# Consistency test set — design outline (DRAFT, not frozen)

Companion to `plan/nl-dsl-consistency.md` (Phase C0) and `research/nl-to-dsl-consistency.md`.

**Status: draft for review.** Per decision rule R6 the set is hashed and frozen *before*
the first scoring run — so this is the moment to dissect it. The last section
(§7 "Known gaps") is where I've listed what I think is missing or weak; add to it.

---

## 1. What makes this different from every eval set we already have

`nl_questions_poc/dev/adversarial` all ask the same question — *did this one phrasing find
the right card?* A consistency set asks a different one — *do five phrasings of the same
intent find the **same** cards?* Four consequences that change the design:

1. **The unit is the intent, not the question.** One intent = one mechanical meaning =
   *N* paraphrases. Scoring compares paraphrases to *each other*, not to a gold query.
2. **A gold DSL query is optional; a witness is not.** We don't need to know the one true
   query (there often isn't one). We need a witness card to tell "consistently right"
   from "consistently wrong," and a foil to catch "consistently overbroad."
3. **Consistency alone is not a good score.** A compiler that returns `{}` for everything
   is perfectly consistent. Hence R2: `PC` always ships next to `agreement@witness`.
4. **Some intents should score badly and that's correct.** Genuinely ambiguous questions
   *ought* to produce divergent readings; the right behaviour is noticing, not guessing
   consistently. Those are a labeled, inverted-scoring stratum (R3).

---

## 2. The four axes

Every intent is tagged on all four. Coverage is checked per-axis, not just in aggregate —
that's what makes R5 ("a phase ships only if it moves the stratum it targets") enforceable.

### Axis S — DSL structural shape (what the compiler must emit)

| tag | shape | why it's in the set | n |
|---|---|---|---|
| `S1` | single `node` | floor case; if this is inconsistent, nothing else matters | 3 |
| `S2` | `node` + `params` | param precision — where `Cost` regexes and zone names live | 6 |
| `S3` | `chain` from→to | the workhorse: one ability leads to another | 5 |
| `S4` | `chain` with **list** `to` | "one ability does *both*" — the subtlest DSL feature | 3 |
| `S5` | `all` across independent abilities | conjunction over separate abilities, not one chain | 3 |
| `S6` | `any` / idiom alternation | where the *same concept has two Forge encodings* | 3 |
| `S7` | `not` | negation — known-weak in every retrieval paradigm | 2 |
| `S8` | `card` attrs + graph | mixing type/color/cost with mechanics | 3 |
| `S9` | `keyword` / `hook` / `role` | closed-label operators: should be the *most* consistent | 4 |
| — | no shape (no correct result set) | the `H09`/`H11`/`H12` rows | 8 |

The `S9` row is a control. Those operators have a closed label set (48 hooks, 4 roles), so
NL→facet is classification, not generation. If `S9` is inconsistent, the problem isn't the
DSL's expressiveness — it's upstream in question understanding, and that changes the plan.

### Axis H — semantic hazard class (where compilers actually slip)

This is the axis to dissect hardest; it's the taxonomy of *how* NL→DSL goes wrong.

| tag | hazard | concrete failure | n |
|---|---|---|---|
| `H01` | **cost vs effect** | "sacrifice a creature" as an activation cost vs as an effect | 3 |
| `H02` | **idiom alternation** | one concept, two encodings: `DamageAll`/`ValidPlayers` vs `DealDamage`/`Defined`; `ChangeZoneAll`/`ChangeType` vs `ChangeZone`; `Fog` vs `PreventDamage`. **All four of our known failures live here.** Picking encoding A on Monday and B on Tuesday is inconsistency with two defensible queries | 3 |
| `H03` | **scope / quantifier** | "a creature" vs "each creature" vs "target creature"; "you" vs "an opponent" vs "each player" | 3 |
| `H04` | **zone precision** | graveyard→battlefield vs library→battlefield vs graveyard→hand | 4 |
| `H05` | **repeatability** | one-shot vs engine (we have `role:...:engine` for exactly this) | 1 |
| `H06` | **timing / speed** | instant-speed, flash, sorcery-only — *not* naturally a graph node | 3 |
| `H07` | **negation / exclusion** | "without", "that don't", "other than" | 2 |
| `H08` | **numeric / comparative** | "three or more", "equal to the number of" — `Count$`/`SVar` territory | 2 |
| `H09` | **underspecified** ⟲ | two or more legitimate readings. **Inverted scoring** (R3) | 4 |
| `H10` | **compositional novelty** | a combination no exemplar covers — does it generalise or snap to the nearest example? | 3 |
| `H11` | **out of DSL scope** | legality, price, meta, "best" — correct answer is *route elsewhere*, consistently | 2 |
| `H12` | **false premise** | the question presupposes a mechanic that doesn't exist | 2 |
| `H00` | no special hazard | plain intents, to keep the set from being all-hard | 8 |

`H09`, `H11` and `H12` share a property worth naming: **the correct behaviour is not a
result set.** They test whether the system consistently *declines* rather than consistently
guesses, which is the same posture `plan/architecture.md` §2 takes on misroutes.

### Axis D — result-set size regime (metric sensitivity, not difficulty)

| tag | hits | why it matters |
|---|---|---|
| `D1` | 1–20 | Jaccard is brittle: one token swap can halve it. Over-reports inconsistency |
| `D2` | 20–300 | the honest middle; most product queries live here |
| `D3` | 300+ | Jaccard is forgiving: two quite different queries can look agreeable. Under-reports |

`PC` is reported per-regime and never pooled across them without the breakdown. Our search
returns unranked sets, so full-set Jaccard is the right operation — but a `D1` intent
scoring 0.5 and a `D3` intent scoring 0.5 mean very different things.

### Axis P — provenance / drift probe

| tag | meaning |
|---|---|
| `spec-covered` | a hand-written `DSL_SPEC` idiom line addresses this family |
| `spec-adjacent` | *near* a spec-covered family but not covered by it — **the drift probes** |
| `spec-absent` | no spec line touches it |

The `spec-adjacent` intents are the point of this axis. When someone adds a `DSL_SPEC` line
for the Fog family, `ΔPC` on the spec-adjacent damage-prevention intents tells us whether
that line helped its neighbours or perturbed them. Right now we have no way to see this.

---

## 3. The paraphrase ladder

Five rungs per intent, fixed roles so the set is balanced by construction rather than by
whatever phrasings happened to occur to the author.

| rung | register | rule |
|---|---|---|
| `P1` | **rules / judge** | precise CR vocabulary. "deals combat damage to a player", "put onto the battlefield". The nearest thing to a canonical form |
| `P2` | **player slang** | how it's actually said at a table: "connects", "blink", "tutor", "wrath", "sac outlet", "goes wide", "impulse". Must contain ≥1 idiom absent from card text |
| `P3` | **terse** | noun phrase, no verb, ≤6 words. "token doublers." Tests behaviour under underspecification that is *not* ambiguity |
| `P4` | **verbose** | 2–3 sentences with deckbuilding context and a hedge. The realistic user message. Must contain ≥1 irrelevant clause — distractor robustness |
| `P5` | **synonym-substituted** | `P1` with domain synonyms swapped (Spider-Syn protocol): graveyard→bin/yard, library→deck, creature→body/dude, battlefield→play, mana value→CMC |

Rules that keep the ladder honest:

- **Same mechanical meaning, verified by hand.** If two rungs genuinely mean different
  things, that's an authoring bug, not a finding. This is the main review burden.
- **No rung may name the witness card.** Otherwise we measure name-matching.
- **No rung may use an ontology token verbatim** (`ChangeZone`, `DamageAll`, `Fog`). That
  turns compilation into copying and inflates every number.
- `P4` distractor clauses are drawn from a fixed pool ("I'm on a budget", "this is for
  Commander", "ideally in black") so verbosity is a controlled variable, not free-form noise.

---

## 4. Worked ladders

Ten intents written out in full, to show the register targets. The remaining thirty are in
§5 as one-liners; their ladders get written during C0, to this template.

---

**I11** · `S6` `H02` `D2` · *spec-covered* · witness **Sizzle**, **Fiery Confluence** · foil **Lightning Bolt**

> The known q1 family. Forge encodes this as `DamageAll`/`ValidPlayers`, but `DealDamage`
> with a `Defined` param is also defensible — two encodings, different result sets, both
> pass validation. This is the flagship `H02` case.

- `P1` cards that deal damage to each opponent
- `P2` stuff that pings the whole table
- `P3` damage to each opponent
- `P4` I'm building a group-slug deck and I'd like anything that hits every opponent at once with damage. It needs to hit all of them, not just one — targeted burn doesn't help me here. Budget isn't a concern.
- `P5` spells that burn every other player at the table

---

**I12** · `S6` `H02` `H03` `D1` · *spec-covered* · witness **Evacuation** · foil **Unsummon**

> The d13 family: mass zone-changes select with `ChangeType`, not `ValidCards`. Also
> carries an `H03` scope hazard ("all" vs "target").

- `P1` cards that return all creatures to their owners' hands
- `P2` mass bounce
- `P3` bounce all creatures
- `P4` My deck folds to a wide board. I want a reset that puts every creature back in hand instead of killing them, since I'd rather not give my opponents graveyard value. This is for Commander.
- `P5` spells that send every creature back to its owner's hand

---

**I40** · `S2` `H02` `D1` · **spec-adjacent** · witness **Circle of Protection: Red** · foil **Fog**

> The drift probe for the Fog spec line. Fog has a dedicated `Fog` api; general damage
> prevention does not. When someone adds the Fog idiom line, does this intent's `PC` move?

- `P1` cards that prevent damage that would be dealt to you
- `P2` cards that let you fog damage aimed at your face
- `P3` damage prevention for yourself
- `P4` I keep dying to burn and I'd like something that stops damage pointed at me specifically, not at my creatures. Repeatable would be ideal but I'll take one-shots. Ideally in white.
- `P5` cards that stop damage that would hit you

---

**I04** · `S2` `H01` `D2` · *spec-absent* · witness **Krark-Clan Ironworks**, **Arcbound Ravager** · foil **Ravenous Chupacabra**

> The cost-vs-effect hazard on the artifact axis. The `Cost` param regex is the whole
> question; an effect-side sacrifice is a different node entirely.

- `P1` activated abilities that require sacrificing an artifact as part of their cost
- `P2` artifact sac outlets
- `P3` sacrifice an artifact: cost
- `P4` I'm building an artifact deck that wants to eat its own permanents for value. I need the sacrifice to be part of paying for the ability, not something the ability does to my opponents. Colour doesn't matter much.
- `P5` abilities you pay for by sacrificing an artifact

---

**I08** · `S4` `H03` `D1` · *spec-absent* · witness **Gray Merchant of Asphodel** · foil **Sizzle**

> `S4`'s "one ability does both" list-`to` form. The foil does half the job (drains without
> the lifegain), which is exactly the error an `all`-of-two-nodes compilation makes.

- `P1` a single ability that makes each opponent lose life and gains you that much life
- `P2` drain effects
- `P3` lose life, you gain it
- `P4` I want the classic drain: opponents lose life and I gain the same amount off one trigger. Two separate abilities that happen to do both things isn't the same thing. This is for a black devotion build.
- `P5` one ability where every other player loses life and you gain that much

---

**I10** · `S5` `S9` `D1` · *spec-absent* · witness **Prossh, Skyraider of Kher** · foil **Krenko, Mob Boss**

> Conjunction across *independent* abilities — deliberately contrasted with I08's single
> chain. Also probes whether the compiler reaches for `hook` operators when it could.

- `P1` creatures that both create creature tokens and have a sacrifice outlet
- `P2` commanders that make their own fodder and can eat it
- `P3` token maker plus sac outlet
- `P4` I want a single card that's a self-contained aristocrats engine — it makes the bodies and it can sacrifice them without needing another card. One card doing both halves, not two cards. This is for Commander.
- `P5` creatures that make tokens and can also sac creatures themselves

---

**I18** · `S9` `H05` `D2` · *spec-absent* · witness **Phyrexian Arena** · foil **Divination**

> The `role:card_draw:engine` control. Closed-label operator + a repeatability hazard the
> DSL already models explicitly. Should be near-perfectly consistent; if it isn't, that
> finding reshapes the plan.

- `P1` cards that provide repeatable card draw every turn rather than a one-time draw
- `P2` draw engines, not cantrips
- `P3` repeatable draw
- `P4` My deck runs out of gas around turn six. I'm looking for something that keeps drawing me extra cards every turn on its own, not a one-shot that refills once and then does nothing. Budget matters.
- `P5` permanents that keep drawing you extra cards each turn

---

**I22** · `S8` `H06` `D2` · *spec-absent* · witness **Swords to Plowshares** · foil **Day of Judgment**

> Timing is a *card-type* property, not a graph node. Tests whether the compiler reaches
> for the `card` operator or hallucinates a mechanical encoding of "instant speed."

- `P1` creature removal that can be cast at instant speed
- `P2` removal I can hold up
- `P3` instant-speed removal
- `P4` I'd rather not tap out on my own turn — I want to kill a creature during someone else's turn, ideally at the end of their turn. Sorceries don't work for this. Any colour is fine.
- `P5` spells that kill a creature and can be cast on someone else's turn

---

**I26** · `H09` ⟲ · *spec-absent* · **no witness — inverted scoring**

> At least four legitimate readings: exile as removal, exile from library (impulse), exile
> as a cost, exile-matters payoffs. Success = the k-sample consensus *fails* and the system
> asks which one. Consistency here would be a bug.

- `P1` cards that exile things
- `P2` exile stuff
- `P3` exile effects
- `P4` I want cards that exile. There's a lot of graveyard recursion in my playgroup so exiling comes up a lot. What's out there?
- `P5` cards that remove things from the game

---

**I36** · `H12` `D1` · *spec-absent* · **expected: 0 results, stated as such**

> Flash on a sorcery is not a thing. Correct behaviour is an empty result set *with an
> explanation*, delivered consistently — not five different creative reinterpretations.
> This is the search-side analogue of the Last Gasp false-premise case from round 2.

- `P1` sorceries with flash
- `P2` sorceries you can cast at instant speed
- `P3` flash sorceries
- `P4` I'm looking for sorceries that have flash so I can cast them on my opponent's turn. Does that exist, and if so which ones are worth playing?
- `P5` sorcery-speed spells that have flash

---

## 5. Full roster (40 intents)

Paraphrase ladders for the un-worked rows get authored during C0. Witnesses are hand-checked
against the index at freeze time; any that don't resolve get replaced *before* the hash.

| id | intent (P1 form) | S | H | D | prov | witness | foil |
|---|---|---|---|---|---|---|---|
| I01 | cards that create Treasure tokens | S1 | H00 | D2 | absent | Smothering Tithe | — |
| I02 | cards that shuffle your graveyard into your library | S1 | H04 | D1 | absent | Elixir of Immortality | Raise Dead |
| I03 | cards with an ability that requires paying life as a cost | S2 | H01 | D2 | absent | Griselbrand | Phyrexian Arena |
| I04 | activated abilities that sacrifice an artifact as a cost | S2 | H01 | D2 | absent | Krark-Clan Ironworks | Ravenous Chupacabra |
| I05 | creatures that draw you a card when they die | S3 | H00 | D2 | absent | Solemn Simulacrum | Elvish Visionary |
| I06 | landfall triggers that create creature tokens | S3 | H00 | D1 | absent | Rampaging Baloths | — |
| I07 | one ability that draws cards and then makes you discard | S4 | H00 | D2 | absent | Faithless Looting | Windfall |
| I08 | one ability that drains each opponent and gains you that life | S4 | H03 | D1 | absent | Gray Merchant of Asphodel | Sizzle |
| I09 | creatures with flying that also have a death trigger | S5 | H00 | D1 | absent | Archon of Justice | Baneslayer Angel |
| I10 | creatures that make tokens and have a sacrifice outlet | S5 | H00 | D1 | absent | Prossh, Skyraider of Kher | Krenko, Mob Boss |
| I11 | cards that deal damage to each opponent | S6 | H02 | D2 | **covered** | Sizzle, Fiery Confluence | Lightning Bolt |
| I12 | cards that return all creatures to their owners' hands | S6 | H02 | D1 | **covered** | Evacuation | Unsummon |
| I13 | creatures that create tokens without sacrificing anything | S7 | H07 | D2 | absent | Krenko, Mob Boss | Prossh, Skyraider of Kher |
| I14 | creature removal that doesn't target | S7 | H07 | D2 | absent | Wrath of God | Doom Blade |
| I15 | green sorceries that search your library for a land | S8 | H04 | D2 | absent | Rampant Growth | Eladamri's Call |
| I16 | instants that create creature tokens | S8 | H06 | D2 | absent | Raise the Alarm | Dragon Fodder |
| I17 | creatures with both deathtouch and lifelink | S9 | H00 | D1 | absent | Vampire Nighthawk | Sedge Scorpion |
| I18 | repeatable card-draw engines, not one-shot draw | S9 | H05 | D2 | absent | Phyrexian Arena | Divination |
| I19 | sacrifice outlets | S9 | H01 | D2 | absent | Viscera Seer | Fleshbag Marauder |
| I20 | cards that return creatures from a graveyard to the battlefield | S3 | H04 | D2 | absent | Reanimate | Raise Dead |
| I21 | cards that search your library for a creature and put it in hand | S2 | H04 | D1 | absent | Eladamri's Call | Green Sun's Zenith |
| I22 | creature removal castable at instant speed | S8 | H06 | D2 | absent | Swords to Plowshares | Day of Judgment |
| I23 | creatures you can cast at instant speed | S9 | H06 | D2 | absent | Restoration Angel | Serra Angel |
| I24 | cards that draw three or more cards at once | S2 | H08 | D2 | absent | Concentrate | Divination |
| I25 | creatures whose power equals the creature cards in your graveyard | S2 | H08 | D1 | absent | Splinterfright | Lord of Extinction |
| I26 | cards that exile things ⟲ | — | H09 | — | absent | — | — |
| I27 | good removal ⟲ | — | H09 | — | absent | — | — |
| I28 | cards that care about creatures dying ⟲ | — | H09 | — | absent | — | — |
| I29 | cards that copy things ⟲ | — | H09 | — | absent | — | — |
| I30 | creatures that make a token whenever you cast an instant or sorcery | S3 | H10 | D2 | absent | Young Pyromancer | Guttersnipe |
| I31 | creatures that untap during each other player's untap step | S5 | H10 | D1 | absent | Seedborn Muse | Wilderness Reclamation |
| I32 | cards that let you cast the top card of your library | S4 | H10 | D1 | absent | Future Sight | Sensei's Divining Top |
| I33 | what's the best commander for a budget deck | — | H11 | — | absent | — | — |
| I34 | cards banned in Modern | — | H11 | — | absent | — | — |
| I35 | cards that let you untap during your opponent's upkeep | — | H12 | — | absent | — | — |
| I36 | sorceries with flash | — | H12 | D1 | absent | — (expect 0) | — |
| I37 | cards that make each player draw an extra card | S6 | H03 | D1 | absent | Howling Mine | Divination |
| I38 | creatures with an enters-the-battlefield trigger | S3 | H00 | **D3** | absent | Solemn Simulacrum | — |
| I39 | cards that destroy a target creature | S1 | H03 | **D3** | absent | Doom Blade | Wrath of God |
| I40 | cards that prevent damage that would be dealt to you | S2 | H02 | D1 | **adjacent** | Circle of Protection: Red | Fog |

Axis totals, as actually allocated (checked against `eval/nl_consistency_intents.json`):

- **S** — S1 ×3, S2 ×6, S3 ×5, S4 ×3, S5 ×3, S6 ×3, S7 ×2, S8 ×3, S9 ×4, untagged ×8.
- **H** — H00 ×8, H01 ×3, H02 ×3, H03 ×3, H04 ×4, H05 ×1, H06 ×3, H07 ×2, H08 ×2,
  H09 ×4, H10 ×3, H11 ×2, H12 ×2.
- **D** — D1 ×10, D2 ×18, D3 ×5, untagged ×7. *(Measured, not declared — see below.)*
- **prov** — covered ×2, adjacent ×1, absent ×37.

**All 40 intents now carry the full five-rung ladder.** The authoring rules in §3 are
enforced by a scripted check (no witness-name leaks, no verbatim ontology tokens, P3
within six words, every witness/foil resolving against the pinned index). It earns its
keep: it caught I20, whose witness was the card *Reanimate* while its slang and terse
rungs use "reanimation"/"reanimate" as the natural player term — the compiler could have
matched the card name instead of the mechanic. Witness swapped to Animate Dead + Zombify,
which also span two encodings of the same effect.

**D-tags are now measured rather than guessed.** Seven were wrong in the draft, all
under-estimates: I08, I10, I12, I40 (D1→D2), I22 (D2→D3, 2,364 hits), and I18/I19
(D2→D3, 2,454 and 533 hits, measurable only once the `hook`/`role` bug was fixed). The
distribution shifted materially — D1 from 15 to 10, D3 from 2 to 5 — which matters
because D-regime is what makes a Jaccard number interpretable.

Three counts remain thinner than the hazard deserves — see §7 items 11–13.

---

## 6. Scoring, per stratum

| stratum | primary metric | target |
|---|---|---|
| `S*`, `H00`–`H08`, `H10` | `PC_correct` (Jaccard over result sets, correct compilations only) | high; per-regime `D1`/`D2`/`D3` breakdown mandatory |
| all of the above | `agreement@witness` — fraction of the 5 paraphrases that return the witness | high; guards against consistent-and-wrong (R2) |
| all of the above | `foil rate` — fraction returning the foil | ~0; guards against consistent-and-overbroad |
| `H09` ⟲ | **disagreement score** — 1 − modal-cluster share over *k* samples | **high**, and separable from the rest of the set (this is C1's decision rule) |
| `H11` | route-away rate | consistent across all 5 paraphrases; the specific route matters less than its stability |
| `H12` | empty-result-plus-explanation rate | consistent; five creative reinterpretations is the failure |
| `spec-adjacent` | `ΔPC` across a `DSL_SPEC` edit | ≈ 0 — a spec line should not perturb its neighbours |

Reported but explicitly **not** optimised: `DSL-EM` (exact query match). Two structurally
different queries with identical hit sets are the same query; optimising EM would train us
toward the wrong invariance (R1).

---

## 7. Known gaps — the part to argue with

Things I left out, with why. Add, override, or tell me the reasoning is wrong.

1. **Multi-face cards.** No split, MDFC, adventure, Saga, or Class intents. The parser
   handles Saga/Class edges specially and those are a plausible inconsistency source, but
   they'd need witnesses whose behaviour I'd want to verify against the index first.
   *Probably the biggest real gap.*
2. **Multi-constraint stacking.** Nothing in the set stacks more than ~2 constraints.
   Real Commander questions routinely stack four ("green creatures under 4 mana that ramp
   and don't die to a wrath"). If `PC` degrades with constraint count, that's a curve worth
   plotting, and this set can't see it.
3. **Follow-up / conversational refinement.** Every intent is a cold single turn. "Now
   only the ones in black" is how people actually search, and its consistency is untested.
   Deliberately deferred — it's a different system (state), not a different question.
4. **Colour and mana-cost constraints** appear once (I15). Under-weighted relative to how
   often real users say them.
5. **Tribal / creature-type** questions entirely absent ("goblins that...").
6. **Non-English and typo'd input.** `P5` does synonym substitution but no misspellings.
   Cheap to add as a sixth rung; excluded to keep the ladder at 5 × 40 = 200.
7. **`D3` is thin** (2 intents). Enough to notice a metric problem, not enough to
   characterise it. If early runs show `PC` behaving oddly at scale, this needs 5+.
8. **Foils are single cards.** A foil *class* ("no sorceries at all") would catch
   overbroad compilation better than one named card. Left simple for authoring cost.
9. **No adversarial paraphrases.** Nothing here is written to *break* the compiler — the
   ladder is realistic-register by design. A hostile rung is a separate exercise, and
   arguably belongs with `nl_questions_adversarial` rather than here.
10. **`H09` has no ground truth for "how many readings".** I labeled four intents
    ambiguous by judgement. If the compiler disagrees, is it wrong or am I? Mitigation
    would be independent labeling by a second person before freeze.
11. **`H05` (repeatability) has exactly one intent** — I18, which is also the `S9` control.
    That conflates two things I wanted to measure separately. Wants a second, e.g. a
    repeatable-vs-one-shot removal or ramp pair.
12. **`H07` (negation) has two intents**, and negation is the single most reliably-weak
    construct across every retrieval paradigm in the literature. Under-sampled relative to
    risk; 3–4 would be proportionate.
13. **`H02` has three intents but is where all four known failures live.** I11 and I12 are
    both `spec-covered`, so only I40 probes an *uncovered* alternation. If `H02` is the
    stratum C3 ships or dies on (R5), three rows — one of them the sole uncovered case — is
    a thin basis for that decision. This is arguably the most consequential gap in the set.

    **Confirmed by events.** C3 did ship on this stratum (baseline 0.456 → 0.599), and the
    14-point gain rests on I11 and I40 alone; I12 was exactly flat. Meanwhile the pool
    turns out to contain many more such families — four `*All`-versus-singular pairs
    measured, every one with Jaccard < 0.01 (`eval/consistency/C3-ablation.md`). Candidate
    additions with witnesses already resolved: mass creature destruction
    (`DestroyAll` 336 vs `Destroy`+`Defined` 189), mass graveyard return (`ChangeZoneAll`
    69 vs `ChangeZone` 792), counters on each creature (`PutCounterAll` 291 vs
    `PutCounter` 3,136). "Each player discards" is a useful *negative* control — `DiscardAll`
    does not exist, so there is no alternation to get wrong. Four more H02 rows would put
    this stratum on a defensible footing; slots I41–I50 are reserved for exactly this.

**Open slots reserved:** I41–I50 are left unallocated for whatever comes out of this
review, so additions don't force a re-hash of the numbered rows.

---

## 8. Contamination controls

- Disjoint from `eval/nl_questions_poc.json`, `eval/nl_questions_dev.json`,
  `eval/nl_questions_adversarial.json`, `benchmark/benchmark.json`, and — importantly —
  the compiler's own `EXAMPLES` in `cardguru/nl_compiler.py` and the README's demo
  questions. (This is why there is no "extra turn," no "impulse exile," no "sagas that
  tutor," and no "play lands from your graveyard" intent here.)
- RulesGuru stays unread; nothing in this set derives from it.
- Frozen and hashed before the first scoring run (R6). Post-freeze edits create
  `consistency-v2`, scored independently; v1 numbers are not carried forward.
- Witnesses and foils are resolved against a pinned index (`forge_commit`, `ontology_rev`)
  recorded in the frozen file, per `plan/architecture.md` §4.
