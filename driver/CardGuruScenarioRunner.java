package org.mage.test.serverside;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import mage.MageObject;
import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.Mode;
import mage.abilities.Modes;
import mage.abilities.costs.Cost;
import mage.cards.Card;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.target.TargetCard;
import mage.choices.Choice;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.events.GameEvent;
import mage.filter.FilterCard;
import mage.util.CardUtil;
import mage.game.permanent.Permanent;
import mage.game.turn.BeginCombatStep;
import mage.game.turn.BeginningPhase;
import mage.game.turn.CombatDamageStep;
import mage.game.turn.CombatPhase;
import mage.game.turn.DeclareAttackersStep;
import mage.game.turn.PostCombatMainPhase;
import mage.game.turn.PostCombatMainStep;
import mage.game.turn.DrawStep;
import mage.game.turn.EndOfCombatStep;
import mage.game.turn.PreCombatMainPhase;
import mage.game.turn.PreCombatMainStep;
import mage.game.turn.Step;
import mage.game.turn.UntapStep;
import mage.game.turn.UpkeepStep;
import mage.abilities.PlayLandAbility;
import mage.player.ai.score.GameStateEvaluator2;
import mage.players.Player;
import mage.target.Target;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestComputerPlayer7;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.io.BufferedWriter;
import java.io.IOException;
import java.security.MessageDigest;
import mage.counters.Counter;
import mage.counters.CounterType;
import mage.game.events.TableEvent;
import mage.game.permanent.PermanentToken;
import mage.game.stack.Spell;
import mage.game.stack.StackAbility;
import mage.game.stack.StackObject;
import mage.players.ManaPool;

/**
 * CardGuru scenario driver: executes engine-neutral scenario JSON files
 * (see CardGuru docs/scenario-spec.md) through XMage's test harness and
 * writes one outcome JSON per scenario.
 *
 * Usage:
 *   mvn -pl Mage.Tests test -Dtest=CardGuruScenarioRunner \
 *       -Dcardguru.scenarios.dir=/path/to/scenarios \
 *       -Dcardguru.out.dir=/path/to/out
 *
 * All scenarios in the directory run through one JVM (reset() between them).
 * A scenario that fails (unimplemented card, unscripted choice, engine error)
 * produces an outcome with status "error" — it never aborts the batch.
 */
public class CardGuruScenarioRunner extends CardTestPlayerBase {

    /** Replay recorder for the running interactive game (null unless
     *  -Dcardguru.record is set). Read by InteractiveTestPlayer.baseRequest. */
    static volatile GameRecorder recorder;

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    @Test
    public void runScenarios() throws Exception {
        String interactive = System.getProperty("cardguru.interactive.spool");
        if (interactive != null) {
            playInteractive(interactive);
            return;
        }
        String spool = System.getProperty("cardguru.server.spool");
        if (spool != null) {
            serve(spool);
            return;
        }
        String dir = System.getProperty("cardguru.scenarios.dir");
        String outDir = System.getProperty("cardguru.out.dir", dir);
        if (dir == null) {
            System.out.println("[CardGuru] no -Dcardguru.scenarios.dir given; nothing to do");
            return;
        }
        File[] files = new File(dir).listFiles((d, n) -> n.endsWith(".json"));
        if (files == null || files.length == 0) {
            System.out.println("[CardGuru] no scenario files in " + dir);
            return;
        }
        Arrays.sort(files);
        new File(outDir).mkdirs();
        boolean first = true;
        for (File f : files) {
            if (!first) {
                reset();   // fresh game per scenario, same JVM
            }
            first = false;
            JsonObject outcome = runOne(f);
            String name = f.getName().replaceAll("\\.json$", "") + ".out.json";
            try (FileWriter w = new FileWriter(new File(outDir, name))) {
                GSON.toJson(outcome, w);
            }
            System.out.println("[CardGuru] " + f.getName() + " -> "
                    + outcome.get("status").getAsString());
        }
    }

    /**
     * Server mode: keep the JVM (and its ~40s card-database warmup) alive
     * and process scenarios from a spool directory until told to stop.
     *
     * Protocol, all file-based so it works unchanged through maven/JUnit:
     *   spool/in/*.json   scenarios (client writes tmp then renames, atomic)
     *   spool/out/*.out.json  outcomes (written tmp-then-rename likewise)
     *   spool/READY       created once the engine is warm
     *   spool/SHUTDOWN    client creates it; server deletes it and exits
     */
    private void serve(String spool) throws Exception {
        File inDir = new File(spool, "in");
        File outDir = new File(spool, "out");
        inDir.mkdirs();
        outDir.mkdirs();
        new File(spool, "READY").createNewFile();
        System.out.println("[CardGuru] server ready, spool=" + spool);
        boolean first = true;
        while (true) {
            File shutdown = new File(spool, "SHUTDOWN");
            if (shutdown.exists()) {
                shutdown.delete();
                System.out.println("[CardGuru] server shutting down");
                return;
            }
            File[] files = inDir.listFiles((d, n) -> n.endsWith(".json"));
            if (files == null || files.length == 0) {
                Thread.sleep(50);
                continue;
            }
            Arrays.sort(files);
            for (File f : files) {
                if (!first) {
                    reset();
                }
                first = false;
                JsonObject outcome = runOne(f);
                String name = f.getName().replaceAll("\\.json$", "") + ".out.json";
                File tmp = new File(outDir, name + ".tmp");
                try (FileWriter w = new FileWriter(tmp)) {
                    GSON.toJson(outcome, w);
                }
                tmp.renameTo(new File(outDir, name));
                f.delete();
            }
        }
    }

    /**
     * Interactive mode: play ONE real 1v1 game to its natural end, with
     * playerA driven externally through a spool directory and playerB the
     * built-in AI. Unlike the scenario adjudicator this executes no
     * predetermined script — every decision playerA must make (mulligan,
     * priority, attackers, blockers) is serialized to spool/request/<n>.json,
     * the JVM blocks until spool/response/<n>.json appears, and the answer is
     * applied to the live game. The winner lands in spool/result.json.
     *
     * The atomic tmp-then-rename + READY/SHUTDOWN conventions mirror serve().
     * The whole game runs synchronously on this thread (see
     * docs/live-match-feasibility.md), so blocking a decision callback simply
     * parks the game until the external policy answers.
     */
    private void playInteractive(String spool) throws Exception {
        new File(spool, "request").mkdirs();
        new File(spool, "response").mkdirs();
        // playerA is already an InteractiveTestPlayer and playerB a MAD
        // (ComputerPlayer7 alpha-beta) opponent unless -Dcardguru.opp=passive
        // (see createNewPlayer, which reads the same system properties during
        // @Before setup).
        playerB.setAIPlayer(true);   // real built-in AI opponent
        System.out.println("[CardGuru] opponent: "
                + ("passive".equals(System.getProperty("cardguru.opp"))
                        ? "passive (base ComputerPlayer, never acts)"
                        : "MAD ComputerPlayer7 skill "
                          + Integer.getInteger("cardguru.opp.skill", 6)));

        // Optional plumbing scaffold (default off): seat N vanilla blockers on
        // the opponent's battlefield at game start. Built for the passive
        // opponent, whose board never develops on its own, so the minimax
        // min-layer never sees a real blocker to weigh. Pre-placing blockers
        // gives the SEARCH's simulated opponent something to block with, so the
        // min-layer is actually exercised and demonstrable (block_responses >
        // 1). With the MAD opponent this is unnecessary (it develops and blocks
        // by itself) but still honored. See docs/live-minimax.md.
        String oppBlockers = System.getProperty("cardguru.minimax.opp_blockers");
        if (oppBlockers != null) {
            int n = Integer.parseInt(oppBlockers);
            if (n > 0) {
                addCard(Zone.BATTLEFIELD, playerB, "Canyon Minotaur", n);
                System.out.println("[CardGuru][minimax] seated " + n
                        + " opponent blocker(s) for the search to weigh");
            }
        }

        // TestPlayer's endless-loop guard (maxCallsWithoutAction, default 400)
        // counts priority calls that don't mutate the scripted-actions list.
        // A pure-AI player (playerB) never mutates it -- its plays happen
        // inside the wrapped ComputerPlayer -- so the counter accumulates for a
        // whole game and trips mid-match. A real game always terminates on its
        // own (a win, or a deck-out loss), so raise the cap well past any
        // realistic game length. playerA bypasses the guard entirely (its
        // priority() override does not call the base method).
        playerA.setMaxCallsWithoutAction(1_000_000);
        playerB.setMaxCallsWithoutAction(1_000_000);

        new File(spool, "READY").createNewFile();
        System.out.println("[CardGuru] interactive game starting, spool=" + spool);

        JsonObject result = new JsonObject();
        try {
            // Start a REAL game, not the test harness's execute(): testMode
            // suppresses GameImpl's drawHand, so hands only ever come from
            // scenario cheat commands — interactive games started with EMPTY
            // hands, both sides drew up from zero, and canTakeMulligan (hand
            // non-empty) meant chooseMulligan could never fire. With testMode
            // off the engine deals real 7-card hands and runs the actual
            // London mulligan phase, which reaches the spool via
            // chooseMulligan. Mirrors execute()'s essential lines; the cheat
            // block is intentionally dropped (so the opp_blockers scaffold is
            // inert here — it was passive-opponent plumbing anyway).
            for (Player p : currentGame.getPlayers().values()) {
                p.updateRange(currentGame);
            }
            gameOptions.testMode = false;
            gameOptions.stopOnTurn = 200;   // natural end, not a scripted stop
            gameOptions.stopAtStep = PhaseStep.UNTAP;
            currentGame.setGameOptions(gameOptions);
            // Seed the engine RNG when asked. NOTE: this does NOT reproduce
            // the opening hand, and measurement showed it does not:
            // Deck.getMaindeckCards() collects the deck's ordered
            // LinkedHashSet through Collectors.toSet(), so the library is
            // built from a HashSet whose iteration order follows each Card's
            // randomly generated UUID. The seeded shuffle therefore applies
            // the SAME permutation to a DIFFERENT starting order every run.
            // Pinning the deal would require rebuilding the library in a
            // canonical order before the shuffle. What the seed does buy is a
            // deterministic RNG stream for everything after that point.
            String seed = System.getProperty("cardguru.seed");
            if (seed != null && !seed.isEmpty()) {
                // Canonicalise both libraries FIRST. Deck.getMaindeckCards()
                // collects the deck's ordered LinkedHashSet through
                // Collectors.toSet(), so the library is built from a HashSet
                // whose iteration order follows each Card's random UUID —
                // seeding alone therefore applied the same permutation to a
                // different starting order every run (measured: two runs at
                // seed 777 dealt different hands). Sorting by name makes the
                // pre-shuffle order identical across runs; copies of one card
                // are interchangeable, so name order is enough to pin the
                // dealt hand.
                for (mage.players.Player p : currentGame.getPlayers().values()) {
                    mage.players.Library lib = p.getLibrary();
                    List<Card> ordered = new ArrayList<>(lib.getCards(currentGame));
                    ordered.sort(java.util.Comparator.comparing(Card::getName));
                    lib.clear();
                    for (Card c : ordered) {
                        lib.putOnBottom(c, currentGame);
                    }
                    System.out.println("[CardGuru] canonicalised library for "
                            + p.getName() + " (" + ordered.size() + " cards)");
                }
                mage.util.RandomUtil.setSeed(Long.parseLong(seed.trim()));
                System.out.println("[CardGuru] seeded shuffle with " + seed);
            }
            String recPath = System.getProperty("cardguru.record");
            if (recPath != null && !recPath.isEmpty()) {
                JsonObject meta = new JsonObject();
                JsonObject players = new JsonObject();
                JsonObject pa = new JsonObject();
                pa.addProperty("id", playerA.getId().toString());
                pa.addProperty("name", playerA.getName());
                JsonObject pb = new JsonObject();
                pb.addProperty("id", playerB.getId().toString());
                pb.addProperty("name", playerB.getName());
                players.add("A", pa);
                players.add("B", pb);
                meta.add("players", players);
                meta.addProperty("deck_a", deckNameA);
                meta.addProperty("deck_b", deckNameB);
                meta.addProperty("seed", seed);
                JsonObject props = new JsonObject();
                for (String k : System.getProperties().stringPropertyNames()) {
                    if (k.startsWith("cardguru.")) {
                        props.addProperty(k, System.getProperty(k));
                    }
                }
                meta.add("props", props);
                recorder = new GameRecorder(recPath, playerA.getId(), playerB.getId(), meta);
                final GameRecorder rec = recorder;
                final Game liveGame = currentGame;
                currentGame.addTableEventListener(ev -> {
                    try {
                        TableEvent.EventType t = ev.getEventType();
                        if (t == TableEvent.EventType.INFO || t == TableEvent.EventType.STATUS) {
                            Game g = ev.getGame() != null ? ev.getGame() : liveGame;
                            if (!g.isSimulation()) {
                                rec.event(g, t.name(), ev.getMessage());
                            }
                        }
                    } catch (RuntimeException e) {
                        rec.noteError(e);   // recording must never break the game
                    }
                });
                System.out.println("[CardGuru] recording replay to " + recPath);
            }
            currentGame.start(playerA.getId());
            result.addProperty("status", "completed");
        } catch (Throwable e) {
            result.addProperty("status", "error");
            result.addProperty("error", e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        if (currentGame != null && currentGame.hasEnded()) {
            String w = String.valueOf(currentGame.getWinner());
            if (w.contains(playerA.getName())) {
                result.addProperty("winner", "A");
            } else if (w.contains(playerB.getName())) {
                result.addProperty("winner", "B");
            }
        }
        result.addProperty("turns", currentGame != null ? currentGame.getTurnNum() : 0);
        if (recorder != null) {
            try {
                recorder.end(currentGame, result);
            } catch (RuntimeException e) {
                System.out.println("[CardGuru] recorder end failed: " + e);
            }
            recorder = null;
        }

        File tmp = new File(spool, "result.json.tmp");
        try (FileWriter w = new FileWriter(tmp)) {
            GSON.toJson(result, w);
        }
        tmp.renameTo(new File(spool, "result.json"));
        // DONE sentinel: unblocks a client that is polling for the next request.
        new File(spool, "DONE").createNewFile();
        System.out.println("[CardGuru] interactive game over: " + result);
    }

    /**
     * Seat playerA as an externally-driven player when interactive mode is
     * active. Called from the @Before setup (createNewGameAndPlayers ->
     * createPlayer -> createNewPlayer) before the test body runs, so the
     * decision comes from the system property, not the test method.
     */
    /**
     * Interactive games need a deck with actual creatures on both sides, or no
     * combat (and so no attack decision to search) ever happens. The harness
     * default "RB Aggro.dck" is a misnomer -- it is 71 Mountains, zero
     * creatures -- so an interactive match just decks out over ~144 turns with
     * nobody attacking. For interactive mode we write a small real mono-red
     * aggro list to a temp file and seat BOTH players with it: playerA gets
     * attackers to search over, and playerB gets creatures so the simulated
     * min-layer has real blockers to weigh. Scenario/server modes are untouched
     * (they build their own battlefields via addCard).
     */
    @Override
    protected Game createNewGameAndPlayers()
            throws mage.game.GameException, java.io.FileNotFoundException {
        if (System.getProperty("cardguru.interactive.spool") != null) {
            // Real constructed decks: -Dcardguru.deck.a / -Dcardguru.deck.b
            // point at .dck files (the Python side converts meta_decks/*.json).
            // Either seat falls back to the mono-red plumbing deck.
            String deckA = System.getProperty("cardguru.deck.a");
            String deckB = System.getProperty("cardguru.deck.b");
            String fallback = (deckA == null || deckB == null)
                    ? writeInteractiveDeck() : null;
            deckNameA = deckA != null ? deckA : fallback;
            deckNameB = deckB != null ? deckB : fallback;
            System.out.println("[CardGuru] decks: A="
                    + new File(deckNameA).getName()
                    + " B=" + new File(deckNameB).getName());
        }
        return super.createNewGameAndPlayers();
    }

    /** Write the interactive plumbing deck to a temp .dck and return its path.
     *  Set codes are placeholders; DckDeckImporter falls back to name search. */
    private String writeInteractiveDeck() {
        String contents = String.join("\n",
                "NAME:CardGuru Mono-Red Aggro (plumbing)",
                "24 [M15:1] Mountain",
                "8 [M15:1] Raging Goblin",
                "8 [M15:1] Goblin Raider",
                "8 [M15:1] Onakke Ogre",
                "6 [M15:1] Canyon Minotaur",
                "6 [M15:1] Hill Giant",
                "");
        try {
            File f = File.createTempFile("cardguru-aggro-", ".dck");
            f.deleteOnExit();
            try (FileWriter w = new FileWriter(f)) {
                w.write(contents);
            }
            return f.getAbsolutePath();
        } catch (Exception e) {
            throw new RuntimeException("cannot write interactive deck", e);
        }
    }

    /**
     * The AI opponent, with mulligans restored.
     *
     * ComputerPlayer.chooseMulligan short-circuits to "keep" whenever
     * isTestMode() is set, and the test framework sets it on every player it
     * creates (CardTestPlayerAPIImpl.createPlayer). The AI therefore kept
     * EVERY opening hand in every game this harness has ever run, including
     * one-landers, while our own pilot mulliganed normally over the spool —
     * a systematic handicap on the opponent that inflates our win rate.
     * This re-applies the engine's own rule without the test bypass.
     */
    private static final class MulliganingTestPlayer extends TestPlayer {
        MulliganingTestPlayer(TestComputerPlayer7 ai) {
            super(ai);
        }

        @Override
        public boolean chooseMulligan(Game game) {
            if (getHand().size() < 6) {
                return false;
            }
            Set<Card> lands = getHand().getCards(
                    new mage.filter.common.FilterLandCard(), game);
            return lands.size() < 2 || lands.size() > getHand().size() - 2;
        }
    }

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence range) {
        String spool = System.getProperty("cardguru.interactive.spool");
        if (spool != null && playerName.equals("PlayerA")) {
            // cardguru.minimax=attacks turns on the in-driver simulation-backed
            // search at the declare-attackers decision (see InteractiveTestPlayer
            // and docs/live-minimax.md). cardguru.minimax=llm runs the same
            // rollouts at BOTH combat decisions but scores the leaves through a
            // "leaf_eval" spool request (PokeChamp arm (d): the LLM is the value
            // function). Any other value leaves combat on the external spool
            // policy like the other decisions.
            return new InteractiveTestPlayer(new TestComputerPlayer(playerName, range),
                    spool, System.getProperty("cardguru.minimax"));
        }
        if (spool != null && playerName.equals("PlayerB")
                && !"passive".equals(System.getProperty("cardguru.opp"))) {
            // Interactive opponent: the REAL alpha-beta AI (ComputerPlayer7
            // from mage-player-ai-mad, on the test classpath transitively via
            // mage-server), seated exactly the way XMage's own
            // CardTestPlayerBaseAI does it. Without this the opponent is the
            // base TestComputerPlayer, whose priority() just passes -- every
            // live "win" was integration proof only. -Dcardguru.opp=passive
            // restores that old opponent; -Dcardguru.opp.skill sets the
            // simulation depth (XMage default 6).
            int skill = Integer.getInteger("cardguru.opp.skill", 6);
            TestComputerPlayer7 ai = new TestComputerPlayer7(playerName, range, skill);
            // MAD cuts its alpha-beta off on WALL CLOCK (skill * 3 = 18s at
            // the default), so the opponent silently gets weaker whenever the
            // machine is busy and results stop being comparable across runs.
            // Raising the time limit lets the existing 5000-node cap
            // (MAX_SIMULATED_NODES_PER_CALC, checked independently) bind
            // instead, making opponent strength a property of the config
            // rather than of the load. -Dcardguru.opp.think_secs=18 restores
            // the stock time-bounded behaviour.
            ai.setMaxThinkTimeSecs(
                    Integer.getInteger("cardguru.opp.think_secs", 3600));
            TestPlayer opp = new MulliganingTestPlayer(ai);
            opp.setAIPlayer(true);   // full AI: simulations drive every priority
            return opp;
        }
        return super.createNewPlayer(playerName, range);
    }

    private JsonObject runOne(File file) {
        JsonObject out = new JsonObject();
        long t0 = System.currentTimeMillis();
        JsonObject spec;
        try (FileReader r = new FileReader(file)) {
            spec = JsonParser.parseReader(r).getAsJsonObject();
        } catch (Exception e) {
            out.addProperty("status", "error");
            out.addProperty("error", "unreadable scenario: " + e);
            return out;
        }
        out.addProperty("id", spec.has("id") ? spec.get("id").getAsString() : file.getName());
        out.addProperty("engine", "xmage");
        try {
            setup(spec);
            script(spec);
            JsonObject stop = spec.getAsJsonObject("stop");
            setStrictChooseMode(true);
            setStopAt(stop.get("turn").getAsInt(),
                    PhaseStep.valueOf(stop.get("phase").getAsString()));
            execute();
            out.addProperty("status", "executed");
            out.add("expectations", checkExpectations(spec));
            out.add("state", readState());
            addWinner(out);
        } catch (Throwable e) {   // AssertionError (strict mode) or engine exception
            // Winner short-circuit: a line may legally end the game before its
            // trailing scripted actions (e.g. a wait_stack queued after the
            // lethal spell). The leftover-actions assertion then fires even
            // though every decision that could execute did. That is a scoring
            // artifact, not a rules violation - report the finished game.
            if (currentGame != null && currentGame.hasEnded()
                    && String.valueOf(e.getMessage()).contains("must have 0 actions")) {
                out.addProperty("status", "executed");
                out.addProperty("note",
                        "game ended before trailing scripted actions; leftovers ignored");
                out.add("expectations", checkExpectations(spec));
                out.add("state", readState());
                addWinner(out);
            } else {
                out.addProperty("status", "error");
                out.addProperty("error", e.getClass().getSimpleName() + ": " + e.getMessage());
            }
        }
        out.addProperty("millis", System.currentTimeMillis() - t0);
        return out;
    }

    /** "A"/"B" when the game has ended with a winner, absent otherwise. */
    private void addWinner(JsonObject out) {
        if (currentGame == null || !currentGame.hasEnded()) {
            return;
        }
        String w = String.valueOf(currentGame.getWinner());
        if (w.contains(playerA.getName())) {
            out.addProperty("winner", "A");
        } else if (w.contains(playerB.getName())) {
            out.addProperty("winner", "B");
        }
    }

    // ------------------------------------------------------------ setup

    private TestPlayer player(String key) {
        return key.equals("B") ? playerB : playerA;
    }

    private void setup(JsonObject spec) {
        JsonObject players = spec.getAsJsonObject("players");
        boolean skipShuffle = false;
        for (String key : players.keySet()) {
            TestPlayer p = player(key);
            JsonObject cfg = players.getAsJsonObject(key);
            if (cfg.has("life")) {
                setLife(p, cfg.get("life").getAsInt());
            }
            for (JsonElement e : arr(cfg, "battlefield")) {
                JsonObject b = e.getAsJsonObject();
                addCard(Zone.BATTLEFIELD, p, b.get("card").getAsString(),
                        b.has("count") ? b.get("count").getAsInt() : 1,
                        b.has("tapped") && b.get("tapped").getAsBoolean());
            }
            for (JsonElement e : arr(cfg, "hand")) {
                addCard(Zone.HAND, p, e.getAsString());
            }
            for (JsonElement e : arr(cfg, "graveyard")) {
                addCard(Zone.GRAVEYARD, p, e.getAsString());
            }
            for (JsonElement e : arr(cfg, "exile")) {
                addCard(Zone.EXILED, p, e.getAsString());
            }
            JsonArray top = arr(cfg, "library_top");
            for (int i = top.size() - 1; i >= 0; i--) {   // last added = top
                addCard(Zone.LIBRARY, p, top.get(i).getAsString());
                skipShuffle = true;
            }
        }
        if (skipShuffle) {
            skipInitShuffling();
        }
    }

    private void script(JsonObject spec) {
        for (JsonElement e : arr(spec, "actions")) {
            JsonObject a = e.getAsJsonObject();
            String kind = a.get("do").getAsString();
            switch (kind) {
                case "cast":
                    if (a.has("target_player")) {
                        castSpell(a.get("turn").getAsInt(), phase(a),
                                player(a.get("player").getAsString()),
                                a.get("card").getAsString(),
                                player(a.get("target_player").getAsString()));
                    } else if (a.has("spell_on_stack")) {
                        castSpell(a.get("turn").getAsInt(), phase(a),
                                player(a.get("player").getAsString()),
                                a.get("card").getAsString(),
                                a.has("target_card") ? a.get("target_card").getAsString() : null,
                                a.get("spell_on_stack").getAsString());
                    } else if (a.has("target_card")) {
                        castSpell(a.get("turn").getAsInt(), phase(a),
                                player(a.get("player").getAsString()),
                                a.get("card").getAsString(),
                                a.get("target_card").getAsString());
                    } else {
                        castSpell(a.get("turn").getAsInt(), phase(a),
                                player(a.get("player").getAsString()),
                                a.get("card").getAsString());
                    }
                    break;
                case "play_land":
                    playLand(a.get("turn").getAsInt(), phase(a),
                            player(a.get("player").getAsString()),
                            a.get("card").getAsString());
                    break;
                case "activate":
                    activateAbility(a.get("turn").getAsInt(), phase(a),
                            player(a.get("player").getAsString()),
                            a.get("ability").getAsString());
                    break;
                case "attack":
                    attack(a.get("turn").getAsInt(),
                            player(a.get("player").getAsString()),
                            a.get("attacker").getAsString());
                    break;
                case "block":
                    block(a.get("turn").getAsInt(),
                            player(a.get("player").getAsString()),
                            a.get("blocker").getAsString(),
                            a.get("attacker").getAsString());
                    break;
                case "wait_stack":
                    waitStackResolved(a.get("turn").getAsInt(), phase(a));
                    break;
                case "choice":
                    setChoice(player(a.get("player").getAsString()),
                            a.get("value").getAsString());
                    break;
                case "target":
                    String tval = a.get("value").getAsString();
                    if (tval.equals("PlayerA") || tval.equals("PlayerB")) {
                        // player targets must be queued as player objects
                        addTarget(player(a.get("player").getAsString()),
                                player(tval.substring(6)));
                    } else {
                        addTarget(player(a.get("player").getAsString()), tval);
                    }
                    break;
                case "mode":
                    setModeChoice(player(a.get("player").getAsString()),
                            a.get("value").getAsString());
                    break;
                default:
                    throw new IllegalArgumentException("unknown action: " + kind);
            }
        }
    }

    private PhaseStep phase(JsonObject a) {
        return PhaseStep.valueOf(a.get("phase").getAsString());
    }

    private static JsonArray arr(JsonObject o, String key) {
        return o.has(key) ? o.getAsJsonArray(key) : new JsonArray();
    }

    // ------------------------------------------------------ expectations

    private JsonArray checkExpectations(JsonObject spec) {
        JsonArray results = new JsonArray();
        for (JsonElement e : arr(spec, "expect")) {
            JsonObject x = e.getAsJsonObject();
            JsonObject res = new JsonObject();
            res.addProperty("check", x.get("check").getAsString());
            try {
                applyCheck(x);
                res.addProperty("pass", true);
            } catch (AssertionError err) {
                res.addProperty("pass", false);
                res.addProperty("detail", String.valueOf(err.getMessage()));
            }
            results.add(res);
        }
        return results;
    }

    private void applyCheck(JsonObject x) {
        String check = x.get("check").getAsString();
        TestPlayer p = x.has("player") ? player(x.get("player").getAsString()) : playerA;
        switch (check) {
            case "permanent_count":
                assertPermanentCount(p, x.get("card").getAsString(), x.get("count").getAsInt());
                break;
            case "exile_count":
                assertExileCount(p, x.get("card").getAsString(), x.get("count").getAsInt());
                break;
            case "graveyard_count":
                assertGraveyardCount(p, x.get("card").getAsString(), x.get("count").getAsInt());
                break;
            case "battlefield_count":
                int n = currentGame.getBattlefield().getAllActivePermanents(p.getId()).size();
                if (n != x.get("count").getAsInt()) {
                    throw new AssertionError("battlefield_count: expected "
                            + x.get("count").getAsInt() + ", got " + n);
                }
                break;
            case "hand_count":
                assertHandCount(p, x.get("count").getAsInt());
                break;
            case "life":
                assertLife(p, x.get("value").getAsInt());
                break;
            case "tapped":
                assertTapped(x.get("card").getAsString(), x.get("value").getAsBoolean());
                break;
            case "power_toughness":
                assertPowerToughness(p, x.get("card").getAsString(),
                        x.get("power").getAsInt(), x.get("toughness").getAsInt());
                break;
            default:
                throw new AssertionError("unknown check: " + check);
        }
    }

    // ------------------------------------------------------------ state

    private JsonObject readState() {
        JsonObject state = new JsonObject();
        state.add("A", playerState(playerA));
        state.add("B", playerState(playerB));
        return state;
    }

    private JsonObject playerState(TestPlayer p) {
        JsonObject s = new JsonObject();
        s.addProperty("life", p.getLife());
        JsonArray bf = new JsonArray();
        for (Permanent perm : currentGame.getBattlefield().getAllActivePermanents(p.getId())) {
            JsonObject o = new JsonObject();
            o.addProperty("name", perm.getName());
            o.addProperty("tapped", perm.isTapped());
            if (perm.isCreature(currentGame)) {
                o.addProperty("power", perm.getPower().getValue());
                o.addProperty("toughness", perm.getToughness().getValue());
            }
            bf.add(o);
        }
        s.add("battlefield", bf);
        JsonArray gy = new JsonArray();
        for (Card c : p.getGraveyard().getCards(currentGame)) {
            gy.add(c.getName());
        }
        s.add("graveyard", gy);
        JsonArray ex = new JsonArray();
        for (Card c : currentGame.getExile().getAllCards(currentGame)) {
            if (c.isOwnedBy(p.getId())) {
                ex.add(c.getName());
            }
        }
        s.add("exile", ex);
        s.addProperty("hand_count", p.getHand().size());
        return s;
    }
}

/**
 * A TestPlayer whose top-level decisions come from outside the JVM.
 *
 * Non-strict TestPlayer already routes unscripted sub-choices (spell targets,
 * mana payment, X, modes) to its wrapped ComputerPlayer -- see
 * chooseStrictModeFailed, a no-op when canChooseByComputer() (i.e. not strict).
 * So only the four decisions the base class does NOT delegate need overriding
 * here: priority, attackers, blockers, mulligan. Each override serializes the
 * request + observable state to spool/request/<seq>.json and blocks reading
 * spool/response/<seq>.json, then applies the answer with the very same engine
 * primitives the base harness uses (getPlayable/activateAbility,
 * declareAttacker, declareBlocker).
 *
 * MVP boundary (docs/live-match-feasibility.md): in-cast target/mana/X are the
 * AI's for now; the top-level line is the external policy's.
 */
class InteractiveTestPlayer extends TestPlayer {

    private static final Gson GSON = new Gson();
    // Must exceed the Python bridge's own escalation timeout (240s default) —
    // the bridge ALWAYS answers by then (dumb_policy fallback), so the only
    // way this fires is a dead bridge.
    private static final long DECISION_TIMEOUT_MS = 300_000;

    private final String spool;
    private final String minimaxMode;   // null | "attacks" | "llm"
    private int seq = 0;

    /** True on a simulation copy of this player (see copy()). */
    private final boolean simCopy;

    InteractiveTestPlayer(TestComputerPlayer computerPlayer, String spool,
                          String minimaxMode) {
        super(computerPlayer);
        this.spool = spool;
        this.minimaxMode = minimaxMode;
        this.simCopy = false;
    }

    /** Simulation copy. The engine copies players through copy(), and
     *  TestPlayer's version returned a plain TestPlayer, so no driver hook
     *  ever ran inside a rollout: every sub-choice in a leaf was the built-in
     *  AI's. Copies keep the hooks but never reach ask(): `searching` is
     *  pinned true and `simCopy` routes sub-choices to the active script. */
    private InteractiveTestPlayer(InteractiveTestPlayer other) {
        super(other);
        this.spool = other.spool;
        this.minimaxMode = other.minimaxMode;
        this.simCopy = true;
        this.searching = true;
    }

    @Override
    public TestPlayer copy() {
        return new InteractiveTestPlayer(this);
    }

    /** Write the request atomically, block for the response, return it. */
    private JsonObject ask(JsonObject request) {
        seq++;
        request.addProperty("seq", seq);
        File reqDir = new File(spool, "request");
        File respDir = new File(spool, "response");
        reqDir.mkdirs();
        respDir.mkdirs();
        File tmp = new File(reqDir, seq + ".json.tmp");
        try (FileWriter w = new FileWriter(tmp)) {
            GSON.toJson(request, w);
        } catch (Exception e) {
            throw new RuntimeException("interactive: cannot write request " + seq, e);
        }
        tmp.renameTo(new File(reqDir, seq + ".json"));

        File resp = new File(respDir, seq + ".json");
        long deadline = System.currentTimeMillis() + DECISION_TIMEOUT_MS;
        while (!resp.exists()) {
            if (new File(spool, "SHUTDOWN").exists()) {
                throw new RuntimeException("interactive: SHUTDOWN while awaiting response " + seq);
            }
            if (System.currentTimeMillis() > deadline) {
                throw new RuntimeException("interactive: timed out awaiting response " + seq);
            }
            try {
                Thread.sleep(20);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("interactive: interrupted awaiting response " + seq, ie);
            }
        }
        JsonObject out;
        try (FileReader r = new FileReader(resp)) {
            out = JsonParser.parseReader(r).getAsJsonObject();
        } catch (Exception e) {
            throw new RuntimeException("interactive: cannot read response " + seq, e);
        }
        resp.delete();
        return out;
    }

    private JsonObject baseRequest(String kind, Game game) {
        JsonObject req = new JsonObject();
        req.addProperty("kind", kind);
        GameRecorder rec = CardGuruScenarioRunner.recorder;
        if (rec != null && !game.isSimulation()) {
            req.addProperty("snapshot_id", rec.snapshot(game, "request:" + kind, true));
        }
        req.addProperty("turn", game.getTurnNum());
        req.addProperty("phase", String.valueOf(game.getTurnStepType()));
        // Sub-choices can fire pre-game (mulligan-time scry, opening choices)
        // when there is no active player yet.
        UUID activeId = game.getActivePlayerId();
        req.addProperty("active", activeId == null ? "-"
                : activeId.equals(this.getId()) ? "A" : "B");
        // What we could actually pay this window. The state lists which lands
        // are untapped, but never what that adds up to, so the pilot was
        // reasoning about affordability from a board read — and got it wrong
        // in the direction that matters (committing to casts it could not
        // pay for). State it outright.
        req.addProperty("mana_available", manaSignature(game));
        req.add("state", observableState(game));
        // The stack, top last, so the bridge's turn planner can see "they
        // cast X" without a search leaf. Leaves already carry the same.
        JsonArray stack = new JsonArray();
        for (mage.game.stack.StackObject so : game.getStack()) {
            // Card types ride along: a spell cast from their hand has never
            // been in card_reference, and the planner's "they_cast:creature"
            // rule needs to classify it without a lookup.
            String types = "";
            try {
                types = " [" + String.join(" ", so.getCardType(game).stream()
                        .map(Object::toString).toArray(String[]::new)) + "]";
            } catch (RuntimeException ignored) {
                // triggered abilities and the like: no card type, no tag
            }
            stack.add(so.getName() + " (" + (so.getControllerId().equals(this.getId())
                    ? "ours" : "theirs") + ")" + types);
        }
        req.add("stack", stack);
        return req;
    }

    /** Turn-plan mode: no per-window search; the bridge executes a plan
     *  the pilot wrote once per turn and asks only for uncovered windows. */
    private static final boolean turnPlanMode = Boolean.getBoolean("cardguru.turn_plan");
    /** In turn-plan mode, keep the per-decision attack/block searches (one
     *  leaf_eval per combat) — the first pure-plan game chose attack_none in
     *  11 of 15 turns with nothing simulated behind it. Off = pure plan. */
    private static final boolean planCombatSearch =
            !"false".equals(System.getProperty("cardguru.plan_combat_search", "true"));

    /** Supertypes + card types, e.g. "[Legendary] [Planeswalker]".
     *
     * getCardType() alone drops supertypes, so LEGENDARY never reached the
     * pilot: in mirror game 3 it cast a second Kaito while already
     * controlling one (turn 9), hit the legend rule, and had to bin a
     * four-mana card it had just paid for. Nothing it was sent said Kaito
     * was legendary — not the type line, not the rules text. */
    // Null-tolerant readers for pilot replies. A model can answer
    // {"choice": null} or {"targets": [null]}; Gson's getAsInt() on a
    // JsonNull throws, and one such reply killed a 69-minute game. Anything
    // that is not a number reads as the default, which every caller treats
    // as "no valid pick" and falls through to its existing fallback.
    private static int intOf(JsonElement e, int def) {
        if (e == null || e.isJsonNull() || !e.isJsonPrimitive()) {
            return def;
        }
        try {
            return e.getAsInt();
        } catch (RuntimeException ex) {
            return def;
        }
    }

    private static int intOr(JsonObject o, String key, int def) {
        return o != null && o.has(key) ? intOf(o.get(key), def) : def;
    }

    private static JsonArray arrOr(JsonObject o, String key) {
        if (o != null && o.has(key) && o.get(key).isJsonArray()) {
            return o.getAsJsonArray(key);
        }
        return new JsonArray();
    }

    private static String typeLine(MageObject o, Game game) {
        String sup = String.valueOf(o.getSuperType(game));
        String types = String.valueOf(o.getCardType(game));
        return "[]".equals(sup) ? types : sup + " " + types;
    }

    /** Both players' public state, plus this (driven) player's own hand.
     *  Cards render with cost, types, and rules text (like the puzzle
     *  encoder) — an LLM policy cannot be assumed to know cards by name,
     *  and game three was misplayed off a misremembered casting cost. */
    private JsonObject observableState(Game game) {
        JsonObject state = new JsonObject();
        for (UUID pid : game.getPlayerList()) {
            mage.players.Player p = game.getPlayer(pid);
            if (p == null) {
                continue;
            }
            JsonObject s = new JsonObject();
            s.addProperty("life", p.getLife());
            JsonArray bf = new JsonArray();
            for (Permanent perm : game.getBattlefield().getAllActivePermanents(pid)) {
                JsonObject o = new JsonObject();
                o.addProperty("name", perm.getName());
                o.addProperty("tapped", perm.isTapped());
                if (perm.isCreature(game)) {
                    o.addProperty("power", perm.getPower().getValue());
                    o.addProperty("toughness", perm.getToughness().getValue());
                    // "can it attack right now" fact the LLM needs
                    o.addProperty("summoning_sick", perm.hasSummoningSickness());
                    // Engine-computed, so the pilot never has to infer it:
                    // summoning-sick creatures CAN block (batch-1 game 2 was
                    // misplayed off the opposite belief); only tapped ones
                    // cannot.
                    o.addProperty("can_block", !perm.isTapped());
                    // The booleans alone did not stop the pilot from writing
                    // "summoning sick, can't block" (campaign g3 T5), so the
                    // same facts also go out as an unambiguous sentence.
                    o.addProperty("status",
                            (perm.isTapped() ? "TAPPED - CANNOT BLOCK"
                                    : "untapped - CAN BLOCK")
                            + (perm.hasSummoningSickness()
                                    ? "; summoning sick (cannot attack, but "
                                      + "blocking is unaffected)" : ""));
                    // Combat facts for the bridge's turn planner ("they
                    // block X" / "X unblocked" events) and for the pilot.
                    try {
                        mage.game.combat.Combat combat = game.getCombat();
                        if (combat != null && combat.getAttackers().contains(perm.getId())) {
                            o.addProperty("attacking", true);
                        }
                        if (combat != null) {
                            JsonArray blocking = new JsonArray();
                            for (mage.game.combat.CombatGroup g : combat.getGroups()) {
                                if (g.getBlockers().contains(perm.getId())) {
                                    for (UUID aid : g.getAttackers()) {
                                        Permanent atk = game.getPermanent(aid);
                                        blocking.add(atk == null ? "?" : atk.getName());
                                    }
                                }
                            }
                            if (blocking.size() > 0) {
                                o.add("blocking", blocking);
                            }
                        }
                    } catch (RuntimeException ignored) {
                        // combat facts are advisory; never break a request
                    }
                }
                o.addProperty("cost", perm.getManaCost().getText());
                o.addProperty("types", typeLine(perm, game));
                String rules = String.join(" ; ", perm.getRules(game));
                if (!rules.isEmpty()) {
                    o.addProperty("text", rules);
                }
                bf.add(o);
            }
            s.add("battlefield", bf);
            JsonArray gy = new JsonArray();
            for (Card c : p.getGraveyard().getCards(game)) {
                gy.add(c.getName());
            }
            s.add("graveyard", gy);
            s.addProperty("hand_count", p.getHand().size());
            if (pid.equals(this.getId())) {
                JsonArray hand = new JsonArray();
                for (Card c : p.getHand().getCards(game)) {
                    JsonObject o = new JsonObject();
                    o.addProperty("name", c.getName());
                    o.addProperty("cost", c.getManaCost().getText());
                    o.addProperty("types", typeLine(c, game));
                    if (c.isCreature(game)) {
                        o.addProperty("power", c.getPower().getValue());
                        o.addProperty("toughness", c.getToughness().getValue());
                    }
                    String rules = String.join(" ; ", c.getRules(game));
                    if (!rules.isEmpty()) {
                        o.addProperty("text", rules);
                    }
                    hand.add(o);
                }
                s.add("hand", hand);
            }
            state.add(pid.equals(this.getId()) ? "A" : "B", s);
        }
        return state;
    }

    @Override
    public boolean chooseMulligan(Game game) {
        JsonObject req = baseRequest("mulligan", game);
        req.addProperty("hand_count", getComputerPlayer().getHand().size());
        JsonObject resp = ask(req);
        return resp.has("mulligan") && resp.get("mulligan").getAsBoolean();
    }

    @Override
    public boolean priority(Game game) {
        if (searching) {
            return super.priority(game);
        }
        String manaSig = manaSignature(game);
        List<ActivatedAbility> playable = dropUnaffordable(
                getComputerPlayer().getPlayable(game, true, Zone.ALL, false),
                manaSig);
        if (("llm".equals(minimaxMode) && !turnPlanMode)) {
            List<ActivatedAbility> real = new ArrayList<>();
            for (ActivatedAbility a : playable) {
                if (!(a instanceof mage.abilities.mana.ManaAbility)) {
                    real.add(a);
                }
            }
            // Search the decision that actually shapes the turn: which spell
            // to cast (or whether to hold), with at least one real choice
            // beyond passing. Mana abilities are noise — casting auto-taps.
            if (!real.isEmpty()) {
                int verdict = llmSearchPriority(game, real, manaSig);
                if (verdict > 0) {
                    return true;            // the search activated something
                }
                if (verdict == 0) {
                    // The search — the pilot's own leaf scores — chose to
                    // hold. Escalating the same window again just asks it the
                    // identical question a second time; that double-ask was
                    // 15% of every pilot call in mirror game 2.
                    getComputerPlayer().pass(game);
                    return false;
                }
                // verdict < 0: no LLM scores, fall through to escalation.
            }
        }
        JsonObject req = baseRequest("priority", game);
        JsonArray opts = new JsonArray();
        JsonObject pass = new JsonObject();
        pass.addProperty("index", 0);
        pass.addProperty("action", "pass");
        pass.addProperty("text", "pass priority");
        opts.add(pass);
        int i = 1;
        for (ActivatedAbility a : playable) {
            JsonObject o = new JsonObject();
            o.addProperty("index", i++);
            o.addProperty("action", "activate");
            o.addProperty("text", String.valueOf(a));
            opts.add(o);
        }
        req.add("options", opts);

        JsonObject resp = ask(req);
        if (turnPlanMode && planSearchOn && resp.has("simulate")
                && resp.get("simulate").isJsonArray()
                && resp.getAsJsonArray("simulate").size() > 0) {
            resp = planSearch(game, req, resp);
        }
        int choice = intOr(resp, "choice", 0);
        if (choice >= 1 && choice <= playable.size()) {
            ActivatedAbility picked = playable.get(choice - 1);
            if (getComputerPlayer().activateAbility(picked.copy(), game)) {
                return true;
            }
            unaffordableMemo.add(manaSig + "|" + picked);
        }
        getComputerPlayer().pass(game);
        return false;
    }

    // ---- in-cast sub-choices (targets / X / modes / yes-no / named) ------
    //
    // Non-strict TestPlayer routes these to the wrapped ComputerPlayer, so
    // until now targeted spells were the AI's choice even when the external
    // policy picked the cast (the "last blocker" in
    // docs/live-match-feasibility.md). With -Dcardguru.subchoices=external
    // they go over the spool instead: each fires nested inside the
    // activateAbility a priority answer triggered, and since the whole game
    // runs synchronously on this thread a nested ask() is just one more
    // round-trip. Trivial picks (<=1 legal option, or X where min==max) stay
    // with the AI to keep chatter down; a malformed/underfilled answer falls
    // back to the AI too (logged), so a bad policy answer degrades instead of
    // wedging the game.

    private final boolean externalSubchoices =
            "external".equals(System.getProperty("cardguru.subchoices"));

    /** True while a search rollout is running on a simulation copy. Every
     *  externalized decision must fall back to the built-in AI then: a copy
     *  of this player lives in the sim, and letting it reach ask() would
     *  spawn nested spool requests for imaginary game states (and recurse,
     *  since scoring a leaf can itself require a decision). */
    private boolean searching = false;

    private JsonObject describeTargetOption(int index, UUID id, Game game) {
        JsonObject o = new JsonObject();
        o.addProperty("index", index);
        mage.players.Player p = game.getPlayer(id);
        if (p != null) {
            String owner = p.getId().equals(getId()) ? "A" : "B";
            o.addProperty("kind", "player");
            o.addProperty("owner", owner);
            o.addProperty("text", "player " + owner + " (life " + p.getLife() + ")");
            return o;
        }
        Permanent perm = game.getPermanent(id);
        if (perm != null) {
            String owner = perm.getControllerId().equals(getId()) ? "A" : "B";
            String text = perm.getName();
            if (perm.isCreature(game)) {
                text += " " + perm.getPower().getValue()
                        + "/" + perm.getToughness().getValue();
            }
            o.addProperty("kind", "permanent");
            o.addProperty("owner", owner);
            o.addProperty("text", text + " (" + owner + ")");
            return o;
        }
        MageObject obj = game.getObject(id);
        o.addProperty("kind", "object");
        o.addProperty("text", obj != null ? obj.getName() : String.valueOf(id));
        return o;
    }

    // ---- sub-choice menus ---------------------------------------------------
    //
    // Every sub-choice prompt (targets, card picks, scry/surveil, yes/no,
    // modes, X) is described as a SubMenu with stable option keys. The REAL
    // player first replays the search's chosen script (pendingScript), then
    // asks the pilot. A SIMULATION COPY (simCopy) consults the active
    // SubScript: a planned answer is applied, otherwise the AI's default is
    // taken and the menu is recorded so the search can branch on it.

    private static final boolean SUBCHOICE_ON =
            !"false".equals(System.getProperty("cardguru.subchoice_search", "true"));
    private static final int SUB_ALTS = Integer.getInteger("cardguru.subchoice_alts", 2);
    private static final int SUB_DEPTH = Integer.getInteger("cardguru.subchoice_depth", 2);
    private static final int SUB_MAX_VARIANTS = Integer.getInteger("cardguru.subchoice_max_variants", 3);
    private static final int SUB_EXTRA_ROWS = Integer.getInteger("cardguru.subchoice_extra_rows", 6);

    private SubScript pendingScript = null;
    private int pendingTurn = -1;
    private int scriptHits = 0;
    private int scriptMisses = 0;
    private List<SubMenu> lastRecorded = new ArrayList<>();

    private SubScript activeScript(Game game) {
        SubScript s = SubScript.ACTIVE;
        return (simCopy && s != null && s.boundTo == game && getId().equals(s.playerId)) ? s : null;
    }

    /** Real game: the pending script's answer for this menu, or null. A
     *  mismatch means the line diverged from the simulated one; the rest of
     *  the script is dropped and the pilot is asked as usual. */
    private int scriptSkippedLibrary = 0;

    private SubAnswer takePending(SubMenu m, Game game) {
        if (pendingScript == null || m == null || m.library) {
            return null;
        }
        if (pendingTurn != game.getTurnNum()) {
            pendingScript = null;
            return null;
        }
        SubAnswer a = pendingScript.next(m);
        if (a == null) {
            if (pendingScript.misses > 0) {
                scriptMisses++;
                System.out.println("[CardGuru][subchoice] script miss at: " + m.prompt);
                pendingScript = null;
            }
            return null;
        }
        scriptHits++;
        String note = "search chose '" + a.label + "' for: " + m.prompt;
        System.out.println("[CardGuru][subchoice] " + note);
        GameRecorder rec = CardGuruScenarioRunner.recorder;
        if (rec != null && !game.isSimulation()) {
            rec.event(game, "SCRIPT", note);
        }
        if (pendingScript.cursor >= pendingScript.planned.size()) {
            pendingScript = null;
        }
        return a;
    }

    private String optionKeyOf(UUID id, Game game, Map<String, Integer> seen) {
        String base;
        Player p = game.getPlayer(id);
        if (p != null) {
            base = "player:" + (p.getId().equals(getId()) ? "A" : "B");
        } else {
            Permanent perm = game.getPermanent(id);
            if (perm != null) {
                base = "perm:" + perm.getName() + ":" + (perm.getControllerId().equals(getId()) ? "A" : "B");
            } else {
                MageObject o = game.getObject(id);
                if (o == null) {
                    o = game.getCard(id);
                }
                base = "card:" + (o == null ? String.valueOf(id) : o.getName());
            }
        }
        int n = seen.merge(base, 1, Integer::sum);
        return n == 1 ? base : base + "#" + n;
    }

    private String optionTextOf(UUID id, Game game) {
        Player p = game.getPlayer(id);
        if (p != null) {
            return "player " + (p.getId().equals(getId()) ? "A" : "B");
        }
        Permanent perm = game.getPermanent(id);
        if (perm != null) {
            String t = perm.getName();
            if (perm.isCreature(game)) {
                t += " " + perm.getPower().getValue() + "/" + perm.getToughness().getValue();
            }
            return t + " (" + (perm.getControllerId().equals(getId()) ? "A" : "B") + ")";
        }
        MageObject o = game.getObject(id);
        if (o == null) {
            o = game.getCard(id);
        }
        return o == null ? String.valueOf(id) : o.getName();
    }

    /** A target/card menu, or null when there is nothing to decide. */
    private SubMenu targetMenu(String kind, String prompt, List<UUID> possible,
                               int min, int max, Game game) {
        if (possible.isEmpty() || (possible.size() == 1 && min >= 1)) {
            return null;
        }
        SubMenu m = new SubMenu(kind, prompt, min, max);
        Map<String, Integer> seen = new HashMap<>();
        for (UUID id : possible) {
            m.keys.add(optionKeyOf(id, game, seen));
            m.texts.add(optionTextOf(id, game));
        }
        // A pile from the library (scry, surveil, look at the top N): the
        // copy's cards are a reseated sample, so the answer is searched but
        // never replayed at the real prompt.
        try {
            m.library = game.getState().getZone(possible.get(0)) == Zone.LIBRARY;
        } catch (RuntimeException ignored) {
        }
        return m;
    }

    private static boolean applyTargetAnswer(Target target, List<UUID> possible, SubMenu m,
                                             SubAnswer a, Ability source, Game game) {
        target.clearChosen();
        for (String k : a.keys) {
            int i = m.keys.indexOf(k);
            if (i >= 0 && target.getTargets().size() < m.max) {
                target.addTarget(possible.get(i), source, game);
            }
        }
        return target.getTargets().size() >= m.min;
    }

    private static List<String> keysOfTargets(Target target, List<UUID> possible, SubMenu m) {
        List<String> out = new ArrayList<>();
        for (UUID id : target.getTargets()) {
            int i = possible.indexOf(id);
            if (i >= 0) {
                out.add(m.keys.get(i));
            }
        }
        return out;
    }

    /** Simulation copy: answer a target/card menu from the script or record
     *  the AI's pick. */
    private boolean simTargetHook(SubScript sc, String kind, Target target, List<UUID> possible,
                                  Ability source, Game game, java.util.function.BooleanSupplier ai) {
        SubMenu m = targetMenu(kind, target.getMessage(game), possible,
                target.getMinNumberOfTargets(), target.getMaxNumberOfTargets(), game);
        if (m == null) {
            return ai.getAsBoolean();
        }
        SubAnswer a = sc.next(m);
        if (a != null) {
            if (applyTargetAnswer(target, possible, m, a, source, game)) {
                m.chosen = new ArrayList<>(a.keys);
                sc.record(m);
                return true;
            }
            target.clearChosen();
        }
        boolean r = ai.getAsBoolean();
        m.chosen = keysOfTargets(target, possible, m);
        sc.record(m);
        return r;
    }

    /** Cards of a pile this TargetCard may pick. Target.possibleTargets(…,
     *  cards) filters the ZONE search by the pile, and the zone search never
     *  offers library cards (they are not targetable), so scry / surveil /
     *  "look at the top N" piles came back empty and fell to the AI. Ask the
     *  target directly, card by card, instead. */
    private List<UUID> pilePossible(TargetCard target, Cards cards, Ability source, Game game) {
        List<UUID> out = new ArrayList<>();
        for (Card c : cards.getCards(game)) {
            try {
                if (target.canTarget(getId(), c.getId(), source, cards, game)) {
                    out.add(c.getId());
                }
            } catch (RuntimeException ignored) {
            }
        }
        if (out.isEmpty()) {
            out.addAll(target.possibleTargets(getId(), source, game, cards));
        }
        return out;
    }

    private List<UUID> possibleOf(Target target, Ability source, Game game) {
        return new ArrayList<>(target.possibleTargets(
                target.getAffectedAbilityControllerId(getId()), source, game));
    }

    /** Ask the policy to pick targets. Returns false when there was nothing
     *  to decide or the answer under-filled the minimum — the caller then
     *  delegates to the AI, which completes whatever was already added. */
    private boolean externalChooseTarget(String kind, Outcome outcome,
                                         Target target, Ability source, Game game) {
        List<UUID> possible = possibleOf(target, source, game);
        int min = target.getMinNumberOfTargets();
        int max = target.getMaxNumberOfTargets();
        if (possible.isEmpty() || (possible.size() == 1 && min >= 1)) {
            return false;   // forced or impossible: no real decision
        }
        SubMenu m = targetMenu(kind, target.getMessage(game), possible, min, max, game);
        SubAnswer a = takePending(m, game);
        if (a != null) {
            if (applyTargetAnswer(target, possible, m, a, source, game)) {
                return true;
            }
            target.clearChosen();
        }
        JsonObject req = baseRequest(kind, game);
        req.addProperty("prompt", target.getMessage(game));
        req.addProperty("ability", String.valueOf(source));
        req.addProperty("outcome", String.valueOf(outcome));
        req.addProperty("min", min);
        req.addProperty("max", max);
        JsonArray opts = new JsonArray();
        for (int i = 0; i < possible.size(); i++) {
            opts.add(describeTargetOption(i, possible.get(i), game));
        }
        req.add("options", opts);
        JsonObject resp = ask(req);
        if (resp.has("targets")) {
            for (JsonElement e : arrOr(resp, "targets")) {
                int idx = intOf(e, -1);
                if (idx >= 0 && idx < possible.size()
                        && target.getTargets().size() < max) {
                    target.addTarget(possible.get(idx), source, game);
                }
            }
        }
        if (target.getTargets().size() < min) {
            System.out.println("[CardGuru][subchoice] " + kind
                    + " answer under-filled (" + target.getTargets().size()
                    + "/" + min + "), AI completes");
            return false;
        }
        return true;
    }

    /** Picking cards out of a specific pile (a hand, a graveyard, the top of
     *  the library for scry / surveil / "look at the top N"). */
    private boolean externalChooseCards(String kind, Cards cards, TargetCard target,
                                        Ability source, Game game) {
        List<UUID> possible = pilePossible(target, cards, source, game);
        int min = target.getMinNumberOfTargets();
        int max = target.getMaxNumberOfTargets();
        if (possible.isEmpty() || (possible.size() == 1 && min >= 1)) {
            return false;
        }
        SubMenu m = targetMenu(kind, target.getMessage(game), possible, min, max, game);
        SubAnswer a = takePending(m, game);
        if (a != null) {
            if (applyTargetAnswer(target, possible, m, a, source, game)) {
                return true;
            }
            target.clearChosen();
        }
        JsonObject req = baseRequest(kind, game);
        req.addProperty("prompt", target.getMessage(game));
        req.addProperty("ability", String.valueOf(source));
        req.addProperty("min", min);
        req.addProperty("max", max);
        JsonArray opts = new JsonArray();
        for (int i = 0; i < possible.size(); i++) {
            JsonObject o = new JsonObject();
            o.addProperty("index", i);
            Card c = game.getCard(possible.get(i));
            o.addProperty("text", c == null ? "?" : c.getName());
            if (c != null) {
                o.addProperty("cost", c.getManaCost().getText());
                o.addProperty("types", typeLine(c, game));
            }
            opts.add(o);
        }
        req.add("options", opts);
        JsonObject resp = ask(req);
        if (resp.has("targets")) {
            for (JsonElement e : arrOr(resp, "targets")) {
                int idx = intOf(e, -1);
                if (idx >= 0 && idx < possible.size()
                        && target.getTargets().size() < max) {
                    target.addTarget(possible.get(idx), source, game);
                }
            }
        }
        if (target.getTargets().size() >= min) {
            return true;
        }
        System.out.println("[CardGuru][subchoice] " + kind
                + " (cards) answer under-filled, AI completes");
        return false;
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Target target, Ability source, Game game) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            return simTargetHook(sc, "target", target, possibleOf(target, source, game), source, game,
                    () -> super.chooseTarget(outcome, target, source, game));
        }
        if (externalSubchoices && !searching
                && externalChooseTarget("target", outcome, target, source, game)) {
            return true;
        }
        return super.chooseTarget(outcome, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source,
                          Game game, Map<String, Serializable> options) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            return simTargetHook(sc, "choose", target, possibleOf(target, source, game), source, game,
                    () -> super.choose(outcome, target, source, game, options));
        }
        if (externalSubchoices
                && externalChooseTarget("choose", outcome, target, source, game)) {
            return true;
        }
        return super.choose(outcome, target, source, game, options);
    }

    /** Picking cards out of a specific Cards pile — the overload used when an
     *  effect reaches into a hand or a graveyard rather than the battlefield
     *  (Deep-Cavern Bat picks the exiled card through exactly this). */
    @Override
    public boolean choose(Outcome outcome, Cards cards, TargetCard target,
                          Ability source, Game game) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            return simTargetHook(sc, "choose", target, pilePossible(target, cards, source, game),
                    source, game, () -> super.choose(outcome, cards, target, source, game));
        }
        if (externalSubchoices && !searching
                && externalChooseCards("choose", cards, target, source, game)) {
            return true;
        }
        return super.choose(outcome, cards, target, source, game);
    }

    /** The overload PlayerImpl.scry / surveil / lookAtTopCards use. It was
     *  never hooked, so scry decisions were the built-in AI's in the real
     *  game and the pilot never saw them. */
    @Override
    public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target,
                                Ability source, Game game) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            return simTargetHook(sc, "choose", target, pilePossible(target, cards, source, game),
                    source, game, () -> super.chooseTarget(outcome, cards, target, source, game));
        }
        if (externalSubchoices && !searching
                && externalChooseCards("choose", cards, target, source, game)) {
            return true;
        }
        return super.chooseTarget(outcome, cards, target, source, game);
    }

    /** Scry and surveil re-implemented on this player. TestPlayer delegates
     *  them to its inner ComputerPlayer, whose PlayerImpl.scry then asks
     *  ITSELF for the card pick, so neither the pilot (real game) nor the
     *  script hooks (copies) ever saw a scry. Same engine steps as
     *  PlayerImpl.scry / doSurveil, but the pick goes through our
     *  chooseTarget(cards) hook. */
    @Override
    public boolean scry(int value, Ability source, Game game) {
        GameEvent event = new GameEvent(GameEvent.EventType.SCRY, getId(), source, getId(), value, true);
        if (game.replaceEvent(event)) {
            return false;
        }
        game.informPlayers(getLogName() + " scries " + event.getAmount()
                + CardUtil.getSourceLogName(game, source));
        Cards cards = new CardsImpl();
        cards.addAllCards(getLibrary().getTopCards(game, event.getAmount()));
        if (!cards.isEmpty()) {
            TargetCard target = new TargetCard(0, cards.size(), Zone.LIBRARY,
                    new FilterCard("card" + (cards.size() == 1 ? "" : "s")
                            + " to PUT on the BOTTOM of your library (Scry)"));
            chooseTarget(Outcome.Benefit, cards, target, source, game);
            putCardsOnBottomOfLibrary(new CardsImpl(target.getTargets()), game, source, true);
            if (!target.getTargets().isEmpty()) {
                game.fireEvent(GameEvent.getEvent(GameEvent.EventType.SCRY_TO_BOTTOM, getId(),
                        source, getId(), target.getTargets().size()));
            }
            cards.removeIf(target.getTargets()::contains);
            putCardsOnTopOfLibrary(cards, game, source, true);
        }
        game.fireEvent(new GameEvent(GameEvent.EventType.SCRIED, getId(), source, getId(),
                event.getAmount(), true));
        return true;
    }

    @Override
    public Player.SurveilResult doSurveil(int value, Ability source, Game game) {
        GameEvent event = new GameEvent(GameEvent.EventType.SURVEIL, getId(), source, getId(), value, true);
        if (game.replaceEvent(event) || event.getAmount() < 1) {
            return Player.SurveilResult.noSurveil();
        }
        game.informPlayers(getLogName() + " surveils " + event.getAmount()
                + CardUtil.getSourceLogName(game, source));
        Cards cards = new CardsImpl();
        cards.addAllCards(getLibrary().getTopCards(game, event.getAmount()));
        int totalCount = cards.size();
        if (!cards.isEmpty()) {
            TargetCard target = new TargetCard(0, cards.size(), Zone.LIBRARY,
                    new FilterCard("card" + (cards.size() == 1 ? "" : "s")
                            + " to PUT into your GRAVEYARD (Surveil)"));
            chooseTarget(Outcome.Benefit, cards, target, source, game);
            moveCards(new CardsImpl(target.getTargets()), Zone.GRAVEYARD, source, game);
            cards.removeIf(target.getTargets()::contains);
            putCardsOnTopOfLibrary(cards, game, source, true);
        }
        game.fireEvent(new GameEvent(GameEvent.EventType.SURVEILED, getId(), source, getId(),
                event.getAmount(), true));
        return Player.SurveilResult.surveil(totalCount - cards.size(), cards.size());
    }

    @Override
    public int announceX(int min, int max, String message, Game game,
                         Ability source, boolean isManaPay) {
        SubScript sc = activeScript(game);
        if (sc != null && max > min) {
            SubMenu m = SubMenu.x(message, min, max);
            SubAnswer a = sc.next(m);
            int x = a != null ? Math.max(min, Math.min(max, a.x))
                    : super.announceX(min, max, message, game, source, isManaPay);
            m.chosen = Collections.singletonList("x=" + x);
            m.chosenX = x;
            sc.record(m);
            return x;
        }
        if (externalSubchoices && max > min) {
            SubMenu m = SubMenu.x(message, min, max);
            SubAnswer a = takePending(m, game);
            if (a != null) {
                return Math.max(min, Math.min(max, a.x));
            }
            JsonObject req = baseRequest("announce_x", game);
            req.addProperty("prompt", message);
            req.addProperty("ability", String.valueOf(source));
            req.addProperty("min", min);
            req.addProperty("max", max);
            req.addProperty("mana_pay", isManaPay);
            JsonObject resp = ask(req);
            int x = intOr(resp, "x", min);
            return Math.max(min, Math.min(max, x));
        }
        return super.announceX(min, max, message, game, source, isManaPay);
    }

    private List<Mode> availableModes(Modes modes, Ability source, Game game) {
        List<Mode> avail = new ArrayList<>(modes.getAvailableModes(source, game));
        // getAvailableModes only filters already-selected modes when the
        // card limits usage by once, so for multi-mode spells (Three
        // Steps Ahead) a mode we already picked can still be offered —
        // returning it again throws "mode already selected" and kills
        // the game. Drop selected modes unless the card allows repeats.
        if (!modes.isMayChooseSameModeMoreThanOnce()) {
            Set<UUID> already = new HashSet<>(modes.getSelectedModes());
            avail.removeIf(mm -> already.contains(mm.getId()));
        }
        return avail;
    }

    private static SubMenu modeMenu(List<Mode> avail, Ability source) {
        SubMenu m = new SubMenu("mode", String.valueOf(source), 1, 1);
        for (Mode md : avail) {
            String t = md.getEffects().getText(md);
            m.keys.add("mode:" + t);
            m.texts.add(t);
        }
        return m;
    }

    @Override
    public Mode chooseMode(Modes modes, Ability source, Game game) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            List<Mode> avail = availableModes(modes, source, game);
            if (avail.size() > 1) {
                SubMenu m = modeMenu(avail, source);
                SubAnswer a = sc.next(m);
                Mode r = null;
                if (a != null && !a.keys.isEmpty()) {
                    int i = m.keys.indexOf(a.keys.get(0));
                    if (i >= 0) {
                        r = avail.get(i);
                    }
                }
                if (r == null) {
                    r = super.chooseMode(modes, source, game);
                }
                int ri = r == null ? -1 : avail.indexOf(r);
                m.chosen = ri >= 0 ? Collections.singletonList(m.keys.get(ri)) : new ArrayList<>();
                sc.record(m);
                return r;
            }
            return super.chooseMode(modes, source, game);
        }
        if (externalSubchoices && !searching) {
            List<Mode> avail = availableModes(modes, source, game);
            if (avail.isEmpty()) {
                return super.chooseMode(modes, source, game);
            }
            if (avail.size() > 1) {
                SubMenu m = modeMenu(avail, source);
                SubAnswer a = takePending(m, game);
                if (a != null && !a.keys.isEmpty()) {
                    int i = m.keys.indexOf(a.keys.get(0));
                    if (i >= 0) {
                        return avail.get(i);
                    }
                }
                JsonObject req = baseRequest("mode", game);
                req.addProperty("ability", String.valueOf(source));
                JsonArray opts = new JsonArray();
                // A Spree mode's cost is charged ON TOP of the spell's base
                // cost, and the effect text alone does not say so. Mirror
                // game 3 kept picking Three Steps Ahead's +{3} copy mode
                // while holding one land, so every cast unwound; the pilot
                // was never shown that the mode cost anything at all.
                for (int i = 0; i < avail.size(); i++) {
                    JsonObject o = new JsonObject();
                    o.addProperty("index", i);
                    o.addProperty("text", avail.get(i).getEffects().getText(avail.get(i)));
                    Cost mc = avail.get(i).getCost();
                    if (mc != null) {
                        o.addProperty("additional_cost", String.valueOf(mc));
                    }
                    opts.add(o);
                }
                req.add("options", opts);
                JsonObject resp = ask(req);
                int c = intOr(resp, "choice", -1);
                if (c >= 0 && c < avail.size()) {
                    return avail.get(c);
                }
                System.out.println("[CardGuru][subchoice] bad mode answer, AI picks");
            }
        }
        return super.chooseMode(modes, source, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, Ability source, Game game) {
        SubScript sc = activeScript(game);
        if (sc != null) {
            SubMenu m = SubMenu.use(message);
            SubAnswer a = sc.next(m);
            boolean r = a != null ? a.bool : super.chooseUse(outcome, message, source, game);
            m.chosen = Collections.singletonList(r ? "yes" : "no");
            sc.record(m);
            return r;
        }
        if (externalSubchoices && !searching) {
            SubAnswer a = takePending(SubMenu.use(message), game);
            if (a != null) {
                return a.bool;
            }
            return externalChooseUse(outcome, message, null, game, source);
        }
        return super.chooseUse(outcome, message, source, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, String secondMessage,
                             String trueText, String falseText, Ability source, Game game) {
        String prompt = message + (secondMessage != null ? " " + secondMessage : "");
        SubScript sc = activeScript(game);
        if (sc != null) {
            SubMenu m = SubMenu.use(prompt);
            SubAnswer a = sc.next(m);
            boolean r = a != null ? a.bool : super.chooseUse(outcome, message, secondMessage,
                    trueText, falseText, source, game);
            m.chosen = Collections.singletonList(r ? "yes" : "no");
            sc.record(m);
            return r;
        }
        if (externalSubchoices && !searching) {
            SubAnswer a = takePending(SubMenu.use(prompt), game);
            if (a != null) {
                return a.bool;
            }
            return externalChooseUse(outcome, message, secondMessage, game, source);
        }
        return super.chooseUse(outcome, message, secondMessage, trueText, falseText,
                source, game);
    }

    private boolean externalChooseUse(Outcome outcome, String message,
                                      String secondMessage, Game game, Ability source) {
        JsonObject req = baseRequest("use", game);
        req.addProperty("prompt", message
                + (secondMessage != null ? " " + secondMessage : ""));
        req.addProperty("ability", String.valueOf(source));
        // The engine's own hint on whether saying yes helps the chooser —
        // the same signal ComputerPlayer.chooseUse decides by.
        req.addProperty("good_outcome", outcome != null && outcome.isGood());
        JsonObject resp = ask(req);
        return resp.has("use") && resp.get("use").getAsBoolean();
    }

    private static SubMenu choiceMenu(Choice choice, List<String> keys, List<String> texts) {
        SubMenu m = new SubMenu("choice", String.valueOf(choice.getMessage()), 1, 1);
        for (String t : texts) {
            m.keys.add("choice:" + t);
            m.texts.add(t);
        }
        return m;
    }

    @Override
    public boolean choose(Outcome outcome, Choice choice, Game game) {
        if (choice == null) {
            return super.choose(outcome, choice, game);
        }
        List<String> keys = null;
        List<String> texts;
        if (choice.isKeyChoice()) {
            keys = new ArrayList<>(choice.getKeyChoices().keySet());
            texts = new ArrayList<>();
            for (String k : keys) {
                texts.add(choice.getKeyChoices().get(k));
            }
        } else {
            texts = new ArrayList<>(choice.getChoices());
        }
        SubScript sc = activeScript(game);
        if (sc != null) {
            if (texts.size() <= 1) {
                return super.choose(outcome, choice, game);
            }
            SubMenu m = choiceMenu(choice, keys, texts);
            SubAnswer a = sc.next(m);
            int idx = -1;
            if (a != null && !a.keys.isEmpty()) {
                idx = m.keys.indexOf(a.keys.get(0));
            }
            boolean r;
            if (idx >= 0) {
                if (keys != null) {
                    choice.setChoiceByKey(keys.get(idx));
                } else {
                    choice.setChoice(texts.get(idx));
                }
                r = true;
            } else {
                r = super.choose(outcome, choice, game);
                String picked = keys != null ? choice.getChoiceKey() : choice.getChoice();
                idx = keys != null ? keys.indexOf(picked) : texts.indexOf(picked);
            }
            m.chosen = idx >= 0 ? Collections.singletonList(m.keys.get(idx)) : new ArrayList<>();
            sc.record(m);
            return r;
        }
        if (externalSubchoices && texts.size() > 1) {
            SubMenu m = choiceMenu(choice, keys, texts);
            SubAnswer a = takePending(m, game);
            if (a != null && !a.keys.isEmpty()) {
                int idx = m.keys.indexOf(a.keys.get(0));
                if (idx >= 0) {
                    if (keys != null) {
                        choice.setChoiceByKey(keys.get(idx));
                    } else {
                        choice.setChoice(texts.get(idx));
                    }
                    return true;
                }
            }
            JsonObject req = baseRequest("choice", game);
            req.addProperty("prompt", String.valueOf(choice.getMessage()));
            JsonArray opts = new JsonArray();
            for (int i = 0; i < texts.size(); i++) {
                JsonObject o = new JsonObject();
                o.addProperty("index", i);
                o.addProperty("text", texts.get(i));
                opts.add(o);
            }
            req.add("options", opts);
            JsonObject resp = ask(req);
            int c = intOr(resp, "choice", -1);
            if (c >= 0 && c < texts.size()) {
                if (keys != null) {
                    choice.setChoiceByKey(keys.get(c));
                } else {
                    choice.setChoice(texts.get(c));
                }
                return true;
            }
            System.out.println("[CardGuru][subchoice] bad choice answer, AI picks");
        }
        return super.choose(outcome, choice, game);
    }

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        List<Permanent> attackers = getComputerPlayer().getAvailableAttackers(game);
        UUID defenderId = null;
        for (UUID d : game.getCombat().getDefenders()) {
            defenderId = d;
        }
        if (defenderId == null) {
            for (UUID pid : game.getOpponents(this.getId())) {
                defenderId = pid;
            }
        }

        // Simulation-backed minimax over the attack decision (design A in
        // docs/live-minimax.md): the search itself is the agent for attacks, so
        // the external spool policy is NOT consulted here. Every other decision
        // still round-trips to Python.
        if (searching) {
            super.selectAttackers(game, attackingPlayerId);
            return;
        }
        if ("attacks".equals(minimaxMode)) {
            minimaxSelectAttackers(game, defenderId, attackers);
            return;
        }
        if ("llm".equals(minimaxMode) && (!turnPlanMode || planCombatSearch)
                && !attackers.isEmpty()) {
            llmSearchAttackers(game, defenderId, attackers);
            return;
        }

        JsonObject req = baseRequest("attackers", game);
        JsonArray opts = new JsonArray();
        int i = 0;
        for (Permanent p : attackers) {
            JsonObject o = new JsonObject();
            o.addProperty("index", i++);
            o.addProperty("name", p.getName());
            o.addProperty("power", p.getPower().getValue());
            o.addProperty("toughness", p.getToughness().getValue());
            opts.add(o);
        }
        req.add("options", opts);

        JsonObject resp = ask(req);
        if (resp.has("attackers")) {
            for (JsonElement e : arrOr(resp, "attackers")) {
                int idx = intOf(e, -1);
                if (idx >= 0 && idx < attackers.size()) {
                    Permanent atk = attackers.get(idx);
                    if (defenderId != null && atk.canAttack(defenderId, game)) {
                        getComputerPlayer().declareAttacker(atk.getId(), defenderId, game, false);
                    }
                }
            }
        }
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        List<Permanent> blockers = getComputerPlayer().getAvailableBlockers(game);
        List<Permanent> attackers = new ArrayList<>();
        for (CombatGroup grp : game.getCombat().getGroups()) {
            for (UUID aid : grp.getAttackers()) {
                Permanent a = game.getPermanent(aid);
                if (a != null) {
                    attackers.add(a);
                }
            }
        }

        if (searching) {
            super.selectBlockers(source, game, defendingPlayerId);
            return;
        }
        if ("llm".equals(minimaxMode) && (!turnPlanMode || planCombatSearch)
                && !blockers.isEmpty() && !attackers.isEmpty()) {
            llmSearchBlockers(game, defendingPlayerId, blockers, attackers);
            return;
        }

        JsonObject req = baseRequest("blockers", game);
        JsonArray blockerOpts = new JsonArray();
        int bi = 0;
        for (Permanent p : blockers) {
            JsonObject o = new JsonObject();
            o.addProperty("index", bi++);
            o.addProperty("name", p.getName());
            o.addProperty("power", p.getPower().getValue());
            o.addProperty("toughness", p.getToughness().getValue());
            blockerOpts.add(o);
        }
        req.add("blockers", blockerOpts);
        JsonArray attackerOpts = new JsonArray();
        int ai = 0;
        for (Permanent p : attackers) {
            JsonObject o = new JsonObject();
            o.addProperty("index", ai++);
            o.addProperty("name", p.getName());
            o.addProperty("power", p.getPower().getValue());
            o.addProperty("toughness", p.getToughness().getValue());
            attackerOpts.add(o);
        }
        req.add("attackers", attackerOpts);

        JsonObject resp = ask(req);
        if (resp.has("blocks")) {
            for (JsonElement e : arrOr(resp, "blocks")) {
                if (!e.isJsonArray() || e.getAsJsonArray().size() < 2) {
                    continue;
                }
                JsonArray pair = e.getAsJsonArray();
                int b = intOf(pair.get(0), -1);
                int a = intOf(pair.get(1), -1);
                if (b >= 0 && b < blockers.size() && a >= 0 && a < attackers.size()) {
                    getComputerPlayer().declareBlocker(defendingPlayerId,
                            blockers.get(b).getId(), attackers.get(a).getId(), game);
                }
            }
        }
    }

    // ==================================================================
    // Simulation-backed minimax over the declare-attackers decision.
    //
    // A real depth-~1.5 game tree, all rooted on the engine's own rollout
    // primitive Game.createSimulationForAI() (a full deep game copy flagged
    // simulation=true; see GameImpl.createSimulationForAI and
    // docs/live-minimax.md):
    //
    //   MAX layer  : our candidate attack sets (all-attack, hold-one-back for
    //                each creature, attack-none -- a handful, not 2^n).
    //   engine     : declare that exact set on a COPY and resolve combat there.
    //   MIN layer  : the opponent's block response, enumerated on the copy and
    //                chosen to MINIMISE our leaf value (which is exactly what
    //                the built-in AI's block heuristic optimises -- the MAD
    //                block chooser maximises GameStateEvaluator2 for the
    //                blocker, i.e. minimises it for us). See the deviation note
    //                in docs/live-minimax.md.
    //   LEAF       : GameStateEvaluator2.evaluate(us, copy) on the resolved
    //                copy, plus our own life/board terms for the JSON trace.
    //
    // We back up max-over-min and apply the argmax set to the REAL game with
    // the same declareAttacker primitive the harness uses everywhere else.
    // ==================================================================

    /** Cap on enumerated opponent block responses per attack set (keeps the
     *  min-layer a real-but-bounded search, matching the max-layer's handful). */
    private static final int MAX_BLOCK_RESPONSES = 16;

    private void minimaxSelectAttackers(Game game, UUID defenderId,
                                        List<Permanent> attackers) {
        UUID myId = this.getId();
        List<List<Integer>> candidates = candidateAttackSets(attackers.size());

        JsonArray candLog = new JsonArray();
        List<Integer> best = candidates.isEmpty() ? new ArrayList<>() : candidates.get(0);
        double bestValue = Double.NEGATIVE_INFINITY;
        JsonObject bestLeaf = null;
        int bestResponses = 0;

        for (List<Integer> set : candidates) {
            AttackEval ev = evaluateAttackSet(game, myId, defenderId, attackers, set);
            JsonObject c = new JsonObject();
            c.addProperty("label", labelFor(set, attackers));
            c.addProperty("attacker_count", set.size());
            c.addProperty("value", ev.value);           // max-over-min backed-up value
            c.addProperty("block_responses", ev.numResponses);
            c.add("leaf", ev.leaf);                      // our own life/board terms
            candLog.add(c);
            if (ev.value > bestValue) {
                bestValue = ev.value;
                best = set;
                bestLeaf = ev.leaf;
                bestResponses = ev.numResponses;
            }
        }

        // Apply the argmax attack set to the REAL game.
        for (int idx : best) {
            Permanent atk = attackers.get(idx);
            if (defenderId != null && atk.canAttack(defenderId, game)) {
                getComputerPlayer().declareAttacker(atk.getId(), defenderId, game, false);
            }
        }

        // Record the decision: how many candidates were simulated and which was
        // chosen (the search's proof-of-work). One JSON object per line in
        // spool/minimax.jsonl for the Python side to read after the game.
        JsonObject decision = new JsonObject();
        decision.addProperty("turn", game.getTurnNum());
        decision.addProperty("available_attackers", attackers.size());
        decision.addProperty("candidate_sets", candidates.size());
        decision.addProperty("chosen", labelFor(best, attackers));
        decision.addProperty("chosen_value", bestValue);
        decision.addProperty("chosen_block_responses", bestResponses);
        if (bestLeaf != null) {
            decision.add("chosen_leaf", bestLeaf);
        }
        decision.add("candidates", candLog);
        appendTrace(decision);
        System.out.println("[CardGuru][minimax] turn " + game.getTurnNum()
                + ": simulated " + candidates.size() + " attack set(s), chose '"
                + labelFor(best, attackers) + "' (value=" + bestValue + ")");
    }

    /** The handful of attack sets we search: attack-none, all-attack, and
     *  hold-one-creature-back for each creature. Deduplicated (with 0 or 1
     *  creatures several of these coincide). Indices are into the attacker list. */
    private List<List<Integer>> candidateAttackSets(int n) {
        List<List<Integer>> sets = new ArrayList<>();
        Set<String> seen = new HashSet<>();

        List<Integer> none = new ArrayList<>();
        addUnique(sets, seen, none);

        List<Integer> all = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            all.add(i);
        }
        addUnique(sets, seen, all);

        for (int hold = 0; hold < n; hold++) {
            List<Integer> s = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                if (i != hold) {
                    s.add(i);
                }
            }
            addUnique(sets, seen, s);
        }
        return sets;
    }

    private static void addUnique(List<List<Integer>> sets, Set<String> seen,
                                  List<Integer> set) {
        String key = set.toString();
        if (seen.add(key)) {
            sets.add(set);
        }
    }

    private String labelFor(List<Integer> set, List<Permanent> attackers) {
        if (set.isEmpty()) {
            return "attack-none";
        }
        if (set.size() == attackers.size()) {
            return "attack-all";
        }
        List<String> names = new ArrayList<>();
        for (int i = 0; i < attackers.size(); i++) {
            if (!set.contains(i)) {
                names.add(attackers.get(i).getName());
            }
        }
        return "hold[" + String.join(",", names) + "]";
    }

    /** Backed-up value of one attack set, and the leaf terms of the opponent's
     *  best (min) response, for the trace. */
    private static final class AttackEval {
        final double value;
        final int numResponses;
        final JsonObject leaf;
        AttackEval(double value, int numResponses, JsonObject leaf) {
            this.value = value;
            this.numResponses = numResponses;
            this.leaf = leaf;
        }
    }

    /**
     * MAX-node child: declare `set` on a fresh copy, enumerate the opponent's
     * block responses, resolve each on its own copy, and return the MIN over
     * responses of our leaf value (the opponent picking its best block).
     */
    private AttackEval evaluateAttackSet(Game game, UUID myId, UUID defenderId,
                                         List<Permanent> attackers, List<Integer> set) {
        Game afterAttack = simCopy(game);
        for (int idx : set) {
            Permanent atk = attackers.get(idx);
            Permanent simAtk = afterAttack.getPermanent(atk.getId());
            if (simAtk != null && defenderId != null
                    && simAtk.canAttack(defenderId, afterAttack)) {
                afterAttack.getPlayer(myId)
                        .declareAttacker(atk.getId(), defenderId, afterAttack, false);
            }
        }
        fireAttackDeclared(afterAttack);

        List<List<UUID[]>> responses = enumerateBlockResponses(afterAttack, defenderId);

        double worstForUs = Double.POSITIVE_INFINITY;
        JsonObject worstLeaf = null;
        for (List<UUID[]> resp : responses) {
            Game leaf = afterAttack.copy();
            applyBlocksAndResolveCombat(leaf, defenderId, resp);
            double v = GameStateEvaluator2.evaluate(myId, leaf).getTotalScore();
            if (v < worstForUs) {
                worstForUs = v;
                worstLeaf = leafTerms(leaf, myId, defenderId, v);
            }
        }
        return new AttackEval(worstForUs, responses.size(), worstLeaf);
    }

    /**
     * The opponent's candidate block responses, as lists of {blockerId,
     * attackerId} pairs on the post-attack copy: no-block, each legal single
     * 1-1 block, and a greedy "block the biggest threat with every blocker"
     * full assignment. A handful, bounded by MAX_BLOCK_RESPONSES -- a real
     * min-layer, not the full block lattice (documented scope).
     */
    private List<List<UUID[]>> enumerateBlockResponses(Game afterAttack, UUID defenderId) {
        List<List<UUID[]>> responses = new ArrayList<>();
        responses.add(new ArrayList<>());   // no block is always an option

        List<Permanent> declared = new ArrayList<>();
        for (CombatGroup grp : afterAttack.getCombat().getGroups()) {
            for (UUID aid : grp.getAttackers()) {
                Permanent a = afterAttack.getPermanent(aid);
                if (a != null) {
                    declared.add(a);
                }
            }
        }
        Player defender = afterAttack.getPlayer(defenderId);
        if (defender == null || declared.isEmpty()) {
            return responses;
        }
        List<Permanent> blockers = defender.getAvailableBlockers(afterAttack);

        // single 1-1 blocks
        for (Permanent b : blockers) {
            for (Permanent a : declared) {
                if (b.canBlock(a.getId(), afterAttack)) {
                    List<UUID[]> r = new ArrayList<>();
                    r.add(new UUID[]{b.getId(), a.getId()});
                    responses.add(r);
                    if (responses.size() >= MAX_BLOCK_RESPONSES) {
                        return responses;
                    }
                }
            }
        }

        // greedy full block: each blocker onto the highest-power attacker it can
        // still block, one blocker per attacker (a coherent "block to stabilise"
        // response rather than a scatter of singletons)
        List<Permanent> byPower = new ArrayList<>(declared);
        byPower.sort((x, y) -> y.getPower().getValue() - x.getPower().getValue());
        List<UUID[]> greedy = new ArrayList<>();
        Set<UUID> takenAttackers = new HashSet<>();
        for (Permanent b : blockers) {
            for (Permanent a : byPower) {
                if (!takenAttackers.contains(a.getId())
                        && b.canBlock(a.getId(), afterAttack)) {
                    greedy.add(new UUID[]{b.getId(), a.getId()});
                    takenAttackers.add(a.getId());
                    break;
                }
            }
        }
        if (greedy.size() > 1) {
            responses.add(greedy);
        }
        return responses;
    }

    /** Apply one block response on a leaf copy and run combat to end-of-combat,
     *  mirroring CombatUtil.willItSurviveSimulation's proven resolution recipe. */
    /** Returns the opponent's post-block response (arm (f)), or null. */
    private String applyBlocksAndResolveCombat(Game leaf, UUID defenderId,
                                               List<UUID[]> resp) {
        Player defender = leaf.getPlayer(defenderId);
        for (UUID[] pair : resp) {
            Permanent b = leaf.getPermanent(pair[0]);
            Permanent a = leaf.getPermanent(pair[1]);
            if (defender != null && b != null && a != null
                    && b.canBlock(a.getId(), leaf)) {
                defender.declareBlocker(defenderId, pair[0], pair[1], leaf);
            }
        }
        leaf.fireEvent(GameEvent.getEvent(GameEvent.EventType.DECLARED_BLOCKERS,
                defenderId, defenderId));
        leaf.checkStateAndTriggered();
        resolveStack(leaf);
        // Arm (f): blockers are declared and damage has not happened. This
        // is the window where an unblocked attacker becomes Kaito by
        // ninjutsu, or a pump/removal lands on a blocker. Across g5-g8
        // neither the pilot nor this search ever considered it — the
        // opponent had no window here at all. Their single best play from
        // the seated hand; the leaf then shows what the block really cost.
        String reply = null;
        UUID attackerId = null;
        for (UUID pid : leaf.getOpponents(defenderId)) {
            attackerId = pid;
        }
        if (attackerId != null) {
            reply = opponentRespond(leaf, attackerId);
            if (reply != null) {
                leaf.checkStateAndTriggered();
                resolveStack(leaf);
            }
        }
        simulateStep(leaf, new CombatDamageStep(true));
        simulateStep(leaf, new CombatDamageStep(false));
        simulateStep(leaf, new EndOfCombatStep());
        leaf.checkStateAndTriggered();
        resolveStack(leaf);
        return reply;
    }

    /** After declaring attackers on a copy by hand, fire what the real
     *  DeclareAttackersStep fires — an AttackerDeclaredEvent per attacker and
     *  DECLARED_ATTACKERS — so "whenever this attacks" triggers resolve on
     *  the copy. Without it every attack rollout in every arm skipped
     *  Preacher's draw-and-lose-1 and Sheoldred's lose-2-per-draw, and the
     *  plan-search game's turn 19 attack was scored "us 10 vs 1-4" for a
     *  swing that took the pilot from 9 to 0. */
    private static void fireAttackDeclared(Game sim) {
        try {
            sim.getCombat().resumeSelectAttackers(sim);
        } catch (RuntimeException ignored) {
            // no attackers declared, or combat not initialised on this copy
        }
        sim.checkStateAndTriggered();
        resolveStack(sim);
    }

    /** Resolve the whole stack, applying effects between resolves. */
    private static void resolveStack(Game g) {
        int guard = 0;
        while (!g.getStack().isEmpty() && guard++ < 100) {
            g.getStack().resolve(g);
            g.applyEffects();
        }
    }

    /** Advance one turn Step on a simulation copy (private in CombatUtil, so
     *  replicated here verbatim): set the step, begin it, drain the stack, end
     *  it. */
    private static void simulateStep(Game sim, Step step) {
        sim.getPhase().setStep(step);
        if (!step.skipStep(sim, sim.getActivePlayerId())) {
            step.beginStep(sim, sim.getActivePlayerId());
            resolveStack(sim);
            step.endStep(sim, sim.getActivePlayerId());
        }
    }

    /** Our own life/board leaf terms (the value.py SPIRIT: score from A's seat
     *  off public outcome state) alongside the engine's own scalar score. */
    private JsonObject leafTerms(Game leaf, UUID myId, UUID defenderId, double engineScore) {
        JsonObject o = new JsonObject();
        Player me = leaf.getPlayer(myId);
        Player opp = leaf.getPlayer(defenderId);
        o.addProperty("engine_score", engineScore);
        if (me != null) {
            o.addProperty("a_life", me.getLife());
            o.addProperty("a_board",
                    leaf.getBattlefield().getAllActivePermanents(myId).size());
        }
        if (opp != null) {
            o.addProperty("b_life", opp.getLife());
            o.addProperty("b_board",
                    leaf.getBattlefield().getAllActivePermanents(defenderId).size());
        }
        return o;
    }

    // ==================================================================
    // PokeChamp arm (d): the same simulation rollouts as the minimax search,
    // but the LEAF VALUE FUNCTION is the LLM. All leaves of one decision go
    // out as a single "leaf_eval" spool request (compact one-line board
    // summaries); the response is a flat 0-100 score per leaf in listed
    // order. Candidate value = MIN over its leaves (the opponent picks the
    // reply worst for us); we apply the argmax candidate. Any missing or
    // malformed response falls back to the GameStateEvaluator2 values that
    // were computed alongside — the game never wedges on the evaluator.
    // ==================================================================

    /** Worst (by heuristic) block-response leaves shown to the LLM per attack
     *  candidate: the LLM re-scores the heuristic's top threats rather than
     *  the full response lattice, keeping one request per combat. */
    private static final int LLM_LEAVES_PER_CANDIDATE = 3;

    private static final class ScoredLeaf {
        final JsonObject summary;
        final double heuristic;
        ScoredLeaf(JsonObject summary, double heuristic) {
            this.summary = summary;
            this.heuristic = heuristic;
        }
    }

    // ---- determinization ----------------------------------------------
    //
    // Game.createSimulationForAI() is a full deep copy: it carries the
    // opponent's REAL hand and library order. Any rollout in which the
    // opponent acts on that copy — or in which one of OUR effects looks at
    // it (Deep-Cavern Bat's ETB reads their hand and the built-in AI picks
    // the exile from cards it should not know) — is using hidden
    // information, and a search that peeks produces numbers that will not
    // generalise. So every copy the search makes goes through simCopy(),
    // which reseats the opponent's hidden zones with a fair sample.
    //
    // The sample needs no belief model of its own: on the copy, their
    // library and hand together are exactly the cards we have not watched
    // leave their library, i.e. believed_remaining. Shuffling the hand back
    // in and redrawing the same count is a draw from that set. (It forgets
    // cards we have actually seen in their hand — a Bat peek — which is a
    // refinement for later, not a leak.)
    //
    // Redraw goes through moveToZone, never drawCards, so no draw trigger
    // fires on the copy: Sheoldred must not drain them for a shuffle.
    private int detRollouts = 0;
    private int detSeatedEqualsReal = 0;

    /** A simulation copy whose opponent hidden zones have been reseated. */
    /** Reseat our own library on copies too. Without this every rollout
     *  drew, scried and looked at the REAL top cards, the leaf summaries
     *  listed them, and the pilot planned around cards it had not drawn
     *  ("nets +2 cards including Stock Up and Glacial Dragonhunt"). */
    private static final boolean RESEAT_SELF =
            !"false".equals(System.getProperty("cardguru.reseat_self", "true"));
    private int selfReseated = 0;
    /** Ids of the cards in our real hand when the current search started;
     *  a leaf's hand card outside this set was drawn inside the rollout. */
    private Set<UUID> searchHandIds = null;

    private Game simCopy(Game game) {
        Player real = game.getPlayer(getId());
        if (real != null) {
            searchHandIds = new HashSet<>(real.getHand());
        }
        Game sim = game.createSimulationForAI();
        UUID oppId = null;
        for (UUID pid : game.getOpponents(getId())) {
            oppId = pid;
        }
        if (oppId != null) {
            detRollouts++;
            if (!determinizeOpponent(sim, oppId)) {
                detSeatedEqualsReal++;
            }
        }
        if (RESEAT_SELF) {
            Player me = sim.getPlayer(getId());
            if (me != null) {
                me.getLibrary().shuffle();
                selfReseated++;
            }
        }
        return sim;
    }

    /** Reseat one player's hand from their own library on a copy. Returns
     *  true iff the seated hand differs from the real one — equality is
     *  possible by chance (small hand, small library) but should be rare,
     *  and its rate is logged per decision as the leak check. */
    private static boolean determinizeOpponent(Game sim, UUID oppId) {
        Player opp = sim.getPlayer(oppId);
        if (opp == null) {
            return true;
        }
        List<String> real = handNames(opp, sim);
        int h = opp.getHand().size();
        if (h > 0) {
            opp.putCardsOnBottomOfLibrary(
                    new CardsImpl(opp.getHand().getCards(sim)), sim, null, false);
        }
        opp.getLibrary().shuffle();
        for (int i = 0; i < h; i++) {
            Card top = opp.getLibrary().getFromTop(sim);
            if (top == null) {
                break;
            }
            top.moveToZone(Zone.HAND, null, sim, false);
        }
        return !handNames(opp, sim).equals(real);
    }

    private static List<String> handNames(Player p, Game g) {
        List<String> names = new ArrayList<>();
        for (Card c : p.getHand().getCards(g)) {
            names.add(c.getName());
        }
        Collections.sort(names);
        return names;
    }

    // ---- arm (e): project the opponent's turn ----------------------------
    //
    // The priority search used to roll out my action, pop the stack, and
    // score. The opponent never acted, so holding mana never produced a
    // different leaf from tapping out, and the search was structurally
    // biased toward tapping out (docs/stack-search-plan.md §1-2).
    //
    // With cardguru.project_turn=K, each priority candidate is instead
    // played out K times, each on a freshly reseated copy (a different
    // sampled opponent hand + draw, so the K copies ARE the chance layer),
    // through the start of their turn and their main-phase play, with an
    // interaction window for me on their turn:
    //
    //   MAX0   my action (pass | cast X)
    //   CHANCE their reseated hand and draw            (one per copy)
    //   MIN    their land drop + most expensive castable spell
    //   MAX1   my response: while their spell is on the stack (counters),
    //          and again after it resolves (instant removal) — each a branch
    //   LEAF   the pilot scores the board
    //
    // MAX1 is the node that gives holding mana a value. With nothing to
    // respond with it has one option and the tree collapses to "cast".
    //
    // Their play is a cheap deterministic heuristic, not MAD's own search:
    // ComputerPlayer7.priority() runs calculateActions() on every main
    // phase, and nesting that inside every leaf would be prohibitive.
    // Targets for their spell go to their own chooser under `searching`,
    // which is adversarial and does not search.
    //
    // Backup is mean over samples of max over my responses, replacing
    // worst-leaf for projected candidates: minimax over a sampled opponent
    // hand would assume they always drew the counter and push the pilot
    // passive — the opposite failure.
    private final int projectTurnK = Integer.getInteger("cardguru.project_turn", 0);
    private static final int MAX_RESPONSES_PER_WINDOW = 2;
    private int projSamplesFailed = 0;
    private String projLastFailure = "";

    /** One row of the priority search: an ability (null = pass) with a
     *  planned sub-choice script (empty = the AI's defaults), the variant's
     *  post-resolution heuristic, and the sample-0 copy the ability's rows
     *  branch from (so variants are compared on the same seated hand). */
    private static final class Row {
        final String label;
        final ActivatedAbility ability;
        final List<SubAnswer> planned;
        final double h;
        final Game base0;

        Row(String label, ActivatedAbility ability, List<SubAnswer> planned, double h, Game base0) {
            this.label = label;
            this.ability = ability;
            this.planned = planned;
            this.h = h;
            this.base0 = base0;
        }
    }

    private int variantsDiscoveredLast = 0;
    private int variantRowsLast = 0;
    private String chosenScriptLast = "";

    /** Activate the ability on the copy under a sub-choice script and let it
     *  resolve; with respond=true the two arm (f) opponent windows fire.
     *  Returns the response tag for the leaf line; the menus met are left in
     *  lastRecorded and the script misses in missOut[0]. */
    private String castSegment(Game sim, UUID myId, UUID oppId, ActivatedAbility ability,
                               List<SubAnswer> planned, boolean respond, int[] missOut) {
        SubScript sc = new SubScript(sim, myId, planned);
        SubScript.ACTIVE = sc;
        try {
            if (ability != null) {
                Player me = sim.getPlayer(myId);
                if (me != null) {
                    me.activateAbility(ability.copy(), sim);
                }
            }
            // Arm (f), window 1: my spell is on the stack. Only a counter or
            // a flash play can meet it here. Window 2: it has resolved and
            // its ETB has fired; now removal has a target.
            String r1 = (respond && ability != null) ? opponentRespond(sim, oppId) : null;
            sim.checkStateAndTriggered();
            resolveStack(sim);
            String r2 = (respond && ability != null) ? opponentRespond(sim, oppId) : null;
            sim.checkStateAndTriggered();
            resolveStack(sim);
            return (r1 != null ? " | they respond on the stack: " + r1 : "")
                    + (r2 != null ? " | after it resolves they cast: " + r2 : "");
        } finally {
            SubScript.ACTIVE = null;
            lastRecorded = sc.recorded;
            if (missOut != null) {
                missOut[0] = sc.misses;
            }
        }
    }

    /** The rows for one candidate: its AI-default line plus up to
     *  SUB_MAX_VARIANTS-1 sub-choice variants. A recording run finds the
     *  menus the cast hits (targets, kicker, scry, card picks); each
     *  alternative answer at the first SUB_DEPTH menus is re-run on the same
     *  sample-0 copy, scored by the engine evaluator, and the best kept. */
    private List<Row> discoverRows(Game game, UUID myId, UUID oppId,
                                   ActivatedAbility ability, String label) {
        List<Row> rows = new ArrayList<>();
        if (ability == null || !SUBCHOICE_ON) {
            rows.add(new Row(label, ability, new ArrayList<SubAnswer>(), Double.NaN, null));
            return rows;
        }
        Game base0;
        try {
            base0 = simCopy(game);
        } catch (Exception e) {
            rows.add(new Row(label, ability, new ArrayList<SubAnswer>(), Double.NaN, null));
            return rows;
        }
        rows.add(new Row(label, ability, new ArrayList<SubAnswer>(), Double.NaN, base0));
        boolean prev = searching;
        searching = true;
        try {
            boolean respond = projectTurnK > 0 && myId.equals(game.getActivePlayerId());
            int[] miss = new int[1];
            castSegment(branch(base0), myId, oppId, ability, new ArrayList<SubAnswer>(), respond, miss);
            List<SubMenu> menus = new ArrayList<>(lastRecorded);
            List<SubAnswer> defaults = new ArrayList<>();
            for (SubMenu m : menus) {
                defaults.add(m.asAnswer());
            }
            // The default row says what the engine answered, so "Cast Burst
            // Lightning \u2192 Pay Kicker: yes" and its "\u2192 Pay Kicker: no" variant
            // read as the two lines they are.
            if (!menus.isEmpty()) {
                int shown = Math.min(menus.size(), SUB_DEPTH);
                rows.set(0, new Row(label + " \u2192 " + SubScript.describe(defaults.subList(0, shown)),
                        ability, new ArrayList<SubAnswer>(), Double.NaN, base0));
            }
            List<Row> alts = new ArrayList<>();
            Set<String> seenLabels = new HashSet<>();
            seenLabels.add(rows.get(0).label);
            for (int d = 0; d < Math.min(menus.size(), SUB_DEPTH); d++) {
                for (SubAnswer alt : menus.get(d).alternatives(SUB_ALTS)) {
                    List<SubAnswer> planned = new ArrayList<>(defaults.subList(0, d));
                    planned.add(alt);
                    String vl = label + " \u2192 " + SubScript.describe(planned);
                    if (!seenLabels.add(vl)) {
                        continue;
                    }
                    Game sv = branch(base0);
                    int[] m2 = new int[1];
                    try {
                        castSegment(sv, myId, oppId, ability, planned, respond, m2);
                    } catch (Exception e) {
                        continue;
                    }
                    if (m2[0] > 0) {
                        continue;
                    }
                    double h = GameStateEvaluator2.evaluate(myId, sv).getTotalScore();
                    alts.add(new Row(vl, ability, planned, h, base0));
                }
            }
            variantsDiscoveredLast += alts.size();
            alts.sort((a, b) -> Double.compare(b.h, a.h));
            for (int i = 0; i < alts.size() && i < SUB_MAX_VARIANTS - 1; i++) {
                rows.add(alts.get(i));
            }
        } catch (Exception e) {
            projSamplesFailed++;
            projLastFailure = String.valueOf(e);
        } finally {
            searching = prev;
        }
        return rows;
    }

    /** Keep at most `cap` variant rows per search (best heuristic first). */
    private static void pruneExtraRows(List<Row> rows, int cap) {
        List<Row> extras = new ArrayList<>();
        for (Row r : rows) {
            if (!r.planned.isEmpty()) {
                extras.add(r);
            }
        }
        if (extras.size() <= cap) {
            return;
        }
        extras.sort((a, b) -> Double.compare(b.h, a.h));
        Set<Row> keep = new HashSet<>(extras.subList(0, cap));
        rows.removeIf(r -> !r.planned.isEmpty() && !keep.contains(r));
    }

    /** Leaves for one row: projected (arm (e), K reseated samples, their
     *  next turn, my responses) on my turn, a single resolved leaf otherwise.
     *  The projection answers "if I act now, what happens on THEIR turn";
     *  run on a window during their own turn it would skip the rest of that
     *  turn, so there the old single rollout is at least not the wrong turn. */
    private List<ScoredLeaf> rolloutRow(Game game, UUID myId, UUID oppId, Row row) {
        List<ScoredLeaf> out = new ArrayList<>();
        boolean projected = projectTurnK > 0 && myId.equals(game.getActivePlayerId());
        int samples = projected ? projectTurnK : 1;
        for (int k = 0; k < samples; k++) {
            Game sim;
            try {
                sim = (k == 0 && row.base0 != null) ? branch(row.base0) : simCopy(game);
            } catch (Exception e) {
                continue;
            }
            boolean prev = searching;
            searching = true;
            try {
                int[] miss = new int[1];
                String respTag = castSegment(sim, myId, oppId, row.ability, row.planned, projected, miss);
                String tag = row.label + respTag + (miss[0] > 0 ? " | script miss" : "");
                if (projected) {
                    projectOpponentTurn(sim, myId, oppId, tag, k, out);
                } else {
                    double h = GameStateEvaluator2.evaluate(myId, sim).getTotalScore();
                    out.add(new ScoredLeaf(compactLeaf(sim, myId, oppId, tag), h));
                }
            } catch (Exception e) {
                // A sample that throws is dropped; the others still count.
                projSamplesFailed++;
                projLastFailure = String.valueOf(e);
            } finally {
                searching = prev;
            }
        }
        return out;
    }

    /** Intra-line branch: a raw copy WITHOUT reseating. The sampled hand
     *  must stay fixed along one line; simCopy would redraw it. */
    private static Game branch(Game sim) {
        return sim.createSimulationForAI();
    }

    /** Hand the copy to the opponent: next turn number, their untap, upkeep
     *  and draw (a real draw, so draw triggers such as Sheoldred's DO fire
     *  here — this is their turn, not a reseat), then their first main
     *  phase with priority. Skips my combat and end step: a known
     *  approximation for a priority-window projection. */
    private static void beginOpponentTurn(Game sim, UUID oppId) {
        sim.getState().setActivePlayerId(oppId);
        sim.getState().setTurnNum(sim.getTurnNum() + 1);
        Player opp = sim.getPlayer(oppId);
        if (opp != null) {
            opp.resetLandsPlayed();
        }
        sim.getTurn().setPhase(new BeginningPhase());
        simulateStep(sim, new UntapStep());
        simulateStep(sim, new UpkeepStep());
        simulateStep(sim, new DrawStep());
        sim.getTurn().setPhase(new PreCombatMainPhase());
        sim.getPhase().setStep(new PreCombatMainStep());
        sim.getState().setPriorityPlayerId(oppId);
    }

    /** Their main phase, cheaply: a land drop if they have one, then their
     *  most expensive castable non-land spell, left ON THE STACK so my
     *  window-1 response can target it. Returns the spell's label, or null
     *  if they cast nothing. */
    /** What the projected opponent did in their main phase. */
    private static final class OppTurn {
        final String spell;      // label of the spell left on the stack, or null
        final boolean land;      // whether a land drop was made
        OppTurn(String spell, boolean land) {
            this.spell = spell;
            this.land = land;
        }
    }

    private static String stripCast(String s) {
        return s != null && s.startsWith("Cast ") ? s.substring(5) : s;
    }

    /** Leaf line fragment for the projected opponent turn: which turn it
     *  is (theirs, next), whether they made a land drop, what they cast.
     *  The replay showed "s0: they cast Stock Up" under a 2-land board and
     *  it read as illegal; it was their next turn with a third land. */
    private static String theirTurnLabel(Game sim, int k, OppTurn t) {
        return "s" + k + ": their T" + sim.getTurnNum() + " \u2014 "
                + (t.land ? "land drop, " : "no land, ")
                + (t.spell == null ? "nothing" : "cast " + stripCast(t.spell));
    }

    private static OppTurn opponentMainPhase(Game sim, UUID oppId) {
        Player opp = sim.getPlayer(oppId);
        if (opp == null) {
            return new OppTurn(null, false);
        }
        boolean land = false;
        for (ActivatedAbility a : opp.getPlayable(sim, true)) {
            if (a instanceof PlayLandAbility) {
                land = opp.activateAbility(a.copy(), sim);
                sim.checkStateAndTriggered();
                resolveStack(sim);
                break;
            }
        }
        ActivatedAbility best = null;
        int bestMv = -1;
        for (ActivatedAbility a : opp.getPlayable(sim, true)) {
            if (a instanceof mage.abilities.mana.ManaAbility
                    || a instanceof PlayLandAbility) {
                continue;
            }
            int mv = a.getManaCosts() == null ? 0 : a.getManaCosts().manaValue();
            if (mv > bestMv) {
                bestMv = mv;
                best = a;
            }
        }
        if (best == null) {
            return new OppTurn(null, land);
        }
        return new OppTurn(opp.activateAbility(best.copy(), sim) ? String.valueOf(best) : null, land);
    }

    // ---- arm (f): their response to MY action -----------------------------
    //
    // Layered on arm (e) behind -Dcardguru.respond=true. At the windows
    // that follow my own action — my spell on the stack, my permanent just
    // resolved with its ETB done, my blockers just declared — the opponent
    // takes their single best instant-speed play from the SEATED hand,
    // adversarially (highest mana value), and the leaf shows the result.
    //
    // No extra branching: the reseated hand already is the chance layer.
    // Per sample, if their hand plus open mana allows a response they take
    // it; if not they do not. "P(they hold the counter)" is the fraction of
    // samples in which they drew it. The engine decides what is legal at
    // each window — a removal spell cannot target my creature while it is
    // still a spell, so it never fires in window 1; ninjutsu needs an
    // unblocked attacker, so it only fires after blocks. No card names.
    private final boolean respondOn = Boolean.getBoolean("cardguru.respond");
    private int projRespondFired = 0;

    /** Their best instant-speed play right now, from the seated hand,
     *  activated (and left for the caller to resolve). Null if none, or
     *  if arm (f) is off. */
    private String opponentRespond(Game sim, UUID oppId) {
        if (!respondOn) {
            return null;
        }
        Player opp = sim.getPlayer(oppId);
        if (opp == null) {
            return null;
        }
        // They can only respond while holding priority, and at every window
        // this is called from the copy's priority is with ME (I just cast,
        // or I just declared blocks). Without this, getPlayable returned
        // nothing for them in 128 straight copies of g9. Hand it over for
        // the lookup and the activation, then hand it back.
        UUID prevPriority = sim.getState().getPriorityPlayerId();
        sim.getState().setPriorityPlayerId(oppId);
        try {
            ActivatedAbility best = null;
            int bestMv = -1;
            for (ActivatedAbility a : opp.getPlayable(sim, true)) {
                if (a instanceof mage.abilities.mana.ManaAbility
                        || a instanceof PlayLandAbility) {
                    continue;
                }
                int mv = a.getManaCosts() == null ? 0 : a.getManaCosts().manaValue();
                if (mv > bestMv) {
                    bestMv = mv;
                    best = a;
                }
            }
            if (best == null) {
                return null;
            }
            if (opp.activateAbility(best.copy(), sim)) {
                projRespondFired++;
                return String.valueOf(best);
            }
            return null;
        } finally {
            if (prevPriority != null) {
                sim.getState().setPriorityPlayerId(prevPriority);
            }
        }
    }

    /** What I could do right now on their turn: playable, non-mana,
     *  non-land — instant speed by construction since it is not my turn. */
    private static List<ActivatedAbility> myInstantResponses(Game sim, UUID myId) {
        List<ActivatedAbility> out = new ArrayList<>();
        Player me = sim.getPlayer(myId);
        if (me == null) {
            return out;
        }
        for (ActivatedAbility a : me.getPlayable(sim, true)) {
            if (!(a instanceof mage.abilities.mana.ManaAbility)
                    && !(a instanceof PlayLandAbility)) {
                out.add(a);
            }
        }
        return out;
    }

    private static boolean castMine(Game b, UUID myId, ActivatedAbility r) {
        Player me = b.getPlayer(myId);
        return me != null && me.activateAbility(r.copy(), b);
    }

    private ScoredLeaf projectedLeaf(Game g, UUID myId, UUID oppId, String line,
                                     int sample, String response) {
        JsonObject s = compactLeaf(g, myId, oppId, line);
        s.addProperty("sample", sample);
        s.addProperty("response", response);
        double h = GameStateEvaluator2.evaluate(myId, g).getTotalScore();
        return new ScoredLeaf(s, h);
    }

    /** Backup that understands projected leaves. A candidate whose leaves
     *  carry a "sample" index is valued as the MEAN over samples of the MAX
     *  over my responses within each sample (expectimax over the reseated
     *  hand, max over my own reply). Leaves without one — the unopposed
     *  arm-(d) rollout — keep the worst-leaf rule. */
    private int argmaxProjected(int nCandidates, List<List<ScoredLeaf>> leaves,
                                double[] scores) {
        double[] v = candidateValues(nCandidates, leaves, scores, false);
        return pickBest(v, nCandidates, leaves, scores, false);
    }

    /** Per-candidate value. Projected candidates (leaves tagged with a
     *  sample) are the mean over samples of the best leaf within each
     *  sample; unprojected ones (or minRule) the worst leaf. Uses the LLM
     *  scores when given, the stored heuristics otherwise. */
    private static double[] candidateValues(int nCandidates, List<List<ScoredLeaf>> leaves,
                                            double[] scores, boolean minRule) {
        double[] out = new double[nCandidates];
        int flat = 0;
        for (int c = 0; c < nCandidates; c++) {
            List<ScoredLeaf> ls = leaves.get(c);
            double v;
            if (ls.isEmpty()) {
                v = Double.NEGATIVE_INFINITY;
            } else if (minRule || !ls.get(0).summary.has("sample")) {
                v = Double.POSITIVE_INFINITY;
                for (ScoredLeaf l : ls) {
                    v = Math.min(v, scores != null ? scores[flat] : l.heuristic);
                    flat++;
                }
            } else {
                Map<Integer, Double> perSample = new HashMap<>();
                for (ScoredLeaf l : ls) {
                    double lv = scores != null ? scores[flat] : l.heuristic;
                    flat++;
                    int k = l.summary.get("sample").getAsInt();
                    perSample.merge(k, lv, Math::max);
                }
                double sum = 0;
                for (double x : perSample.values()) {
                    sum += x;
                }
                v = sum / perSample.size();
            }
            out[c] = v;
        }
        return out;
    }

    // ---- tie-break ---------------------------------------------------------
    //
    // Measured on the recorded Izzet game: in about half the searches the
    // best and runner-up candidate were within one point on a 0-100 scale,
    // i.e. the pick was noise. Within cardguru.tie_margin the engine's own
    // evaluator (GameStateEvaluator2, already computed per leaf) decides
    // among the tied candidates; with cardguru.tie_compare=true the pilot
    // is first asked one pairwise question (top two, same-sample leaves side
    // by side), which is a more reliable question for an LLM than an
    // absolute score.
    private static final double TIE_MARGIN =
            Double.parseDouble(System.getProperty("cardguru.tie_margin", "2"));
    private static final boolean TIE_COMPARE = Boolean.getBoolean("cardguru.tie_compare");
    private double[] lastAggValues = new double[0];
    private double lastAggGap = Double.NaN;
    private String lastTieBreak = "none";
    private int tieBreaksHeuristic = 0;
    private int tieBreaksCompare = 0;

    private int pickBest(double[] v, int n, List<List<ScoredLeaf>> leaves,
                         double[] scores, boolean minRule) {
        lastAggValues = v.clone();
        lastTieBreak = "none";
        lastAggGap = Double.NaN;
        int best = 0;
        for (int c = 1; c < n; c++) {
            if (v[c] > v[best]) {
                best = c;
            }
        }
        if (n < 2 || scores == null || Double.isInfinite(v[best])) {
            return best;
        }
        int second = -1;
        for (int c = 0; c < n; c++) {
            if (c != best && (second < 0 || v[c] > v[second])) {
                second = c;
            }
        }
        lastAggGap = v[best] - v[second];
        if (lastAggGap >= TIE_MARGIN) {
            return best;
        }
        // Tied set: everything within the margin of the best.
        List<Integer> tied = new ArrayList<>();
        for (int c = 0; c < n; c++) {
            if (v[best] - v[c] < TIE_MARGIN) {
                tied.add(c);
            }
        }
        if (TIE_COMPARE && pendingCompare != null) {
            int r = pendingCompare.apply(best, second);
            if (r >= 0) {
                tieBreaksCompare++;
                lastTieBreak = "compare:" + (r == best ? "kept" : "flipped");
                return r;
            }
        }
        double[] h = candidateValues(n, leaves, null, minRule);
        int pick = best;
        for (int c : tied) {
            if (h[c] > h[pick]) {
                pick = c;
            }
        }
        tieBreaksHeuristic++;
        lastTieBreak = "heuristic:" + (pick == best ? "kept" : "flipped");
        return pick;
    }

    /** Set by the search that owns the current decision when tie_compare is
     *  on: given the two tied candidates, asks the pilot and returns the
     *  winner, or -1 when undecided. */
    private java.util.function.BinaryOperator<Integer> pendingCompare = null;

    /** One pairwise question to the pilot: candidate a vs candidate b, each
     *  sample's best leaf side by side. Returns the preferred candidate or
     *  -1 when the answer is missing or balanced. */
    private int askCompare(Game game, String decision, List<String> labels,
                           List<List<ScoredLeaf>> leaves, double[] scores, int a, int b) {
        int[] start = new int[labels.size() + 1];
        for (int c = 0; c < labels.size(); c++) {
            start[c + 1] = start[c] + leaves.get(c).size();
        }
        Map<Integer, JsonObject> bestA = bestLeafPerSample(leaves.get(a), scores, start[a]);
        Map<Integer, JsonObject> bestB = bestLeafPerSample(leaves.get(b), scores, start[b]);
        JsonArray pairs = new JsonArray();
        for (Map.Entry<Integer, JsonObject> e : bestA.entrySet()) {
            JsonObject lb = bestB.get(e.getKey());
            if (lb == null) {
                continue;
            }
            JsonObject pair = new JsonObject();
            pair.addProperty("sample", e.getKey());
            pair.add("a", e.getValue());
            pair.add("b", lb);
            pairs.add(pair);
        }
        if (pairs.size() == 0) {
            return -1;
        }
        JsonObject req = baseRequest("leaf_compare", game);
        req.addProperty("decision", decision);
        req.addProperty("a_label", labels.get(a));
        req.addProperty("b_label", labels.get(b));
        req.addProperty("a_value", lastAggValues[a]);
        req.addProperty("b_value", lastAggValues[b]);
        req.add("pairs", pairs);
        req.addProperty("pair_count", pairs.size());
        JsonObject resp = ask(req);
        if (resp == null || !resp.has("prefer") || !resp.get("prefer").isJsonArray()) {
            return -1;
        }
        int sum = 0;
        try {
            for (JsonElement el : resp.getAsJsonArray("prefer")) {
                sum += Integer.signum(el.getAsInt());
            }
        } catch (RuntimeException e) {
            return -1;
        }
        return sum > 0 ? a : sum < 0 ? b : -1;
    }

    private static Map<Integer, JsonObject> bestLeafPerSample(List<ScoredLeaf> ls, double[] scores,
                                                              int offset) {
        Map<Integer, JsonObject> out = new LinkedHashMap<>();
        Map<Integer, Double> bestScore = new HashMap<>();
        for (int i = 0; i < ls.size(); i++) {
            ScoredLeaf l = ls.get(i);
            int k = l.summary.has("sample") ? l.summary.get("sample").getAsInt() : i;
            double sc = scores[offset + i];
            Double prev = bestScore.get(k);
            if (prev == null || sc > prev) {
                bestScore.put(k, sc);
                JsonObject o = l.summary.deepCopy();
                o.addProperty("score", sc);
                out.put(k, o);
            }
        }
        return out;
    }

    /** One-line-per-side board summary of a resolved leaf copy. */
    private JsonObject compactLeaf(Game leaf, UUID myId, UUID oppId, String label) {
        JsonObject o = new JsonObject();
        o.addProperty("line", label);
        Player me = leaf.getPlayer(myId);
        Player opp = leaf.getPlayer(oppId);
        o.addProperty("our_life", me == null ? 0 : me.getLife());
        o.addProperty("opp_life", opp == null ? 0 : opp.getLife());
        o.addProperty("our_board", boardLine(leaf, myId));
        o.addProperty("opp_board", boardLine(leaf, oppId));
        // What each side can still DO from this position. The five fields
        // above describe a board; they never said whether it was reached by
        // tapping out into the opponent's turn, so the pilot could not price
        // that — the pattern every lost mirror game shares. Open mana on both
        // sides, hand sizes, my remaining hand (I know my own cards, so the
        // pilot can see "I still hold an answer"), and the stack.
        o.addProperty("our_mana", manaOf(leaf, myId));
        o.addProperty("opp_mana", manaOf(leaf, oppId));
        o.addProperty("our_hand_count", me == null ? 0 : me.getHand().size());
        o.addProperty("opp_hand_count", opp == null ? 0 : opp.getHand().size());
        // Graveyard sizes: cost reducers (Eddymurk Crab, Hearth Elemental)
        // and recursion make them part of what a board is worth, and they
        // are why a 4-land opponent could cast a 7-drop in the replay.
        o.addProperty("our_graveyard_count", me == null ? 0 : me.getGraveyard().size());
        o.addProperty("opp_graveyard_count", opp == null ? 0 : opp.getGraveyard().size());
        o.addProperty("turn", leaf.getTurnNum());
        JsonArray hand = new JsonArray();
        if (me != null) {
            for (Card c : me.getHand().getCards(leaf)) {
                boolean drawn = searchHandIds != null && !searchHandIds.contains(c.getId());
                hand.add(c.getName() + (drawn ? " (drawn)" : ""));
            }
        }
        o.add("our_hand", hand);
        JsonArray stack = new JsonArray();
        for (mage.game.stack.StackObject so : leaf.getStack()) {
            stack.add(so.getName() + " (" + (so.getControllerId().equals(myId)
                    ? "ours" : "theirs") + ")");
        }
        o.add("stack", stack);
        return o;
    }

    /** Mana a player could produce right now on this game (a leaf or the
     *  live one). Never throws: an empty string just means "unknown". */
    private static String manaOf(Game g, UUID pid) {
        try {
            Player p = g.getPlayer(pid);
            return p == null ? "" : String.valueOf(p.getManaAvailable(g));
        } catch (Exception e) {
            return "?";
        }
    }

    private String boardLine(Game leaf, UUID pid) {
        List<String> creatures = new ArrayList<>();
        List<String> others = new ArrayList<>();
        int lands = 0;
        int landsUntapped = 0;
        for (Permanent p : leaf.getBattlefield().getAllActivePermanents(pid)) {
            if (p.isCreature(leaf)) {
                creatures.add(p.getName() + " " + p.getPower().getValue() + "/"
                        + p.getToughness().getValue() + (p.isTapped() ? " T" : ""));
            } else if (p.isLand(leaf)) {
                lands++;
                if (!p.isTapped()) {
                    landsUntapped++;
                }
            } else {
                // Enchantments, artifacts, planeswalkers: invisible before,
                // so two boards that differed only by an Ascension or a
                // planeswalker read as identical to the pilot.
                String extra = "";
                try {
                    if (p.isPlaneswalker(leaf)) {
                        extra = " L" + p.getCounters(leaf).getCount(CounterType.LOYALTY);
                    }
                } catch (RuntimeException ignored) {
                }
                others.add(p.getName() + extra + (p.isTapped() ? " T" : ""));
            }
        }
        String s = creatures.isEmpty() ? "no creatures" : String.join(", ", creatures);
        if (!others.isEmpty()) {
            s += " | " + String.join(", ", others);
        }
        return s + " | " + lands + " lands (" + landsUntapped + " untapped)";
    }

    // ---- leaf value memo (dynamic programming over leaf states) ----------
    //
    // A leaf's value is a function of the leaf STATE, not of the candidate
    // or the window that produced it. Measured on the overnight suite, 30-53%
    // of all leaves the pilot scored were states it had already scored
    // earlier in the same turn, and 20-33% were duplicates inside the same
    // request; when it re-scored a state within a turn the median change was
    // 0-3 points. So:
    //   1. duplicate leaves inside one request are sent once and the score is
    //      expanded back (shorter prompt, less thinking);
    //   2. leaves scored earlier this turn are sent WITH their earlier score
    //      as `prior_score`, so the pilot scores the new leaves on the same
    //      scale instead of inventing one (tier 2 in the plan);
    //   3. a request whose leaves are ALL cached is answered from the cache
    //      without a call, but only when the decision is clear-cut: the best
    //      candidate must lead the runner-up by LEAF_CACHE_MARGIN under both
    //      mean and min aggregation. Otherwise ask (tier 3, gated).
    // The cache is cleared at every new turn: scores are absolute-ish (see
    // the briefing's rubric) but drift with the game, and "seen earlier in
    // the game" never exceeded "seen earlier this turn" in the suite data.
    private final Map<String, double[]> leafValueCache = new HashMap<>();
    private int leafCacheTurn = -1;
    private static final double LEAF_CACHE_MARGIN =
            Double.parseDouble(System.getProperty("cardguru.leaf_cache_margin", "10"));
    private static final boolean LEAF_CACHE_ON =
            !"false".equals(System.getProperty("cardguru.leaf_cache", "true"));
    private int leafCacheFullHits = 0;      // requests answered without a call
    private int leafCacheLeavesSaved = 0;   // leaves not sent because cached
    private int leafDedupSaved = 0;         // leaves not sent because duplicate
    private int leavesTotalLast = 0;
    private int leavesSentLast = 0;

    /** Canonical key for a leaf state. Projected leaves (arm (e), tagged
     *  with a `sample`) are end-of-opponent-turn states and compare across
     *  windows; an unprojected leaf is a mid-turn state and is keyed on the
     *  step it was reached in, because "the same board with combat still
     *  to come" is a different state from "the same board after combat". */
    private static String leafKey(JsonObject summary, Game game) {
        JsonObject k = new JsonObject();
        List<String> names = new ArrayList<>(summary.keySet());
        Collections.sort(names);
        for (String n : names) {
            if (n.equals("line") || n.equals("leaf_index") || n.equals("sample")
                    || n.equals("response") || n.equals("prior_score")) {
                continue;
            }
            k.add(n, summary.get(n));
        }
        // Unprojected leaves are keyed on the combat BUCKET, not the exact
        // step: a board seen at upkeep, draw and precombat main is the same
        // state (combat still to come); keying on the step gave 3 hits in a
        // whole game where the measurement had promised a third of leaves.
        String prefix = summary.has("sample") ? "P|" : "S|" + combatBucket(game) + "|";
        return prefix + k;
    }

    private static String combatBucket(Game game) {
        PhaseStep s = game.getTurnStepType();
        if (s == null) {
            return "?";
        }
        switch (s) {
            case UNTAP: case UPKEEP: case DRAW: case PRECOMBAT_MAIN: case BEGIN_COMBAT:
                return "pre";
            case DECLARE_ATTACKERS: case DECLARE_BLOCKERS: case FIRST_COMBAT_DAMAGE:
            case COMBAT_DAMAGE: case END_COMBAT:
                return "combat";
            default:
                return "post";
        }
    }

    /** The "sN: their T.. — ..." fragment of a projected leaf line. */
    private static String sampleFragment(JsonObject summary) {
        String line = summary.has("line") ? summary.get("line").getAsString() : "";
        for (String part : line.split(" \\| ")) {
            if (part.matches("s\\d+: .*")) {
                return part;
            }
        }
        return "";
    }

    private static double meanOf(List<Double> xs) {
        double s = 0;
        for (double x : xs) {
            s += x;
        }
        return xs.isEmpty() ? 0 : s / xs.size();
    }

    /** Send every leaf in one "leaf_eval" request; return the flat score list
     *  or null when the response is missing/short (caller falls back). */
    private double[] askLeafScores(Game game, String decision,
                                   List<String> candidateLabels,
                                   List<List<ScoredLeaf>> leavesPerCandidate) {
        if (game.getTurnNum() != leafCacheTurn) {
            leafValueCache.clear();
            leafCacheTurn = game.getTurnNum();
        }
        // Flatten, key, and dedup.
        int total = 0;
        List<String> flatKeys = new ArrayList<>();
        List<Integer> flatCand = new ArrayList<>();
        Map<String, Integer> uniqueIndex = new LinkedHashMap<>();
        List<JsonObject> uniqueSummary = new ArrayList<>();
        List<Integer> uniqueCand = new ArrayList<>();
        for (int c = 0; c < candidateLabels.size(); c++) {
            for (ScoredLeaf l : leavesPerCandidate.get(c)) {
                String key = LEAF_CACHE_ON ? leafKey(l.summary, game) : "n" + total;
                flatKeys.add(key);
                flatCand.add(c);
                if (!uniqueIndex.containsKey(key)) {
                    uniqueIndex.put(key, uniqueSummary.size());
                    uniqueSummary.add(l.summary);
                    uniqueCand.add(c);
                }
                total++;
            }
        }
        leavesTotalLast = total;
        int unique = uniqueSummary.size();
        int cached = 0;
        for (String key : uniqueIndex.keySet()) {
            if (leafValueCache.containsKey(key)) {
                cached++;
            }
        }

        // Tier 3: everything cached and the decision is clear-cut.
        if (LEAF_CACHE_ON && unique > 0 && cached == unique) {
            double[] scores = new double[total];
            for (int i = 0; i < total; i++) {
                scores[i] = leafValueCache.get(flatKeys.get(i))[0];
            }
            if (clearCutUnderBothAggregations(candidateLabels.size(), flatCand, scores)) {
                leafCacheFullHits++;
                leafCacheLeavesSaved += unique;
                leafDedupSaved += total - unique;
                leavesSentLast = 0;
                return scores;
            }
        }

        JsonObject req = baseRequest("leaf_eval", game);
        req.addProperty("decision", decision);
        JsonArray cands = new JsonArray();
        List<JsonArray> perCand = new ArrayList<>();
        for (int c = 0; c < candidateLabels.size(); c++) {
            JsonObject co = new JsonObject();
            co.addProperty("label", candidateLabels.get(c));
            JsonArray ls = new JsonArray();
            perCand.add(ls);
            co.add("leaves", ls);
            cands.add(co);
        }
        int sent = 0;
        List<String> uniqueKeys = new ArrayList<>(uniqueIndex.keySet());
        for (int u = 0; u < unique; u++) {
            JsonObject lo = uniqueSummary.get(u).deepCopy();
            lo.addProperty("leaf_index", sent++);
            double[] prior = leafValueCache.get(uniqueKeys.get(u));
            if (prior != null) {
                lo.addProperty("prior_score", Math.round(prior[0]));
            }
            perCand.get(uniqueCand.get(u)).add(lo);
        }
        req.add("candidates", cands);
        req.addProperty("leaf_count", sent);
        // The same leaves regrouped by opponent sample, so the pilot can
        // compare candidates under the SAME opponent draw. Grouped only by
        // candidate, 20-60 near-identical leaves got 2-5 distinct scores and
        // the pick came down to fractions of a point.
        boolean projected = false;
        Map<Integer, JsonObject> bySample = new LinkedHashMap<>();
        sent = 0;
        for (int u = 0; u < unique; u++) {
            JsonObject sm = uniqueSummary.get(u);
            int idx = sent++;
            if (!sm.has("sample")) {
                continue;
            }
            projected = true;
            int k = sm.get("sample").getAsInt();
            JsonObject grp = bySample.get(k);
            if (grp == null) {
                grp = new JsonObject();
                grp.addProperty("sample", k);
                grp.addProperty("their_line", sampleFragment(sm));
                grp.add("leaves", new JsonArray());
                bySample.put(k, grp);
            }
            JsonObject e = new JsonObject();
            e.addProperty("leaf_index", idx);
            e.addProperty("candidate", candidateLabels.get(uniqueCand.get(u)));
            if (sm.has("response")) {
                e.addProperty("response", sm.get("response").getAsString());
            }
            grp.getAsJsonArray("leaves").add(e);
        }
        if (projected) {
            JsonArray samples = new JsonArray();
            for (JsonObject g : bySample.values()) {
                samples.add(g);
            }
            req.add("samples", samples);
        }
        req.addProperty("aggregation", projected
                ? "candidate value = mean over samples of its best leaf within each sample"
                : "candidate value = its worst leaf");
        if (total != sent) {
            req.addProperty("duplicate_leaves_collapsed", total - sent);
        }
        if (cached > 0) {
            req.addProperty("leaves_with_prior_score", cached);
        }
        leavesSentLast = sent;
        leafDedupSaved += total - sent;

        JsonObject resp = ask(req);
        if (!resp.has("scores") || !resp.get("scores").isJsonArray()) {
            return null;
        }
        JsonArray arr = resp.getAsJsonArray("scores");
        if (arr.size() < sent) {
            return null;
        }
        double[] uniqueScores = new double[sent];
        try {
            for (int i = 0; i < sent; i++) {
                uniqueScores[i] = arr.get(i).getAsDouble();
            }
        } catch (Exception e) {
            return null;
        }
        // Anchor: candidate 0 is always the status quo ("pass", "attack-none",
        // "no-blocks"); its mean is the request's reference level. Stored so
        // a later window can re-base if it ever needs to.
        List<Double> anchorScores = new ArrayList<>();
        for (int u = 0; u < unique; u++) {
            if (uniqueCand.get(u) == 0) {
                anchorScores.add(uniqueScores[u]);
            }
        }
        double anchor = anchorScores.isEmpty() ? 50 : meanOf(anchorScores);
        for (int u = 0; u < unique; u++) {
            leafValueCache.put(uniqueKeys.get(u),
                    new double[]{uniqueScores[u], uniqueScores[u] - anchor});
        }
        double[] scores = new double[total];
        for (int i = 0; i < total; i++) {
            scores[i] = uniqueScores[uniqueIndex.get(flatKeys.get(i))];
        }
        return scores;
    }

    /** True when one candidate leads the runner-up by LEAF_CACHE_MARGIN under
     *  BOTH mean-of-leaves and min-of-leaves, and it is the same candidate.
     *  Every decision rule in this file (worst leaf, mean of max) sits
     *  between those two, so a lead under both is a lead under any. */
    private static boolean clearCutUnderBothAggregations(int nCand, List<Integer> flatCand,
                                                         double[] scores) {
        double[] mean = new double[nCand];
        double[] min = new double[nCand];
        int[] n = new int[nCand];
        Arrays.fill(min, Double.POSITIVE_INFINITY);
        for (int i = 0; i < scores.length; i++) {
            int c = flatCand.get(i);
            mean[c] += scores[i];
            min[c] = Math.min(min[c], scores[i]);
            n[c]++;
        }
        int bestMean = -1, bestMin = -1;
        double m1 = Double.NEGATIVE_INFINITY, m2 = Double.NEGATIVE_INFINITY;
        double k1 = Double.NEGATIVE_INFINITY, k2 = Double.NEGATIVE_INFINITY;
        for (int c = 0; c < nCand; c++) {
            if (n[c] == 0) {
                continue;
            }
            mean[c] /= n[c];
            if (mean[c] > m1) {
                m2 = m1; m1 = mean[c]; bestMean = c;
            } else if (mean[c] > m2) {
                m2 = mean[c];
            }
            if (min[c] > k1) {
                k2 = k1; k1 = min[c]; bestMin = c;
            } else if (min[c] > k2) {
                k2 = min[c];
            }
        }
        if (bestMean < 0 || bestMean != bestMin) {
            return false;
        }
        boolean single = Double.isInfinite(m2);   // only one candidate
        return single || (m1 - m2 >= LEAF_CACHE_MARGIN && k1 - k2 >= LEAF_CACHE_MARGIN);
    }

    // ---- plan-scoped search ----------------------------------------------
    //
    // Turn-plan mode's missing piece. The pilot proposes two or three whole
    // lines for its turn (main-phase casts, an attack spec, postcombat
    // casts); the driver plays each out on reseated copies — my casts, my
    // attack against the engine's worst block for me, my postcombat casts,
    // then the opponent's projected turn with my instant-speed responses
    // (the arm (e) tail) — and the pilot scores the leaves once. The best
    // line becomes the plan the bridge executes for free. PokéChamp's
    // shape: LLM proposes, engine simulates, LLM values, one call per turn.
    private static final boolean planSearchOn =
            !"false".equals(System.getProperty("cardguru.plan_search", "true"));

    /** Find the playable ability a plan step names ("cast X", "play X",
     *  "activate <fragment>"), or null. Target hints after " @ " are ignored
     *  on the copy: the AI's own targeting stands in for them. */
    private static ActivatedAbility findByLabel(Game sim, UUID myId, String step) {
        Player me = sim.getPlayer(myId);
        if (me == null || step == null) {
            return null;
        }
        String s = step.trim().toLowerCase();
        int at = s.indexOf(" @ ");
        if (at >= 0) {
            s = s.substring(0, at).trim();
        }
        int sp = s.indexOf(' ');
        String verb = sp < 0 ? s : s.substring(0, sp);
        String rest = sp < 0 ? "" : s.substring(sp + 1).trim();
        if (rest.isEmpty()) {
            return null;
        }
        for (ActivatedAbility a : me.getPlayable(sim, true)) {
            if (a instanceof mage.abilities.mana.ManaAbility) {
                continue;
            }
            String t = String.valueOf(a).toLowerCase();
            if (verb.equals("cast") && t.startsWith("cast ") && t.contains(rest)) {
                return a;
            }
            if (verb.equals("play") && t.startsWith("play ") && t.contains(rest)) {
                return a;
            }
            if (verb.equals("activate") && !t.startsWith("cast ") && t.contains(rest)) {
                return a;
            }
        }
        return null;
    }

    private static List<String> strList(JsonObject o, String key) {
        List<String> out = new ArrayList<>();
        if (o != null && o.has(key) && o.get(key).isJsonArray()) {
            for (JsonElement e : o.getAsJsonArray(key)) {
                if (e.isJsonPrimitive()) {
                    out.add(e.getAsString());
                } else if (e.isJsonObject() && e.getAsJsonObject().has("action")) {
                    out.add(e.getAsJsonObject().get("action").getAsString());
                }
            }
        }
        return out;
    }

    /** Apply plan steps on a copy in order; returns the steps that were not
     *  available (so the leaf label can say the line was not fully legal). */
    private String applySteps(Game sim, UUID myId, List<String> steps) {
        StringBuilder missing = new StringBuilder();
        Player me = sim.getPlayer(myId);
        for (String step : steps) {
            ActivatedAbility a = findByLabel(sim, myId, step);
            if (a == null || me == null || !me.activateAbility(a.copy(), sim)) {
                missing.append(missing.length() == 0 ? "" : ", ").append(step);
                continue;
            }
            sim.checkStateAndTriggered();
            resolveStack(sim);
        }
        return missing.toString();
    }

    /** Enter combat on the copy, declare the spec'd attackers, and resolve
     *  against the block response the engine heuristic rates worst for me
     *  (the same pessimism the attack search keeps). */
    private void attackOnCopy(Game sim, UUID myId, UUID oppId, String spec) {
        String s = spec == null ? "attack_none" : spec.trim().toLowerCase();
        if (s.isEmpty() || s.equals("attack_none") || s.equals("none") || s.equals("ask")) {
            return;
        }
        sim.getTurn().setPhase(new CombatPhase());
        simulateStep(sim, new BeginCombatStep());
        sim.getPhase().setStep(new DeclareAttackersStep());
        boolean all = s.equals("attack_all") || s.equals("all");
        List<String> names = new ArrayList<>();
        if (!all) {
            for (String n : s.replaceFirst("^attack ", "").split(",")) {
                if (!n.trim().isEmpty()) {
                    names.add(n.trim());
                }
            }
        }
        Player me = sim.getPlayer(myId);
        boolean any = false;
        for (Permanent p : new ArrayList<>(sim.getBattlefield().getAllActivePermanents(myId))) {
            if (!p.isCreature(sim) || !p.canAttack(oppId, sim)) {
                continue;
            }
            boolean pick = all;
            for (String n : names) {
                if (p.getName().toLowerCase().contains(n)) {
                    pick = true;
                }
            }
            if (pick && me != null) {
                me.declareAttacker(p.getId(), oppId, sim, false);
                any = true;
            }
        }
        if (!any) {
            return;
        }
        fireAttackDeclared(sim);
        List<UUID[]> worst = new ArrayList<>();
        double worstH = Double.POSITIVE_INFINITY;
        for (List<UUID[]> resp : enumerateBlockResponses(sim, oppId)) {
            Game leaf = sim.copy();
            applyBlocksAndResolveCombat(leaf, oppId, resp);
            double h = GameStateEvaluator2.evaluate(myId, leaf).getTotalScore();
            if (h < worstH) {
                worstH = h;
                worst = resp;
            }
        }
        applyBlocksAndResolveCombat(sim, oppId, worst);
    }

    /** The arm (e) tail, shared with the priority projection: hand the copy
     *  to the opponent, let them play, give me two response windows. */
    private void projectOpponentTurn(Game sim, UUID myId, UUID oppId, String label,
                                     int k, List<ScoredLeaf> out) {
        beginOpponentTurn(sim, oppId);
        OppTurn theirs = opponentMainPhase(sim, oppId);
        String base = label + " | " + theirTurnLabel(sim, k, theirs);
        if (theirs.spell == null) {
            out.add(projectedLeaf(sim, myId, oppId, base, k, "nothing"));
            return;
        }
        int n = 0;
        for (ActivatedAbility r : myInstantResponses(sim, myId)) {
            if (n >= MAX_RESPONSES_PER_WINDOW) {
                break;
            }
            Game b = branch(sim);
            if (castMine(b, myId, r)) {
                resolveStack(b);
                out.add(projectedLeaf(b, myId, oppId,
                        base + " | on the stack I cast " + r, k, "stack:" + r));
                n++;
            }
        }
        resolveStack(sim);
        sim.checkStateAndTriggered();
        resolveStack(sim);
        n = 0;
        for (ActivatedAbility r : myInstantResponses(sim, myId)) {
            if (n >= MAX_RESPONSES_PER_WINDOW) {
                break;
            }
            Game b = branch(sim);
            if (castMine(b, myId, r)) {
                resolveStack(b);
                out.add(projectedLeaf(b, myId, oppId,
                        base + " | after it resolves I cast " + r, k, "post:" + r));
                n++;
            }
        }
        out.add(projectedLeaf(sim, myId, oppId, base + " | I do nothing", k, "nothing"));
    }

    /** One candidate line played out on K reseated copies. */
    private List<ScoredLeaf> rolloutLine(Game game, UUID myId, UUID oppId,
                                         JsonObject line, String label) {
        List<ScoredLeaf> out = new ArrayList<>();
        List<String> main1 = strList(line, "main1");
        List<String> main2 = strList(line, "main2");
        String attack = line.has("attack") && line.get("attack").isJsonPrimitive()
                ? line.get("attack").getAsString() : "attack_none";
        for (int k = 0; k < Math.max(1, projectTurnK); k++) {
            Game sim;
            try {
                sim = simCopy(game);
            } catch (Exception e) {
                continue;
            }
            boolean prev = searching;
            searching = true;
            try {
                String miss1 = applySteps(sim, myId, main1);
                attackOnCopy(sim, myId, oppId, attack);
                sim.getTurn().setPhase(new PostCombatMainPhase());
                sim.getPhase().setStep(new PostCombatMainStep());
                sim.getState().setPriorityPlayerId(myId);
                String miss2 = applySteps(sim, myId, main2);
                String tag = label;
                if (!miss1.isEmpty() || !miss2.isEmpty()) {
                    tag += " | NOT available: " + miss1
                            + (miss1.isEmpty() || miss2.isEmpty() ? "" : ", ") + miss2;
                }
                projectOpponentTurn(sim, myId, oppId, tag, k, out);
            } catch (Exception e) {
                projSamplesFailed++;
                projLastFailure = String.valueOf(e);
            } finally {
                searching = prev;
            }
        }
        return out;
    }

    /** The bridge answered a priority window with {"simulate": [lines]}:
     *  roll each line out, have the pilot score the leaves, then re-ask the
     *  same window with the chosen line so the bridge installs it. */
    private JsonObject planSearch(Game game, JsonObject req, JsonObject resp) {
        UUID myId = this.getId();
        UUID oppId = null;
        for (UUID pid : game.getOpponents(myId)) {
            oppId = pid;
        }
        JsonArray lines = resp.getAsJsonArray("simulate");
        List<String> labels = new ArrayList<>();
        List<List<ScoredLeaf>> leaves = new ArrayList<>();
        for (int i = 0; i < lines.size(); i++) {
            JsonObject line = lines.get(i).isJsonObject()
                    ? lines.get(i).getAsJsonObject() : new JsonObject();
            String label = line.has("label") && line.get("label").isJsonPrimitive()
                    ? line.get("label").getAsString() : "line " + i;
            labels.add(label);
            leaves.add(rolloutLine(game, myId, oppId, line, label));
        }
        double[] scores = askLeafScores(game, "plan", labels, leaves);
        pendingCompare = (x, y) -> askCompare(game, "plan", labels, leaves, scores, x, y);
        int best = scores == null ? 0 : argmaxProjected(labels.size(), leaves, scores);
        pendingCompare = null;
        traceLlmSearch("plan", labels, leaves, scores, best, game);
        JsonObject again = req.deepCopy();
        JsonObject chosen = new JsonObject();
        chosen.addProperty("index", best);
        chosen.addProperty("label", labels.get(best));
        chosen.addProperty("scored", scores != null);
        again.add("chosen_line", chosen);
        return ask(again);
    }

    /** Rolled-out attack candidate: declare the set on a copy, resolve, keep
     *  the K heuristically-worst block-response leaves. */
    private List<ScoredLeaf> rolloutAttackLeaves(Game game, UUID myId, UUID defenderId,
                                                 List<Permanent> attackers,
                                                 List<Integer> set) {
        Game afterAttack = simCopy(game);
        for (int idx : set) {
            Permanent atk = attackers.get(idx);
            Permanent simAtk = afterAttack.getPermanent(atk.getId());
            if (simAtk != null && defenderId != null
                    && simAtk.canAttack(defenderId, afterAttack)) {
                afterAttack.getPlayer(myId)
                        .declareAttacker(atk.getId(), defenderId, afterAttack, false);
            }
        }
        fireAttackDeclared(afterAttack);

        List<ScoredLeaf> leaves = new ArrayList<>();
        int r = 0;
        for (List<UUID[]> resp : enumerateBlockResponses(afterAttack, defenderId)) {
            Game leaf = afterAttack.copy();
            applyBlocksAndResolveCombat(leaf, defenderId, resp);
            double h = GameStateEvaluator2.evaluate(myId, leaf).getTotalScore();
            String label = resp.isEmpty() ? "unblocked"
                    : resp.size() + " block(s), response " + r;
            leaves.add(new ScoredLeaf(compactLeaf(leaf, myId, defenderId, label), h));
            r++;
        }
        leaves.sort((x, y) -> Double.compare(x.heuristic, y.heuristic));
        if (leaves.size() > LLM_LEAVES_PER_CANDIDATE) {
            leaves = new ArrayList<>(leaves.subList(0, LLM_LEAVES_PER_CANDIDATE));
        }
        return leaves;
    }

    private void llmSearchAttackers(Game game, UUID defenderId,
                                    List<Permanent> attackers) {
        UUID myId = this.getId();
        List<List<Integer>> candidates = candidateAttackSets(attackers.size());
        List<String> labels = new ArrayList<>();
        List<List<ScoredLeaf>> leaves = new ArrayList<>();
        for (List<Integer> set : candidates) {
            labels.add(labelFor(set, attackers));
            leaves.add(rolloutAttackLeaves(game, myId, defenderId, attackers, set));
        }

        double[] scores = askLeafScores(game, "attackers", labels, leaves);
        pendingCompare = (x, y) -> askCompare(game, "attackers", labels, leaves, scores, x, y);
        int best = argmaxOfMins(candidates.size(), leaves, scores);
        pendingCompare = null;
        for (int idx : candidates.get(best)) {
            Permanent atk = attackers.get(idx);
            if (defenderId != null && atk.canAttack(defenderId, game)) {
                getComputerPlayer().declareAttacker(atk.getId(), defenderId, game, false);
            }
        }
        traceLlmSearch("attackers", labels, leaves, scores, best, game);
    }

    /** Our candidate block assignments when defending: no-block, each legal
     *  single block, a greedy full block (each blocker onto the biggest
     *  still-unblocked attacker), and an all-gang onto the biggest attacker. */
    private List<List<UUID[]>> candidateBlockSets(Game game,
                                                  List<Permanent> blockers,
                                                  List<Permanent> attackers) {
        List<List<UUID[]>> sets = new ArrayList<>();
        sets.add(new ArrayList<>());   // no blocks
        for (Permanent b : blockers) {
            for (Permanent a : attackers) {
                if (b.canBlock(a.getId(), game)) {
                    List<UUID[]> s = new ArrayList<>();
                    s.add(new UUID[]{b.getId(), a.getId()});
                    sets.add(s);
                    if (sets.size() >= MAX_BLOCK_RESPONSES) {
                        return sets;
                    }
                }
            }
        }
        List<Permanent> byPower = new ArrayList<>(attackers);
        byPower.sort((x, y) -> y.getPower().getValue() - x.getPower().getValue());
        List<UUID[]> greedy = new ArrayList<>();
        Set<UUID> taken = new HashSet<>();
        for (Permanent b : blockers) {
            for (Permanent a : byPower) {
                if (!taken.contains(a.getId()) && b.canBlock(a.getId(), game)) {
                    greedy.add(new UUID[]{b.getId(), a.getId()});
                    taken.add(a.getId());
                    break;
                }
            }
        }
        if (greedy.size() > 1) {
            sets.add(greedy);
        }
        if (!byPower.isEmpty() && blockers.size() > 1) {
            Permanent big = byPower.get(0);
            List<UUID[]> gang = new ArrayList<>();
            for (Permanent b : blockers) {
                if (b.canBlock(big.getId(), game)) {
                    gang.add(new UUID[]{b.getId(), big.getId()});
                }
            }
            if (gang.size() > 1) {
                sets.add(gang);
            }
        }
        return sets;
    }

    private String blockLabel(Game game, List<UUID[]> set) {
        if (set.isEmpty()) {
            return "no-blocks";
        }
        List<String> parts = new ArrayList<>();
        for (UUID[] pair : set) {
            Permanent b = game.getPermanent(pair[0]);
            Permanent a = game.getPermanent(pair[1]);
            parts.add((b == null ? "?" : b.getName()) + ">"
                    + (a == null ? "?" : a.getName()));
        }
        return String.join(", ", parts);
    }

    private void llmSearchBlockers(Game game, UUID defendingPlayerId,
                                   List<Permanent> blockers,
                                   List<Permanent> attackers) {
        UUID myId = this.getId();
        UUID oppId = null;
        for (UUID pid : game.getOpponents(myId)) {
            oppId = pid;
        }
        List<List<UUID[]>> candidates = candidateBlockSets(game, blockers, attackers);
        List<String> labels = new ArrayList<>();
        List<List<ScoredLeaf>> leaves = new ArrayList<>();
        for (List<UUID[]> set : candidates) {
            labels.add(blockLabel(game, set));
            Game leaf = simCopy(game);
            String reply = applyBlocksAndResolveCombat(leaf, defendingPlayerId, set);
            double h = GameStateEvaluator2.evaluate(myId, leaf).getTotalScore();
            List<ScoredLeaf> one = new ArrayList<>();
            one.add(new ScoredLeaf(
                    compactLeaf(leaf, myId, oppId, "after combat"
                            + (reply != null ? " | after blocks they cast " + reply : "")), h));
            leaves.add(one);
        }

        double[] scores = askLeafScores(game, "blockers", labels, leaves);
        pendingCompare = (x, y) -> askCompare(game, "blockers", labels, leaves, scores, x, y);
        int best = argmaxOfMins(candidates.size(), leaves, scores);
        pendingCompare = null;
        for (UUID[] pair : candidates.get(best)) {
            Permanent b = game.getPermanent(pair[0]);
            Permanent a = game.getPermanent(pair[1]);
            if (b != null && a != null && b.canBlock(a.getId(), game)) {
                getComputerPlayer().declareBlocker(defendingPlayerId,
                        pair[0], pair[1], game);
            }
        }
        traceLlmSearch("blockers", labels, leaves, scores, best, game);
    }

    /** Candidate value = min over its leaves; argmax over candidates. Uses
     *  LLM scores when present, the stored heuristics otherwise. */
    private int argmaxOfMins(int nCandidates, List<List<ScoredLeaf>> leaves,
                             double[] scores) {
        double[] v = candidateValues(nCandidates, leaves, scores, true);
        return pickBest(v, nCandidates, leaves, scores, true);
    }

    private void traceLlmSearch(String decision, List<String> labels,
                                List<List<ScoredLeaf>> leaves, double[] scores,
                                int chosen, Game game) {
        JsonObject rec = new JsonObject();
        rec.addProperty("mode", "llm_leaf");
        rec.addProperty("decision", decision);
        rec.addProperty("turn", game.getTurnNum());
        rec.addProperty("llm_scored", scores != null);
        rec.addProperty("chosen", labels.get(chosen));
        // Leak check, cumulative: every copy the search made so far, and how
        // many reseated an opponent hand identical to the real one. The
        // second should stay near zero; if it tracks the first, the
        // determinization is not doing anything.
        rec.addProperty("det_rollouts", detRollouts);
        rec.addProperty("det_seated_equals_real", detSeatedEqualsReal);
        // Arm (e) health: projection samples that threw and were dropped.
        // If this tracks det_rollouts, the projection is not running.
        rec.addProperty("project_turn_k", projectTurnK);
        rec.addProperty("proj_samples_failed", projSamplesFailed);
        // Arm (f): how many opponent response windows actually fired so far.
        rec.addProperty("respond_on", respondOn);
        rec.addProperty("resp_fired", projRespondFired);
        if (!projLastFailure.isEmpty()) {
            rec.addProperty("proj_last_failure", projLastFailure);
        }
        // Leaf value memo (DP): cumulative counts, plus this request's size.
        rec.addProperty("leaf_cache_on", LEAF_CACHE_ON);
        rec.addProperty("leaf_cache_full_hits", leafCacheFullHits);
        rec.addProperty("leaf_cache_leaves_saved", leafCacheLeavesSaved);
        rec.addProperty("leaf_dedup_saved", leafDedupSaved);
        rec.addProperty("leaves_total", leavesTotalLast);
        rec.addProperty("leaves_sent", leavesSentLast);
        // Resolution of this search: how many distinct scores the pilot
        // used, the aggregate per candidate, the top-two gap, and whether
        // the tie-break decided it.
        if (scores != null) {
            Set<Long> distinct = new HashSet<>();
            for (double x : scores) {
                distinct.add(Math.round(x * 10));
            }
            rec.addProperty("score_distinct", distinct.size());
        }
        JsonArray aggs = new JsonArray();
        for (double x : lastAggValues) {
            aggs.add(Double.isInfinite(x) ? null : Math.round(x * 100.0) / 100.0);
        }
        rec.add("agg_values", aggs);
        if (!Double.isNaN(lastAggGap)) {
            rec.addProperty("agg_gap", Math.round(lastAggGap * 100.0) / 100.0);
        }
        rec.addProperty("tie_break", lastTieBreak);
        rec.addProperty("tie_margin", TIE_MARGIN);
        rec.addProperty("tie_breaks_heuristic", tieBreaksHeuristic);
        rec.addProperty("tie_breaks_compare", tieBreaksCompare);
        // Sub-choice search: variants found / kept this search, the chosen
        // script, and how the real game replayed scripts so far.
        rec.addProperty("variants_discovered", variantsDiscoveredLast);
        rec.addProperty("variant_rows", variantRowsLast);
        rec.addProperty("chosen_script", chosenScriptLast);
        rec.addProperty("script_hits", scriptHits);
        rec.addProperty("script_misses", scriptMisses);
        rec.addProperty("script_skipped_library", scriptSkippedLibrary);
        rec.addProperty("reseat_self", RESEAT_SELF);
        rec.addProperty("self_reseated", selfReseated);
        JsonArray cands = new JsonArray();
        int flat = 0;
        for (int c = 0; c < labels.size(); c++) {
            JsonObject co = new JsonObject();
            co.addProperty("label", labels.get(c));
            JsonArray ls = new JsonArray();
            for (ScoredLeaf l : leaves.get(c)) {
                JsonObject lo = l.summary.deepCopy();
                lo.addProperty("heuristic", l.heuristic);
                if (scores != null) {
                    lo.addProperty("llm_score", scores[flat]);
                }
                flat++;
                ls.add(lo);
            }
            co.add("leaves", ls);
            cands.add(co);
        }
        rec.add("candidates", cands);
        appendTrace(rec);
        System.out.println("[CardGuru][llm-search] turn " + game.getTurnNum()
                + " " + decision + ": " + labels.size() + " candidates, chose '"
                + labels.get(chosen) + "' (" + (scores != null ? "LLM" : "heuristic fallback")
                + " leaves)");
    }

    /**
     * Search over the priority decision: pass, or activate each real ability.
     * Each candidate is rolled out on a simulation copy (sub-choices there
     * fall to the built-in AI via the `searching` guard), the resolved board
     * becomes a leaf, and the pilot scores every leaf in one leaf_eval.
     *
     * Returns 1 when it activated an ability, 0 when the pilot's own scores
     * chose to hold (the caller passes without asking again), and -1 when the
     * search could not run or got no scores (the caller escalates normally).
     *
     * A "hold" verdict is memoised on the shape of the decision, because the
     * engine re-offers the same window many times per turn — mirror game 2
     * searched "pass vs Cast Three Steps Ahead" sixteen separate times, since
     * that card's draw mode is legal at every priority. Re-asking an
     * unchanged question wastes a pilot call and cannot change the answer.
     */
    private final Map<String, Integer> priorityHoldMemo = new HashMap<>();

    /** Casts the engine offered but could not actually pay for.
     *
     * getPlayable() clears a Spree card on its BASE cost alone, so with one
     * land untapped "Cast Three Steps Ahead" ({U}, cheapest mode +{2}) is on
     * the menu for a spell that cannot be cast in any configuration.
     * activateAbility then asks the pilot for modes and targets, fails to
     * pay, and unwinds. Both the search and the escalation re-offered that
     * identical cast at every priority window: mirror game 3 burned 72 pilot
     * calls in one turn and never reached turn 5.
     *
     * Keyed on the mana actually available, not on the turn/step, because
     * the reason the cast failed is the mana — so the memo has to outlive
     * the step (the loop ran across all nine phases of the turn) and has to
     * lapse the moment a land or a rock changes what is payable. */
    private final Set<String> unaffordableMemo = new HashSet<>();

    /** Stable string for "what mana could I produce right now". */
    private String manaSignature(Game game) {
        try {
            return String.valueOf(getComputerPlayer().getManaAvailable(game));
        } catch (Exception e) {
            // Never let a signature failure break priority; an empty
            // signature just means nothing is memoised this window.
            return "?";
        }
    }

    /** Drop casts already known to be unpayable at this exact mana. */
    private List<ActivatedAbility> dropUnaffordable(List<ActivatedAbility> in,
                                                    String manaSig) {
        if (unaffordableMemo.isEmpty()) {
            return in;
        }
        List<ActivatedAbility> out = new ArrayList<>();
        for (ActivatedAbility a : in) {
            if (!unaffordableMemo.contains(manaSig + "|" + a)) {
                out.add(a);
            }
        }
        return out;
    }

    private String prioritySignature(Game game, List<ActivatedAbility> real) {
        UUID myId = this.getId();
        UUID oppId = null;
        for (UUID pid : game.getOpponents(myId)) {
            oppId = pid;
        }
        List<String> labels = new ArrayList<>();
        for (ActivatedAbility a : real) {
            labels.add(String.valueOf(a));
        }
        Collections.sort(labels);
        Player me = game.getPlayer(myId);
        Player opp = game.getPlayer(oppId);
        // Keyed on the POSITION, not the step: a "hold" decided at precombat
        // main is the same decision at begin combat, declare attackers, end
        // combat, postcombat main and end step as long as nothing changed.
        // 46 of 113 searches in the suite's two-hour game re-scored an
        // identical candidate set inside one turn for exactly this reason.
        // Any change to a permanent (new, tapped, counters), hand size,
        // life or stack invalidates it.
        List<String> perms = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents()) {
            perms.add((p.getControllerId().equals(myId) ? "A:" : "B:") + p.getName()
                    + (p.isTapped() ? "*" : "") + "#" + p.getCounters(game).getTotalCount()
                    + (p.isCreature(game) ? "/" + p.getPower().getValue()
                       + "/" + p.getToughness().getValue() : ""));
        }
        Collections.sort(perms);
        return game.getTurnNum() + "|" + game.getActivePlayerId().equals(myId) + "|"
                + (me == null ? 0 : me.getLife()) + "/"
                + (opp == null ? 0 : opp.getLife()) + "|"
                + (me == null ? 0 : me.getHand().size()) + "/"
                + (opp == null ? 0 : opp.getHand().size())
                + "|" + game.getStack().size()
                + "|" + manaSignature(game)
                + "|" + perms
                + "|" + labels;
    }

    private int llmSearchPriority(Game game, List<ActivatedAbility> real,
                                  String manaSig) {
        String sig = prioritySignature(game, real);
        if (priorityHoldMemo.containsKey(sig)) {
            return 0;   // already decided to hold this exact position
        }
        UUID myId = this.getId();
        UUID oppId = null;
        for (UUID pid : game.getOpponents(myId)) {
            oppId = pid;
        }
        // Rows: "pass", each ability with the AI's sub-choices, and each
        // ability's best sub-choice variants ("Cast Opt \u2192 scry: bottom Island").
        variantsDiscoveredLast = 0;
        List<Row> rows = new ArrayList<>(discoverRows(game, myId, oppId, null, "pass (hold everything)"));
        for (ActivatedAbility a : real) {
            rows.addAll(discoverRows(game, myId, oppId, a, String.valueOf(a)));
        }
        pruneExtraRows(rows, SUB_EXTRA_ROWS);
        variantRowsLast = 0;
        List<String> labels = new ArrayList<>();
        List<List<ScoredLeaf>> leaves = new ArrayList<>();
        for (Row r : rows) {
            if (!r.planned.isEmpty()) {
                variantRowsLast++;
            }
            labels.add(r.label);
            leaves.add(rolloutRow(game, myId, oppId, r));
        }

        double[] scores = askLeafScores(game, "priority", labels, leaves);
        if (scores == null) {
            // No LLM scores: leave the decision to the normal escalation
            // rather than acting on the heuristic alone.
            return -1;
        }
        pendingCompare = (x, y) -> askCompare(game, "priority", labels, leaves, scores, x, y);
        int best = argmaxProjected(labels.size(), leaves, scores);
        pendingCompare = null;
        Row picked = rows.get(best);
        chosenScriptLast = SubScript.describe(picked.planned);
        traceLlmSearch("priority", labels, leaves, scores, best, game);
        if (picked.ability == null) {
            priorityHoldMemo.put(sig, 1);
            return 0;
        }
        // The chosen variant's sub-choices are replayed at the real prompts
        // (targets during activation, scry / card picks at resolution).
        List<SubAnswer> replay = new ArrayList<>();
        for (SubAnswer a : picked.planned) {
            if (a.library) {
                scriptSkippedLibrary++;   // real prompt shows the real cards: pilot decides
            } else {
                replay.add(a);
            }
        }
        pendingScript = replay.isEmpty() ? null : new SubScript(null, myId, replay);
        pendingTurn = game.getTurnNum();
        if (getComputerPlayer().activateAbility(picked.ability.copy(), game)) {
            return 1;
        }
        pendingScript = null;
        // The cast unwound — the engine offered it but we cannot pay. Record
        // it so neither this window's escalation nor any later step in the
        // turn offers it again while the mana is unchanged, then fall through
        // to escalation so the pilot can still pick something else.
        unaffordableMemo.add(manaSig + "|" + picked.ability);
        return -1;
    }

    /** Append one decision record as a JSON line to spool/minimax.jsonl. */
    private void appendTrace(JsonObject record) {
        File log = new File(spool, "minimax.jsonl");
        try (FileWriter w = new FileWriter(log, true)) {
            w.write(GSON.toJson(record));
            w.write("\n");
        } catch (Exception e) {
            // A trace failure must never abort a real game; just note it.
            System.out.println("[CardGuru][minimax] trace write failed: " + e);
        }
    }
}


/**
 * Replay recorder: writes printing-exact game snapshots and the game log to
 * a JSONL file (-Dcardguru.record=path) for the replay studio. Independent
 * of the pilot protocol: one snapshot per driver request (stamped into the
 * request as snapshot_id) plus one per game-log line, deduplicated by state
 * hash. Reads engine objects directly; never mutates anything, and every
 * per-object block is guarded so recording can never break a game.
 * Simulation copies never reach it (they have no event listeners and
 * baseRequest checks isSimulation()).
 *
 * Record types (field "t"): meta, card (once per printing), snap, event, end.
 */
class GameRecorder {
    private static final Gson G = new Gson();
    private final BufferedWriter out;
    private final UUID aId;
    private final UUID bId;
    private final Set<String> cardsSeen = new HashSet<>();
    private final MessageDigest sha;
    private int nextId = 0;
    private int lastId = -1;
    private String lastHash = null;
    private int lastTurn = -1;
    private int eventSeq = 0;
    private int snapCount = 0;
    private int errors = 0;
    private boolean closed = false;

    GameRecorder(String path, UUID aId, UUID bId, JsonObject meta) throws IOException {
        this.out = new BufferedWriter(new FileWriter(path), 1 << 20);
        this.aId = aId;
        this.bId = bId;
        MessageDigest md;
        try {
            md = MessageDigest.getInstance("SHA-1");
        } catch (Exception e) {
            md = null;
        }
        this.sha = md;
        JsonObject m = new JsonObject();
        m.addProperty("t", "meta");
        m.addProperty("version", 1);
        m.addProperty("ts", System.currentTimeMillis() / 1000.0);
        for (Map.Entry<String, JsonElement> e : meta.entrySet()) {
            m.add(e.getKey(), e.getValue());
        }
        write(m);
    }

    // ---- public API -------------------------------------------------------

    /** Snapshot the live game; returns the snapshot id (reused when the
     *  state hash is unchanged and forceNew is false). */
    synchronized int snapshot(Game game, String trigger, boolean forceNew) {
        if (closed) {
            return lastId;
        }
        JsonObject body;
        try {
            body = body(game);
        } catch (RuntimeException e) {
            errors++;
            return lastId;
        }
        String json = G.toJson(body);
        String h = hash(json);
        if (!forceNew && lastId >= 0 && h.equals(lastHash)) {
            return lastId;
        }
        int id = nextId++;
        JsonObject line = new JsonObject();
        line.addProperty("t", "snap");
        line.addProperty("id", id);
        line.addProperty("trigger", trigger);
        for (Map.Entry<String, JsonElement> e : body.entrySet()) {
            line.add(e.getKey(), e.getValue());
        }
        write(line);
        lastHash = h;
        lastId = id;
        snapCount++;
        int turn = game.getTurnNum();
        if (forceNew || turn != lastTurn) {
            flush();
        }
        lastTurn = turn;
        return id;
    }

    /** A game-log line (TableEvent INFO/STATUS): snapshot-if-changed, then
     *  the event bound to that snapshot. */
    synchronized void event(Game game, String type, String message) {
        if (closed || message == null) {
            return;
        }
        int id = snapshot(game, "event", false);
        JsonObject e = new JsonObject();
        e.addProperty("t", "event");
        e.addProperty("snap", id);
        e.addProperty("n", eventSeq++);
        e.addProperty("turn", game.getTurnNum());
        PhaseStep ps = game.getTurnStepType();
        e.addProperty("step", ps == null ? "-" : ps.getStepShortText());
        e.addProperty("type", type);
        e.addProperty("text", strip(message));
        if (message.indexOf('<') >= 0) {
            e.addProperty("html", message);
        }
        write(e);
    }

    synchronized void noteError(Throwable t) {
        errors++;
    }

    synchronized void end(Game game, JsonObject result) {
        if (closed) {
            return;
        }
        try {
            if (game != null) {
                snapshot(game, "end", true);
            }
        } catch (RuntimeException ignored) {
            errors++;
        }
        JsonObject e = new JsonObject();
        e.addProperty("t", "end");
        e.add("result", result == null ? new JsonObject() : result.deepCopy());
        e.addProperty("snapshots", snapCount);
        e.addProperty("events", eventSeq);
        e.addProperty("errors", errors);
        write(e);
        try {
            out.flush();
            out.close();
        } catch (IOException ignored) {
        }
        closed = true;
    }

    // ---- serialization ----------------------------------------------------

    private JsonObject body(Game game) {
        JsonObject b = new JsonObject();
        b.addProperty("turn", game.getTurnNum());
        PhaseStep ps = game.getTurnStepType();
        b.addProperty("phase", ps == null ? "-" : ps.name());
        b.addProperty("step", ps == null ? "-" : ps.getStepShortText());
        b.addProperty("active", side(game.getActivePlayerId()));
        b.addProperty("priority", side(game.getPriorityPlayerId()));
        JsonObject players = new JsonObject();
        for (UUID pid : game.getPlayerList()) {
            Player p = game.getPlayer(pid);
            if (p == null) {
                continue;
            }
            try {
                players.add(side(pid), player(p, pid, game));
            } catch (RuntimeException e) {
                errors++;
            }
        }
        b.add("players", players);
        try {
            b.add("stack", stack(game));
        } catch (RuntimeException e) {
            errors++;
            b.add("stack", new JsonArray());
        }
        try {
            b.add("combat", combat(game));
        } catch (RuntimeException e) {
            errors++;
        }
        if (game.hasEnded()) {
            b.addProperty("ended", true);
        }
        return b;
    }

    private JsonObject player(Player p, UUID pid, Game game) {
        JsonObject s = new JsonObject();
        s.addProperty("life", p.getLife());
        s.addProperty("library", p.getLibrary().size());
        s.add("hand", refs(p.getHand().getCards(game), game));
        String pool = manaPool(p.getManaPool());
        if (!pool.isEmpty()) {
            s.addProperty("mana_pool", pool);
        }
        JsonObject ctr = counters(p.getCountersAsCopy());
        if (ctr.size() > 0) {
            s.add("counters", ctr);
        }
        JsonArray bf = new JsonArray();
        for (Permanent perm : game.getBattlefield().getAllActivePermanents(pid)) {
            try {
                bf.add(permanent(perm, game));
            } catch (RuntimeException e) {
                errors++;
            }
        }
        s.add("battlefield", bf);
        s.add("graveyard", refs(p.getGraveyard().getCards(game), game));
        try {
            s.add("exile", refs(game.getExile().getCardsOwned(game, pid), game));
        } catch (RuntimeException e) {
            errors++;
        }
        return s;
    }

    private JsonObject permanent(Permanent perm, Game game) {
        JsonObject o = ref(perm, game);
        if (perm.isTapped()) {
            o.addProperty("tapped", true);
        }
        if (perm.hasSummoningSickness()) {
            o.addProperty("sick", true);
        }
        if (perm.isCreature(game)) {
            o.addProperty("power", perm.getPower().getValue());
            o.addProperty("toughness", perm.getToughness().getValue());
        }
        if (perm.getDamage() > 0) {
            o.addProperty("damage", perm.getDamage());
        }
        mage.counters.Counters cs = perm.getCounters(game);
        if (perm.isPlaneswalker(game)) {
            o.addProperty("loyalty", cs.getCount(CounterType.LOYALTY));
        }
        JsonObject ctr = counters(cs);
        if (ctr.size() > 0) {
            o.add("counters", ctr);
        }
        if (perm.getAttachedTo() != null) {
            o.addProperty("attached_to", shortId(perm.getAttachedTo()));
        }
        if (perm.getAttachments() != null && !perm.getAttachments().isEmpty()) {
            JsonArray a = new JsonArray();
            for (UUID u : perm.getAttachments()) {
                a.add(shortId(u));
            }
            o.add("attachments", a);
        }
        mage.game.combat.Combat combat = game.getCombat();
        if (combat != null) {
            if (combat.getAttackers().contains(perm.getId())) {
                o.addProperty("attacking", true);
            }
            JsonArray blocking = new JsonArray();
            for (CombatGroup g : combat.getGroups()) {
                if (g.getBlockers().contains(perm.getId())) {
                    for (UUID aid : g.getAttackers()) {
                        blocking.add(shortId(aid));
                    }
                }
            }
            if (blocking.size() > 0) {
                o.add("blocking", blocking);
            }
        }
        if (perm.isFaceDown(game)) {
            o.addProperty("face_down", true);
        }
        if (perm instanceof PermanentToken) {
            o.addProperty("token", true);
        }
        if (perm.isTransformed()) {
            o.addProperty("transformed", true);
        }
        if (perm.isFlipped()) {
            o.addProperty("flipped", true);
        }
        if (perm.isCopy() && perm.getCopyFrom() != null) {
            o.addProperty("copy_of", perm.getCopyFrom().getName());
        }
        o.add("types", strArray(perm.getCardType(game)));
        List<String> now = perm.getRules(game);
        List<String> base = perm.getRules();
        if (now != null && !now.equals(base)) {
            o.addProperty("rules_now", String.join(" ; ", now));
        }
        return o;
    }

    private JsonArray stack(Game game) {
        List<StackObject> items = new ArrayList<>();
        for (StackObject so : game.getStack()) {
            items.add(so);          // ArrayDeque iteration: top first
        }
        Collections.reverse(items); // write bottom -> top
        JsonArray arr = new JsonArray();
        for (StackObject so : items) {
            JsonObject o = new JsonObject();
            try {
                o.addProperty("id", shortId(so.getId()));
                o.addProperty("name", so.getName());
                o.addProperty("controller", side(so.getControllerId()));
                if (so.getSourceId() != null) {
                    o.addProperty("source_id", shortId(so.getSourceId()));
                }
                try {
                    o.addProperty("mana_cost", so.getManaCost().getText());
                } catch (RuntimeException ignored) {
                }
                try {
                    o.add("types", strArray(so.getCardType(game)));
                } catch (RuntimeException ignored) {
                }
                List<Target> targets = new ArrayList<>();
                if (so instanceof Spell) {
                    Spell s = (Spell) so;
                    o.addProperty("ability", false);
                    Card c = s.getCard();
                    if (c != null) {
                        o.addProperty("key", keyOf(c, game));
                    }
                    o.addProperty("rules", String.join(" ; ", s.getRules(game)));
                    if (s.isCopy()) {
                        o.addProperty("copy", true);
                    }
                    if (s.isFaceDown(game)) {
                        o.addProperty("face_down", true);
                    }
                    for (mage.abilities.SpellAbility sa : s.getSpellAbilities()) {
                        targets.addAll(sa.getAllSelectedTargets());
                    }
                } else if (so instanceof StackAbility) {
                    StackAbility a = (StackAbility) so;
                    o.addProperty("ability", true);
                    MageObject src = game.getObject(a.getSourceId());
                    String srcName = src == null ? so.getName() : src.getName();
                    o.addProperty("source_name", srcName);
                    if (src != null) {
                        o.addProperty("key", keyOf(src, game));
                    }
                    String rule;
                    try {
                        rule = a.getRule(srcName);
                    } catch (RuntimeException e) {
                        rule = a.getRule();
                    }
                    o.addProperty("rules", rule);
                    if (a.isCopy()) {
                        o.addProperty("copy", true);
                    }
                    targets.addAll(a.getAllSelectedTargets());
                } else {
                    o.addProperty("ability", true);
                }
                JsonArray ta = new JsonArray();
                for (Target t : targets) {
                    for (UUID u : t.getTargets()) {
                        ta.add(targetRef(u, game));
                    }
                }
                o.add("targets", ta);
            } catch (RuntimeException e) {
                errors++;
            }
            arr.add(o);
        }
        return arr;
    }

    private JsonObject targetRef(UUID u, Game game) {
        JsonObject t = new JsonObject();
        t.addProperty("id", shortId(u));
        Player pl = game.getPlayer(u);
        if (pl != null) {
            t.addProperty("kind", "player");
            t.addProperty("name", side(u));
            return t;
        }
        Permanent perm = game.getPermanent(u);
        if (perm != null) {
            t.addProperty("kind", "permanent");
            t.addProperty("name", perm.getName());
            return t;
        }
        StackObject so = game.getStack().getStackObject(u);
        if (so != null) {
            t.addProperty("kind", "stack");
            t.addProperty("name", so.getName());
            return t;
        }
        MageObject o = game.getObject(u);
        if (o == null) {
            o = game.getCard(u);
        }
        t.addProperty("kind", "card");
        t.addProperty("name", o == null ? "?" : o.getName());
        return t;
    }

    private JsonArray combat(Game game) {
        JsonArray arr = new JsonArray();
        mage.game.combat.Combat combat = game.getCombat();
        if (combat == null) {
            return arr;
        }
        for (CombatGroup g : combat.getGroups()) {
            JsonObject o = new JsonObject();
            JsonArray at = new JsonArray();
            for (UUID u : g.getAttackers()) {
                at.add(shortId(u));
            }
            JsonArray bl = new JsonArray();
            for (UUID u : g.getBlockers()) {
                bl.add(shortId(u));
            }
            o.add("attackers", at);
            o.add("blockers", bl);
            o.addProperty("defender", side(g.getDefendingPlayerId()));
            if (g.isDefenderIsPermanent() && g.getDefenderId() != null) {
                o.addProperty("defender_id", shortId(g.getDefenderId()));
            }
            arr.add(o);
        }
        return arr;
    }

    // ---- cards --------------------------------------------------------------

    private JsonArray refs(Iterable<? extends Card> cards, Game game) {
        JsonArray a = new JsonArray();
        for (Card c : cards) {
            try {
                a.add(ref(c, game));
            } catch (RuntimeException e) {
                errors++;
            }
        }
        return a;
    }

    private JsonObject ref(MageObject o, Game game) {
        JsonObject r = new JsonObject();
        r.addProperty("id", shortId(o.getId()));
        r.addProperty("key", keyOf(o, game));
        r.addProperty("name", o.getName());
        return r;
    }

    /** Printing key ("SET/NUM", or "T/SET/Name" for tokens); emits the card
     *  record the first time a key is seen. */
    private String keyOf(MageObject o, Game game) {
        boolean token = (o instanceof PermanentToken)
                || (o instanceof mage.game.permanent.token.Token);
        String set = o.getExpansionSetCode();
        String num = o.getCardNumber();
        String key;
        if (token || num == null || num.isEmpty() || "0".equals(num)) {
            key = "T/" + (set == null || set.isEmpty() ? "-" : set) + "/" + o.getName();
            token = true;
        } else {
            key = set + "/" + num;
        }
        if (cardsSeen.add(key)) {
            try {
                write(cardRecord(o, game, key, token));
            } catch (RuntimeException e) {
                errors++;
            }
        }
        return key;
    }

    private JsonObject cardRecord(MageObject o, Game game, String key, boolean token) {
        JsonObject c = new JsonObject();
        c.addProperty("t", "card");
        c.addProperty("key", key);
        c.addProperty("name", o.getName());
        c.addProperty("set", o.getExpansionSetCode());
        c.addProperty("number", o.getCardNumber());
        String imgFile = o.getImageFileName();
        if (imgFile != null && !imgFile.isEmpty()) {
            c.addProperty("image_file", imgFile);
        }
        Integer imgNum = o.getImageNumber();
        if (imgNum != null && imgNum != 0) {
            c.addProperty("image_number", imgNum);
        }
        if (o.getUsesVariousArt()) {
            c.addProperty("various_art", true);
        }
        if (token) {
            c.addProperty("token", true);
        }
        try {
            c.addProperty("mana_cost", o.getManaCost().getText());
        } catch (RuntimeException ignored) {
        }
        JsonArray sup = strArray(o.getSuperType(game));
        JsonArray typ = strArray(o.getCardType(game));
        JsonArray sub = strArray(o.getSubtype(game));
        c.add("supertypes", sup);
        c.add("types", typ);
        c.add("subtypes", sub);
        StringBuilder tl = new StringBuilder();
        for (JsonElement e : sup) {
            tl.append(e.getAsString()).append(' ');
        }
        for (JsonElement e : typ) {
            tl.append(e.getAsString()).append(' ');
        }
        String types = tl.toString().trim();
        if (sub.size() > 0) {
            StringBuilder sb = new StringBuilder();
            for (JsonElement e : sub) {
                sb.append(sb.length() > 0 ? " " : "").append(e.getAsString());
            }
            types = types + " — " + sb;
        }
        c.addProperty("type_line", types);
        try {
            c.addProperty("color", o.getColor(game).toString());
        } catch (RuntimeException ignored) {
        }
        List<String> rules = null;
        if (o instanceof Card) {
            rules = ((Card) o).getRules();
        }
        if (rules == null && o instanceof Spell) {
            rules = ((Spell) o).getRules(game);
        }
        c.add("rules", rules == null ? new JsonArray() : strArray(rules));
        if (o.isCreature(game)) {
            c.addProperty("power", o.getPower().getValue());
            c.addProperty("toughness", o.getToughness().getValue());
        }
        if (o.isPlaneswalker(game)) {
            c.addProperty("loyalty", o.getStartingLoyalty());
        }
        if (o instanceof Card) {
            Card back = ((Card) o).getSecondCardFace();
            if (back != null && back != o) {
                JsonObject b = new JsonObject();
                b.addProperty("name", back.getName());
                b.addProperty("set", back.getExpansionSetCode());
                b.addProperty("number", back.getCardNumber());
                c.add("back", b);
            }
        }
        return c;
    }

    // ---- helpers ------------------------------------------------------------

    private String side(UUID id) {
        return id == null ? "-" : id.equals(aId) ? "A" : id.equals(bId) ? "B" : "?";
    }

    private static String shortId(UUID u) {
        return u == null ? null : u.toString().substring(0, 8);
    }

    private static JsonArray strArray(java.util.Collection<?> items) {
        JsonArray a = new JsonArray();
        if (items != null) {
            for (Object x : items) {
                a.add(String.valueOf(x));
            }
        }
        return a;
    }

    private static JsonObject counters(mage.counters.Counters cs) {
        JsonObject o = new JsonObject();
        if (cs != null) {
            for (Counter c : cs.values()) {
                if (c.getCount() != 0) {
                    o.addProperty(c.getName(), c.getCount());
                }
            }
        }
        return o;
    }

    private static String manaPool(ManaPool mp) {
        if (mp == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        rep(sb, 'W', mp.getWhite());
        rep(sb, 'U', mp.getBlue());
        rep(sb, 'B', mp.getBlack());
        rep(sb, 'R', mp.getRed());
        rep(sb, 'G', mp.getGreen());
        rep(sb, 'C', mp.getColorless());
        return sb.toString();
    }

    private static void rep(StringBuilder sb, char c, int n) {
        for (int i = 0; i < n; i++) {
            sb.append(c);
        }
    }

    private static String strip(String html) {
        return html.replaceAll("<[^>]+>", "").replaceAll("\\s+", " ").trim();
    }

    private String hash(String s) {
        if (sha == null) {
            return Integer.toHexString(s.hashCode()) + ":" + s.length();
        }
        sha.reset();
        byte[] d = sha.digest(s.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        for (byte b : d) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private void write(JsonObject o) {
        try {
            out.write(G.toJson(o));
            out.write('\n');
        } catch (IOException e) {
            errors++;
        }
    }

    private void flush() {
        try {
            out.flush();
        } catch (IOException ignored) {
        }
    }
}


/** One sub-choice prompt as a menu with stable option keys. */
final class SubMenu {
    final String kind;          // target | choose | use | mode | x | choice
    final String prompt;
    final int min;
    final int max;
    final List<String> keys = new ArrayList<>();
    final List<String> texts = new ArrayList<>();
    List<String> chosen = new ArrayList<>();   // keys the answer selected ("yes"/"no", "x=N")
    int chosenX = 0;
    boolean library = false;                   // pile of (reseated) library cards

    SubMenu(String kind, String prompt, int min, int max) {
        this.kind = kind;
        this.prompt = prompt == null ? "" : prompt;
        this.min = min;
        this.max = max;
    }

    static SubMenu use(String prompt) {
        SubMenu m = new SubMenu("use", prompt, 1, 1);
        m.keys.add("yes");
        m.keys.add("no");
        m.texts.add("yes");
        m.texts.add("no");
        return m;
    }

    static SubMenu x(String prompt, int min, int max) {
        return new SubMenu("x", prompt, min, max);
    }

    /** Identity across a simulation copy and the real game: kind, the
     *  prompt without volatile bits, and the option keys (order-free). */
    String key() {
        String p = prompt.replaceAll("\\(selected[^)]*\\)", "").replaceAll("\\(life \\d+\\)", "")
                .replaceAll("\\s+", " ").trim();
        List<String> ks = new ArrayList<>(keys);
        Collections.sort(ks);
        return kind + "|" + p + "|" + ks + (kind.equals("x") ? "|" + min + "-" + max : "");
    }

    boolean chosenBool() {
        return chosen.contains("yes");
    }

    private String textOf(String key) {
        int i = keys.indexOf(key);
        return (library ? "~" : "") + (i >= 0 ? texts.get(i) : key);   // ~ = sampled card
    }

    private String verb() {
        String p = prompt.toLowerCase();
        if (p.contains("scry") || p.contains("bottom")) {
            return "scry";
        }
        if (p.contains("surveil")) {
            return "surveil";
        }
        if (p.contains("discard")) {
            return "discard";
        }
        if (p.contains("exile")) {
            return "exile";
        }
        if (p.contains("sacrifice")) {
            return "sacrifice";
        }
        if (p.contains("hand")) {
            return "keep";
        }
        return kind.equals("target") ? "target" : "pick";
    }

    /** Human label for an answer (the tree's "→ …" text). */
    String label(List<String> ks) {
        switch (kind) {
            case "use": {
                String p = prompt.replaceAll("\\([^)]*\\)", "").replace("?", "")
                        .replaceAll("\\s+", " ").trim();
                if (p.length() > 30) {
                    p = p.substring(0, 29) + "\u2026";
                }
                // answer first: a truncated tree label still says yes or no
                return (ks.contains("yes") ? "yes" : "no") + " \u2014 " + p;
            }
            case "x":
                return ks.isEmpty() ? "X" : ks.get(0).replace("x=", "X=");
            case "mode":
            case "choice": {
                String t = ks.isEmpty() ? "?" : textOf(ks.get(0));
                return kind + ": " + (t.length() > 30 ? t.substring(0, 29) + "…" : t);
            }
            default: {
                String v = verb();
                if (ks.isEmpty()) {
                    return v.equals("scry") ? "scry: keep on top"
                            : v.equals("surveil") ? "surveil: keep on top" : v + ": none";
                }
                List<String> names = new ArrayList<>();
                for (String k : ks) {
                    names.add(textOf(k));
                }
                return v + (v.equals("scry") || v.equals("surveil") ? ": bottom " : ": ")
                        + String.join(", ", names);
            }
        }
    }

    /** Alternatives to the recorded answer, at most `limit`. */
    List<SubAnswer> alternatives(int limit) {
        List<SubAnswer> out = new ArrayList<>();
        try {
            return alternativesInner(limit, out);
        } finally {
            for (SubAnswer a : out) {
                a.library = library;
            }
        }
    }

    private List<SubAnswer> alternativesInner(int limit, List<SubAnswer> out) {
        String mk = key();
        switch (kind) {
            case "use": {
                boolean alt = !chosenBool();
                out.add(new SubAnswer(mk, Collections.singletonList(alt ? "yes" : "no"), alt, 0,
                        label(Collections.singletonList(alt ? "yes" : "no"))));
                break;
            }
            case "x": {
                for (int v : new int[]{min, max}) {
                    if (v != chosenX && out.size() < limit) {
                        List<String> ks = Collections.singletonList("x=" + v);
                        out.add(new SubAnswer(mk, ks, false, v, label(ks)));
                    }
                }
                break;
            }
            case "mode":
            case "choice": {
                for (String k : keys) {
                    if (!chosen.contains(k) && out.size() < limit) {
                        List<String> ks = Collections.singletonList(k);
                        out.add(new SubAnswer(mk, ks, false, 0, label(ks)));
                    }
                }
                break;
            }
            default: {
                if (max <= 1 || chosen.isEmpty()) {
                    for (String k : keys) {
                        if (!chosen.contains(k) && out.size() < limit) {
                            List<String> ks = Collections.singletonList(k);
                            out.add(new SubAnswer(mk, ks, false, 0, label(ks)));
                        }
                    }
                } else {
                    // multi-select: swap the last chosen card for each unchosen one
                    for (String k : keys) {
                        if (!chosen.contains(k) && out.size() < limit) {
                            List<String> ks = new ArrayList<>(chosen.subList(0, chosen.size() - 1));
                            ks.add(k);
                            out.add(new SubAnswer(mk, ks, false, 0, label(ks)));
                        }
                    }
                }
                if (min == 0 && !chosen.isEmpty() && out.size() < limit + 1) {
                    List<String> none = new ArrayList<>();
                    out.add(new SubAnswer(mk, none, false, 0, label(none)));
                }
            }
        }
        return out;
    }

    SubAnswer asAnswer() {
        SubAnswer a = new SubAnswer(key(), new ArrayList<>(chosen), chosenBool(), chosenX, label(chosen));
        a.library = library;
        return a;
    }
}

/** A planned answer to one menu. */
final class SubAnswer {
    final String menuKey;
    final List<String> keys;
    final boolean bool;
    final int x;
    final String label;
    boolean library = false;

    SubAnswer(String menuKey, List<String> keys, boolean bool, int x, String label) {
        this.menuKey = menuKey;
        this.keys = keys;
        this.bool = bool;
        this.x = x;
        this.label = label;
    }
}

/** The sub-choice script of one rollout (or the pending real-game script):
 *  planned answers in order, the menus met, and how many planned answers
 *  did not match the menu they were meant for. */
final class SubScript {
    /** The script consulted by simulation copies of the driven player. */
    static SubScript ACTIVE = null;

    final Game boundTo;         // the copy this script belongs to (null for the real game)
    final UUID playerId;
    final List<SubAnswer> planned;
    final List<SubMenu> recorded = new ArrayList<>();
    int cursor = 0;
    int misses = 0;

    SubScript(Game boundTo, UUID playerId, List<SubAnswer> planned) {
        this.boundTo = boundTo;
        this.playerId = playerId;
        this.planned = planned == null ? new ArrayList<SubAnswer>() : planned;
    }

    /** The planned answer for the menu at the current position, or null
     *  (no plan for this position, or the plan does not match the menu). */
    SubAnswer next(SubMenu m) {
        int pos = cursor++;
        if (pos >= planned.size()) {
            return null;
        }
        SubAnswer a = planned.get(pos);
        if (a.menuKey.equals(m.key())) {
            return a;
        }
        misses++;
        return null;
    }

    void record(SubMenu m) {
        recorded.add(m);
    }

    /** Labels of the planned answers; a prompt the engine repeats (kicker
     *  is asked at activation and at payment) is shown once. */
    static String describe(List<SubAnswer> planned) {
        List<String> ls = new ArrayList<>();
        for (SubAnswer a : planned) {
            if (ls.isEmpty() || !ls.get(ls.size() - 1).equals(a.label)) {
                ls.add(a.label);
            }
        }
        return String.join("; ", ls);
    }
}
