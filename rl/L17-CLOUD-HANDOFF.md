# Handoff prompt for a cloud session: 17Lands DSK game-rebuild fidelity (2026-09-15)

Paste everything below the line into a new cloud Claude Code session.

---

You are continuing a one-set fidelity trial: how faithfully can the XMage engine rebuild logged human Magic: The Gathering games from 17Lands replay data? This instance cannot reach 17Lands; all data is in the repo.

REPO AND BRANCHES
- Repo: https://github.com/miketanto/CardGuru (public).
- Start from branch `data/l17-dsk` at its latest commit (0ef778d or later). Create and work on a NEW branch `data/l17-cloud` from it. Push only to `data/l17-cloud`. A local session may still push to `data/l17-dsk`; do not push there.
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

STATE SO FAR (done by a local session)
- Coverage: every user deck and every logged opponent card exists at the XMage pin (2000/2000, in `rl/l17_dsk/coverage_games.csv`).
- Harness: in `rl/l17/`. `build_specs.py` turns a game into a spec. `L17Rebuild.java` is a `CardTestPlayerBase` subclass driving an `L17Player` (a `TestPlayer`) that forces the logged actions. `analyze.py` compares states and `causes.py` classifies first mismatches. `run_l17.sh` drives it all.
- `rl/l17/classpath.txt` and `run_l17.sh` were written for a local machine, using `/home/user/mage` and `~/.m2` from an existing build. Adapt them to your own build.
- Base result on 200 seeded games (`random.Random(17).sample(range(2000), 200)`): the median game matched 2 turns, and 0 of 200 reached 8 turns (Wilson [0, 0.019]). Only 1 of 200 fully matched. "Turns matched" counts full rounds, so the bar of 8 means about 16 side-turns.
- First-mismatch fields: user_creatures 57, user_life 42, user_hand 41, oppo_life 30, user_lands 13, oppo_hand 11.
- Most common failed forced actions: an attacker absent (user 322, opponent 209), a cast whose card was not in hand (user 293, opponent 125), a block with no blocker (141), a land not in hand (116), a draw not found in library or hand (115).
- Causes of the first mismatch in the 20-game debug: an ability was logged but not replayed (6 of 20); a hidden choice such as a target, manifest dread, surveil or search (4); a forced land not in hand (2); a draw not found (2); the rest single cases.
- The "guided" variant steers hidden choices using logged outcomes. It matched longer than base in 5 of 20 games and shorter in none.
- The pre-stated go/no-go was coverage >= 0.6 AND >= 50% of covered games matching >= 8 turns. On the base rebuild it is NO-GO for fidelity, while coverage passed. Do not change that bar or re-score it.

STEP 1 - ENGINE (from scratch)
- Install JDK 21 and Maven 3.9.
- Clone https://github.com/magefree/mage and check out 7554968c.
- Run `git apply rl/engine-patches/phase9-engine.patch`. Do NOT apply phase12-mana-recopy.patch.
- Overlay `rl/xmage-src/*.java` into `Mage.Tests/src/test/java/org/mage/test/benchmark/rl/`, and `benchmark/xmage/src/*.java` into `.../org/mage/test/benchmark/`.
- Run `mvn -q -T 1C -DskipTests -Dmaven.javadoc.skip=true install`. `rl/setup_engine.sh` does all of this, but it hardcodes /home/user paths; symlink those paths or edit a copy.
- If GitHub or Maven Central is unreachable, write the blocker to `rl/L17-FIDELITY-CLOUD.md`, then commit, push and stop.

STEP 2 - REPRODUCE
- Port the harness to your build and rerun the base rebuild on the same 200 seeded games.
- Report whether the per-game turns matched equal `rl/l17_dsk/fidelity_games_s200.csv`. Report any differences, with the reason for each.
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
