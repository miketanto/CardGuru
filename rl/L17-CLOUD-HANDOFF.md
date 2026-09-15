# Handoff prompt for a cloud session: 17Lands DSK game-rebuild fidelity (2026-09-15)

Paste everything below the line into a new cloud Claude Code session.

---

You are continuing a one-set fidelity trial: how faithfully can the XMage engine rebuild logged human Magic: The Gathering games from 17Lands replay data? This instance cannot reach 17Lands; all data is in the repo.

REPO AND BRANCHES
- Repo: https://github.com/miketanto/CardGuru (public).
- Start from branch `data/l17-dsk` at its latest commit (19e179b or later). Create and work on a NEW branch `data/l17-cloud` from it. Push only to `data/l17-cloud`. The local session has finished; do not push to `data/l17-dsk`.
- End every commit message with: Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
- Commit results as text/CSV only: no jars, .class files, build output or model files.

READ FIRST, in this order:
1. `rl/L17-FIDELITY.md`: everything done so far, including the harness design in section 3 and the faults already fixed in 3.1.
2. `rl/L17-CLOUD.md`: the plan, the verified data format in section 4, and the pre-stated readings in section 3.
3. `CLAUDE.md`, section "Ground rules for results": Wilson intervals; pre-register before looking; state what a number cannot support; correct in the open.
4. `rl/engine-patches/README.md` and `rl/setup_engine.sh`.

DATA
- `rl/l17_dsk/DSK_top2000.jsonl.gz` holds 2,000 Duskmourn PremierDraft games by strong players, one JSON object per game. It has every non-empty 17Lands column, plus the `deck` and `sideboard` fields as {card name: count}.
- Card lists are pipe-separated Arena ids, mapped to names by `rl/l17_dsk/DSK_top2000.cards.json`. Token ids are named, with rarity "token".
- The `*_abilities` columns hold ability ids, which are not mapped.
- `on_play` and `won` are the strings "True" and "False".
- `user_turn_N` is the user's own turn N, and `oppo_turn_N` is the opponent's turn N.
- The user's hand is logged in full; the opponent's hand only as a count.

STATE SO FAR (done by a local session; final commit 19e179b)
- Coverage: every user deck and every logged opponent card exists at the XMage pin (2000/2000, `rl/l17_dsk/coverage_games.csv`).
- Harness: in `rl/l17/`. `build_specs.py` turns a game into a spec. `L17Rebuild.java` is a `CardTestPlayerBase` subclass driving an `L17Player` (a `TestPlayer`) that forces the logged actions. `analyze.py` compares states and `causes.py` classifies first mismatches. `run_l17.sh` drives it all.
- `rl/l17/classpath.txt` and `run_l17.sh` were written for a local machine, using `/home/user/mage` and `~/.m2` from an existing build. Adapt them to your own build.
- Five harness faults were already found and fixed; they are listed in `rl/L17-FIDELITY.md`. The last one: face-down attackers and blockers logged as "[Face-Down Card]" were never matched. The preliminary 200 commit 0ef778d is superseded.
- Final base results. "Turns matched" counts full rounds, so the bar of 8 means about 16 side-turns.
  - 200 seeded games (`random.Random(17).sample(range(2000), 200)`): 0/200 >= 8, Wilson [0, 0.019].
  - All 2,000: median 2, mean 2.60; 1/2000 >= 8, Wilson [0, 0.003]; 15/2000 fully matched. The most frequent first mismatch is user creatures (32%).
- Guided variant: it steers hidden choices using logged outcomes. On 2,000 games its median is 3, with 4/2000 >= 8 and 25 fully matched. It was longer than base in 405 games and shorter in 21.
- Yield (base): labelled decisions per game before the first mismatch are land 2.63, spell 1.64, attack 0.66, block 0.07. The unambiguous share is 0.387, but only 0.028 for spells. 58.6% of user turns had more than one possible order.
- Causes of the first mismatch (2,000 games):
  - 33%: drift in state the check doesn't compare, which later makes a logged action impossible. Example: a surveil sent next turn's logged draw to the graveyard.
  - 27%: activated abilities not replayed, because the ability ids are unmapped.
  - At least 14%: hidden choices (search, manifest dread, targets).
  - 13%: a life total alone differs.
- The pre-stated go/no-go was coverage >= 0.6 AND >= 50% of covered games matching >= 8 turns. It is NO-GO on fidelity; coverage passed. Do not change that bar or re-score it. Your job is to find out what CAN be made faithful, as a separate, pre-stated reading.

STEP 1 - ENGINE (from scratch)
- Install JDK 21 and Maven 3.9.
- Clone https://github.com/magefree/mage and check out 7554968c.
- Run `git apply rl/engine-patches/phase9-engine.patch`. Do NOT apply phase12-mana-recopy.patch.
- Overlay `rl/xmage-src/*.java` into `Mage.Tests/src/test/java/org/mage/test/benchmark/rl/`, and `benchmark/xmage/src/*.java` into `.../org/mage/test/benchmark/`.
- Run `mvn -q -T 1C -DskipTests -Dmaven.javadoc.skip=true install`. `rl/setup_engine.sh` does all of this, but it hardcodes /home/user paths; symlink those paths or edit a copy.
- If GitHub or Maven Central is unreachable, write the blocker to `rl/L17-FIDELITY-CLOUD.md`, then commit, push and stop.

STEP 2 - REPRODUCE (on the corrected harness at 19e179b)
- Port the harness to your build and rerun the base rebuild on the same 200 seeded games.
- Report whether the per-game turns matched equal the corrected base 200 rows in `rl/l17_dsk/` (see `rl/L17-FIDELITY.md` for the file name). Report any differences, with the reason for each.
- Commit and push.

STEP 3 - IMPROVE THE REBUILDER (the main work). Attack the causes in order of their counts, each as a named, separately reported variant. The base result stays as recorded. Candidates:
 a. Cascading divergence: once one action fails, the later forced actions fail too (attacker absent, card not in hand). Measure how often the first failed forced action comes before the first state mismatch. Also measure how far a per-turn "resync" gets. A resync sets the state to the logged end-of-turn state: hand, lands, creatures, non-creatures and life. That tests one-turn fidelity independent of drift. Report per-turn fidelity (the share of side-turns whose end state matches, given a correct start) as its own reading.
 b. Logged abilities: map the ability ids if the data allows (they may match XMage ability text via the card that owns them). Otherwise infer activations from state changes, and force the activations.
 c. Hidden choices: extend the guided steering (targets from logged kills, manifest dread, surveil, searches, discards).
 d. Opponent seat: better hand reconstruction, and flash or instant timing.
 e. The fixed within-turn order rule (land, then casts by ascending mana value): try orders consistent with the log's end state.
 Before running each variant on 200 games, write in the doc what it is expected to move and what it cannot move.

STEP 4 - READINGS (report for base and every variant on the same 200 games, then on all 2,000 if a variant looks promising)
- Median turns matched, and the share >= 8 turns with a Wilson 95% interval.
- Per-turn fidelity after resync.
- The first-mismatch field distribution.
- Labelled decisions per game by kind (land / spell / attack / block) before the first mismatch, and the unambiguous share.
- The top three remaining causes, with an example game each and the fix each would need.
- State what the numbers cannot support: the opponent seat is reconstructed, and order and targets are guessed.
- Finish with a recommendation. Either full-game imitation from these logs is viable, or only per-turn labels after resync are, or neither is. Say what it would take.

OUTPUT
- Write everything to `rl/L17-FIDELITY-CLOUD.md`, with per-game CSVs in `rl/l17_dsk/` (suffix `_cloud`).
- Commit and push after each step, so nothing is lost if the session ends.
- Your final message: the reproduction check, the readings table (base and variants), the recommendation, and the commit hashes.
