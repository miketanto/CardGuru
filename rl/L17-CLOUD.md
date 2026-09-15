# L17-CLOUD — a one-set fidelity trial of rebuilding 17Lands games in XMage, run off this machine (plan, 2026-09-15)

Goal (user, 2026-09-15): try the 17Lands replay idea (rl/IDEA-17LANDS.md) on
**one set** to measure fidelity — how much of a logged human game XMage can
rebuild — on a cloud instance, because this box's GPU/RAM are busy with
Phase 13. The cloud instance cannot reach 17Lands, so the data is prepared
here and passed in.

## 1. Here: download and extract (CPU only, beside Phase 13)

* Inputs (downloaded 2026-09-15 with the user's permission; sizes 569,973,037 and 1,704,693 bytes): `replay_data_public.DSK.PremierDraft.csv.gz`
  (570 MB) and `cards/cards.csv` (1.7 MB, id → name) into `rl/data/l17/`
  (gitignored). License/terms not verified yet — confirm before building on it.
* `rl/l17_extract.py`: stream the gzipped CSV in chunks (pandas `chunksize`, only
  the needed columns via `usecols`); keep PremierDraft games from the top
  win-rate buckets; sample **2,000 games** (seeded); for each game write one
  JSON line: expansion, on_play, won, num_mulligans / opp_num_mulligans, the
  user's deck (card name → count), opening hand, cards drawn in order, and per
  turn for both players every recorded field (lands played, creatures cast,
  non-creatures cast, instants/sorceries cast, attacked / blocked / unblocked /
  blocking, killed, damage taken, mana spent, abilities, end-of-turn hand /
  lands / creatures / non-creatures / life), with card ids mapped to names via
  cards.csv. Output `rl/data/l17/DSK_sample2000.jsonl.gz` (expected tens of MB)
  plus `DSK_sample2000.stats.txt` (games, turns, cards, the id-mapping miss
  rate). The per-turn encoding (names vs Arena ids, separator) is fixed by
  reading the real header and first rows before the extractor is finalised.
* Transfer: commit the extract to a data branch `data/l17-dsk` (split into
  < 90 MB parts if needed; GitHub rejects files over 100 MB). No raw 17Lands
  file leaves this machine. (If the repo is ever made public, the extract
  must not go with it until the license is confirmed.)

## 2. In the cloud: build and rebuild

* Environment: Linux, JDK + Maven matching the pinned XMage (the version this
  box builds with — record it), Python 3.10+, ~8 GB RAM, no GPU needed. Clone
  this repo (branch `v7/lane-d` + `data/l17-dsk`) and the pinned XMage source
  at the commit this box uses; apply `rl/xmage-src/*.java` the way
  `rl/sync_lane_b.sh` does; build.
* XMage coverage first: map every card in the 2,000 decks to an XMage card
  class; report the share of games whose whole deck (user side) is implemented;
  only those games are rebuilt.
* Rebuilder (new, Java + Python):
  - user seat: the logged deck; library stacked so the logged opening hand and
    per-turn draws come out exactly; mulligans replayed as logged;
  - opponent seat: a synthetic deck made of the cards it was logged playing plus
    basic-land filler, its library stacked so each card is in hand when it was
    logged cast; its logged plays and attacks forced turn by turn;
  - the user's decisions: at every decision pick an option consistent with the
    turn's logged actions (land, casts, attackers, blockers); where several
    orders are consistent, pick the first and count the ambiguity; block
    assignment chosen to match the logged kills and damage;
  - check after every turn: rebuilt end-of-turn life, lands, creatures,
    non-creatures and hand size against the log; stop at the first mismatch.
* Outputs (committed as text): per game, turns matched before the first
  mismatch and the mismatch field; labels produced per game by decision kind;
  the ambiguity count.

## 3. The fidelity reading (pre-stated)

* **Coverage**: share of sampled games whose user deck is fully in XMage.
* **Fidelity**: median turns matched before the first mismatch; share of games
  matching ≥ 8 turns; which field breaks first, most often.
* **Yield**: labelled decisions per game by kind (land / spell / attack / block),
  and the share that were unambiguous.
* Go / no-go for building it properly: coverage ≥ 0.6 AND ≥ 50 % of covered
  games match ≥ 8 turns. Otherwise record which mismatch dominates and stop.

Cannot: say anything about whether Limited labels help constructed play (that
is the pre-train-then-constructed comparison in rl/IDEA-17LANDS.md, not this
trial); the opponent seat is a reconstruction, so its hidden choices are
guessed.

## 4. What the file actually holds (checked 2026-09-15 on the downloaded DSK file)

* 2,541 columns; turns up to 30 per side. Card lists (opening hand, candidate
  hands per mulligan, per-turn cards drawn / lands played / creatures cast /
  non-creatures cast / instants-sorceries cast / attacked / blocked / blocking /
  killed, and end-of-turn **user** hand, lands, creatures, non-creatures in play)
  are **pipe-separated Arena card ids** (`92216|92181|90190`), mapped by
  `cards.csv` (`id,expansion,name,rarity,color_identity,mana_value,types,is_booster`).
* The user's end-of-turn hand is a full card list; the opponent's hand is a
  count (`6.0`). Life totals are floats. Deck and sideboard are per-card count
  columns (`deck_<name>`, with ", " in names written as two spaces).
* `*_abilities` hold **ability ids** (e.g. `1004|174387`), not card ids; they
  are not in cards.csv (an abilities table would be a separate download).
* Small ids such as `3` appear in creature lists; they are probably tokens
  (unconfirmed; the rebuilder must treat unmapped ids as tokens or unknowns).
* The pinned XMage registers Duskmourn (`DuskmournHouseOfHorror.java`, 417
  `SetCardInfo` lines including variants), so user-deck coverage should be high.

## 5. Mechanism (user choice 2026-09-15: a Claude cloud session)

1. Here: `rl/l17_extract.py` → `rl/data/l17/DSK_top2000.{jsonl.gz,cards.json,stats.txt}`
   (strong-player filter: win-rate bucket ≥ 0.58 and ≥ 50 games; seed 17).
2. Commit only those three files (plus this doc) to branch `data/l17-dsk`
   (branched from `v7/lane-d`, so it carries all code) and push. Raw 17Lands
   files stay on this machine.
3. A remote Claude session is launched on the repo with the runbook in §2:
   check out `data/l17-dsk`, build the engine with `rl/setup_engine.sh`
   (fetches the XMage pin `7554968c` from GitHub, applies
   `rl/engine-patches/phase9-engine.patch`, overlays `rl/xmage-src/`), write the
   coverage check and the rebuilder, run them on the sample, commit the §3
   readings to `rl/L17-FIDELITY.md` on that branch and push.
4. Here: pull the branch and relay. Phase 13 on this box is untouched throughout.

## 6. Status (2026-09-15)

* Sample extracted: 2,000 of 264,720 eligible games (1,011,949 rows read);
  median 9 turns, 1,409 games with ≥ 8 turns; won share 0.62; 887 card ids,
  862 mapped, 25 unmapped (all small ids 0–33, probably tokens).
* **miketanto/CardGuru is a public repo.** The sample (4.1 MB) was pushed to
  branch `data/l17-dsk` (c95d82f) after the user was told it would be public and
  that 17Lands' licence is unverified, and said to push anyway. Raw files stayed
  local.
* Cloud session launched on `data/l17-dsk` with the §2–§3 runbook; results land
  in `rl/L17-FIDELITY.md` and `rl/l17_dsk/fidelity_games.csv` on that branch.
* **Correction (2026-09-15, 13:10 CDT):** the "cloud session" did **not** run in
  the cloud. The launched session is running on this machine's WSL box beside
  Phase 13 (its own rl/L17-FIDELITY.md §1 says so). It built nothing: it compiles
  a private harness against the existing pinned engine at /home/user/mage and
  leaves /home/user/mage and ~/.m2 untouched. It was told to run one JVM
  (-Xmx1536m, serial GC, nice 15), to pause while MemAvailable < 2,000 MB or swap
  > 1 GB, and to stop at 200 games unless that run finishes within ~2 h. So the
  public push of the sample was not needed for this run.
* **Result (2026-09-15, local run, final 19e179b on data/l17-dsk):** coverage
  2000/2000; fidelity NO-GO. Base: median 2 turns matched, 1/2000 ≥ 8 turns
  [0, 0.003], 15/2000 fully matched. Guided: median 3, 4/2000 ≥ 8. Main causes:
  unchecked-state drift making later logged actions impossible 33%, activated
  abilities not replayed 27%, hidden choices ≥ 14%, life-only 13%. Full report:
  rl/L17-FIDELITY.md on data/l17-dsk. Follow-up prompt for a real cloud session:
  rl/L17-CLOUD-HANDOFF.md (updated to this final state).
