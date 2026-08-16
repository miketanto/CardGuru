# Local engine patches on the XMage pin (`7554968c`)

`phase9-engine.patch` is the full diff of the three engine files this
project modifies, taken against the pin. Apply it to a fresh checkout
with `git apply` from the checkout root, then overlay `rl/xmage-src/`
into `Mage.Tests/src/test/java/org/mage/test/benchmark/rl/` and
`benchmark/xmage/src/` into `.../org/mage/test/benchmark/`.

- `mage/game/combat/Combat.java` — pre-existing bounded
  `getAttackablePlayers` scan (the circular player list spins forever
  when no live opponent remains). Unconditional; upstreamable.
- `mage/util/RandomUtil.java` — Phase 9. `-Dmage.randomPerThread=true`
  gives each thread its own `Random` so concurrent games keep private,
  seedable streams. Default false = the original shared instance.
- `mage/players/PlayerImpl.java` — Phase 9. `-Dmage.playableCache=on`
  memoizes `getPlayable` per player against a state fingerprint;
  `=verify` recomputes and throws on any disagreement; `=off` (default)
  is the untouched code path. See rl/PHASE9-PERF.md.

Everything Phase 9 added is off unless its flag is set, so a checkout
with these patches reproduces pre-Phase-9 behavior by default.

`phase12-mana-recopy.patch` **is not applied and should not be.** Its
fuzzy hunks land on top of the Phase 9 playable-memo block and duplicate
it, and the recopy optimisation it proposes was never adopted. Only two
things from it are carried in `phase9-engine.patch`: the
`MANA_RECOPY_CHECKED` / `MANA_RECOPY_MISMATCHES` counters, which exist
solely because `EpisodeRunner` still prints them under
`-Dmage.manaNoRecopy` and the module does not compile without them. They
stay at zero. This cost a rebuild once; that is why it is written down.
