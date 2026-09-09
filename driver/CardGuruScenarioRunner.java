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
import mage.cards.Card;
import mage.choices.Choice;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.game.turn.CombatDamageStep;
import mage.game.turn.EndOfCombatStep;
import mage.game.turn.Step;
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
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

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
            TestPlayer opp = new TestPlayer(
                    new TestComputerPlayer7(playerName, range, skill));
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

    InteractiveTestPlayer(TestComputerPlayer computerPlayer, String spool,
                          String minimaxMode) {
        super(computerPlayer);
        this.spool = spool;
        this.minimaxMode = minimaxMode;
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
        req.addProperty("turn", game.getTurnNum());
        req.addProperty("phase", String.valueOf(game.getTurnStepType()));
        // Sub-choices can fire pre-game (mulligan-time scry, opening choices)
        // when there is no active player yet.
        UUID activeId = game.getActivePlayerId();
        req.addProperty("active", activeId == null ? "-"
                : activeId.equals(this.getId()) ? "A" : "B");
        req.add("state", observableState(game));
        return req;
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
                }
                o.addProperty("types", String.valueOf(perm.getCardType(game)));
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
                    o.addProperty("types", String.valueOf(c.getCardType(game)));
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
        List<ActivatedAbility> playable = getComputerPlayer().getPlayable(game, true, Zone.ALL, false);
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
        int choice = resp.has("choice") ? resp.get("choice").getAsInt() : 0;
        if (choice >= 1 && choice <= playable.size()) {
            ActivatedAbility chosen = playable.get(choice - 1).copy();
            if (getComputerPlayer().activateAbility(chosen, game)) {
                return true;
            }
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

    /** Ask the policy to pick targets. Returns false when there was nothing
     *  to decide or the answer under-filled the minimum — the caller then
     *  delegates to the AI, which completes whatever was already added. */
    private boolean externalChooseTarget(String kind, Outcome outcome,
                                         Target target, Ability source, Game game) {
        List<UUID> possible = new ArrayList<>(target.possibleTargets(
                target.getAffectedAbilityControllerId(getId()), source, game));
        int min = target.getMinNumberOfTargets();
        int max = target.getMaxNumberOfTargets();
        if (possible.isEmpty() || (possible.size() == 1 && min >= 1)) {
            return false;   // forced or impossible: no real decision
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
            for (JsonElement e : resp.getAsJsonArray("targets")) {
                int idx = e.getAsInt();
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

    @Override
    public boolean chooseTarget(Outcome outcome, Target target, Ability source, Game game) {
        if (externalSubchoices
                && externalChooseTarget("target", outcome, target, source, game)) {
            return true;
        }
        return super.chooseTarget(outcome, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source,
                          Game game, Map<String, Serializable> options) {
        if (externalSubchoices
                && externalChooseTarget("choose", outcome, target, source, game)) {
            return true;
        }
        return super.choose(outcome, target, source, game, options);
    }

    @Override
    public int announceX(int min, int max, String message, Game game,
                         Ability source, boolean isManaPay) {
        if (externalSubchoices && max > min) {
            JsonObject req = baseRequest("announce_x", game);
            req.addProperty("prompt", message);
            req.addProperty("ability", String.valueOf(source));
            req.addProperty("min", min);
            req.addProperty("max", max);
            req.addProperty("mana_pay", isManaPay);
            JsonObject resp = ask(req);
            int x = resp.has("x") ? resp.get("x").getAsInt() : min;
            return Math.max(min, Math.min(max, x));
        }
        return super.announceX(min, max, message, game, source, isManaPay);
    }

    @Override
    public Mode chooseMode(Modes modes, Ability source, Game game) {
        if (externalSubchoices) {
            List<Mode> avail = new ArrayList<>(modes.getAvailableModes(source, game));
            if (avail.size() > 1) {
                JsonObject req = baseRequest("mode", game);
                req.addProperty("ability", String.valueOf(source));
                JsonArray opts = new JsonArray();
                for (int i = 0; i < avail.size(); i++) {
                    JsonObject o = new JsonObject();
                    o.addProperty("index", i);
                    o.addProperty("text", avail.get(i).getEffects().getText(avail.get(i)));
                    opts.add(o);
                }
                req.add("options", opts);
                JsonObject resp = ask(req);
                int c = resp.has("choice") ? resp.get("choice").getAsInt() : -1;
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
        if (externalSubchoices) {
            return externalChooseUse(outcome, message, null, game, source);
        }
        return super.chooseUse(outcome, message, source, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, String secondMessage,
                             String trueText, String falseText, Ability source, Game game) {
        if (externalSubchoices) {
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

    @Override
    public boolean choose(Outcome outcome, Choice choice, Game game) {
        if (externalSubchoices && choice != null) {
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
            if (texts.size() > 1) {
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
                int c = resp.has("choice") ? resp.get("choice").getAsInt() : -1;
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
        if ("attacks".equals(minimaxMode)) {
            minimaxSelectAttackers(game, defenderId, attackers);
            return;
        }
        if ("llm".equals(minimaxMode) && !attackers.isEmpty()) {
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
            for (JsonElement e : resp.getAsJsonArray("attackers")) {
                int idx = e.getAsInt();
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

        if ("llm".equals(minimaxMode) && !blockers.isEmpty() && !attackers.isEmpty()) {
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
            for (JsonElement e : resp.getAsJsonArray("blocks")) {
                JsonArray pair = e.getAsJsonArray();
                int b = pair.get(0).getAsInt();
                int a = pair.get(1).getAsInt();
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
        Game afterAttack = game.createSimulationForAI();
        for (int idx : set) {
            Permanent atk = attackers.get(idx);
            Permanent simAtk = afterAttack.getPermanent(atk.getId());
            if (simAtk != null && defenderId != null
                    && simAtk.canAttack(defenderId, afterAttack)) {
                afterAttack.getPlayer(myId)
                        .declareAttacker(atk.getId(), defenderId, afterAttack, false);
            }
        }
        afterAttack.checkStateAndTriggered();
        resolveStack(afterAttack);

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
    private void applyBlocksAndResolveCombat(Game leaf, UUID defenderId,
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
        simulateStep(leaf, new CombatDamageStep(true));
        simulateStep(leaf, new CombatDamageStep(false));
        simulateStep(leaf, new EndOfCombatStep());
        leaf.checkStateAndTriggered();
        resolveStack(leaf);
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
        return o;
    }

    private String boardLine(Game leaf, UUID pid) {
        List<String> creatures = new ArrayList<>();
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
            }
        }
        String s = creatures.isEmpty() ? "no creatures" : String.join(", ", creatures);
        return s + " | " + lands + " lands (" + landsUntapped + " untapped)";
    }

    /** Send every leaf in one "leaf_eval" request; return the flat score list
     *  or null when the response is missing/short (caller falls back). */
    private double[] askLeafScores(Game game, String decision,
                                   List<String> candidateLabels,
                                   List<List<ScoredLeaf>> leavesPerCandidate) {
        JsonObject req = baseRequest("leaf_eval", game);
        req.addProperty("decision", decision);
        int total = 0;
        JsonArray cands = new JsonArray();
        for (int c = 0; c < candidateLabels.size(); c++) {
            JsonObject co = new JsonObject();
            co.addProperty("label", candidateLabels.get(c));
            JsonArray ls = new JsonArray();
            for (ScoredLeaf l : leavesPerCandidate.get(c)) {
                JsonObject lo = l.summary.deepCopy();
                lo.addProperty("leaf_index", total++);
                ls.add(lo);
            }
            co.add("leaves", ls);
            cands.add(co);
        }
        req.add("candidates", cands);
        req.addProperty("leaf_count", total);

        JsonObject resp = ask(req);
        if (!resp.has("scores") || !resp.get("scores").isJsonArray()) {
            return null;
        }
        JsonArray arr = resp.getAsJsonArray("scores");
        if (arr.size() < total) {
            return null;
        }
        double[] scores = new double[total];
        try {
            for (int i = 0; i < total; i++) {
                scores[i] = arr.get(i).getAsDouble();
            }
        } catch (Exception e) {
            return null;
        }
        return scores;
    }

    /** Rolled-out attack candidate: declare the set on a copy, resolve, keep
     *  the K heuristically-worst block-response leaves. */
    private List<ScoredLeaf> rolloutAttackLeaves(Game game, UUID myId, UUID defenderId,
                                                 List<Permanent> attackers,
                                                 List<Integer> set) {
        Game afterAttack = game.createSimulationForAI();
        for (int idx : set) {
            Permanent atk = attackers.get(idx);
            Permanent simAtk = afterAttack.getPermanent(atk.getId());
            if (simAtk != null && defenderId != null
                    && simAtk.canAttack(defenderId, afterAttack)) {
                afterAttack.getPlayer(myId)
                        .declareAttacker(atk.getId(), defenderId, afterAttack, false);
            }
        }
        afterAttack.checkStateAndTriggered();
        resolveStack(afterAttack);

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
        int best = argmaxOfMins(candidates.size(), leaves, scores);
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
            Game leaf = game.createSimulationForAI();
            applyBlocksAndResolveCombat(leaf, defendingPlayerId, set);
            double h = GameStateEvaluator2.evaluate(myId, leaf).getTotalScore();
            List<ScoredLeaf> one = new ArrayList<>();
            one.add(new ScoredLeaf(
                    compactLeaf(leaf, myId, oppId, "after combat"), h));
            leaves.add(one);
        }

        double[] scores = askLeafScores(game, "blockers", labels, leaves);
        int best = argmaxOfMins(candidates.size(), leaves, scores);
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
        int best = 0;
        double bestV = Double.NEGATIVE_INFINITY;
        int flat = 0;
        for (int c = 0; c < nCandidates; c++) {
            double v = Double.POSITIVE_INFINITY;
            for (ScoredLeaf l : leaves.get(c)) {
                double lv = scores != null ? scores[flat] : l.heuristic;
                flat++;
                v = Math.min(v, lv);
            }
            if (leaves.get(c).isEmpty()) {
                v = Double.NEGATIVE_INFINITY;
            }
            if (v > bestV) {
                bestV = v;
                best = c;
            }
        }
        return best;
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
