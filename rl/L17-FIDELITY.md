# L17-FIDELITY — how faithfully XMage rebuilds 17Lands DSK games (one-set trial, 2026-09-15)

Plan and pre-stated readings: `rl/L17-CLOUD.md` §3 (not changed after seeing data).
Data: `rl/l17_dsk/DSK_top2000.jsonl.gz` (2,000 DSK PremierDraft games, strong players, seed 17).
Harness: `rl/l17/`. Results as text/CSV in `rl/l17_dsk/`.

Status: **stage 1 (engine) and stage 2 (coverage) done; rebuilder in progress.**

## 1. Engine

Not run on a cloud instance: this trial ran on the project's local WSL box
beside Phase 13. Instead of rebuilding XMage (a full `mvn install` would
overwrite the `~/.m2` jars the running Phase 13 driver JVM loads, and the
reactor build would starve it of RAM), the harness compiles against the
engine already built at `/home/user/mage`, after checking it is the pinned one:

* checkout HEAD = `7554968c96211009ad1f1208b83d6de8c2b7746d` (the pin);
* `patch -R --dry-run` of `rl/engine-patches/phase9-engine.patch` applies
  cleanly on all three files (Combat, PlayerImpl, RandomUtil), i.e. the patch
  is applied exactly;
* `phase12-mana-recopy.patch` forward dry-run fails a hunk on PlayerImpl
  (not applied), as required;
* JDK `openjdk 21.0.12.1`, Maven 3.9.9 (the ones that built it).

The harness classes are compiled with `javac` into a private directory and run
from a private working directory holding a copy of `Mage.Tests/db` and
`config/`, so nothing in `/home/user/mage` or `~/.m2` is modified. The
`rl/xmage-src` overlay in that build is whatever Phase 13 uses; the harness
touches none of it (it uses only XMage core, Mage.Sets and the Mage.Tests
`CardTestPlayerBase` / `TestPlayer` framework).

## 2. Coverage (`rl/l17/coverage.py` → `rl/l17_dsk/coverage_games.csv`)

Card database = every name registered by a `SetCardInfo` in any
`Mage.Sets/src/mage/sets/*.java` at the pin (32,456 names; CardRepository is
built by scanning these classes). A 17Lands name matches if it is registered
as-is, or for "A // B" names (rooms, double-faced) if the halves are.

| reading | value |
|---|---|
| games whose user `deck` is fully implemented | **2000/2000 = 1.000**, Wilson 95% [0.998, 1.000] |
| games whose user deck AND every mapped opponent card logged played/cast (lands, creatures, non-creatures, instants/sorceries on either turn) is implemented | **2000/2000 = 1.000**, [0.998, 1.000] |
| distinct user-deck card names | 278, missing 0 |
| missing card names | none |
| deck sizes | 40: 1894, 41: 85, 42: 11, 43–48: 10 |

Coverage bar (≥ 0.6): **met**. Cannot support: that the implementations are
*correct* — a registered card can still be implemented differently from Arena;
the rebuild (§3) is what tests behaviour. Unmapped small ids (0–33, 25 ids) are
excluded from the opponent check; they are assumed to be tokens.
