package org.mage.test.serverside;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
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
        // playerA is already an InteractiveTestPlayer (see createNewPlayer,
        // which reads the same system property during @Before setup).
        playerB.setAIPlayer(true);   // real built-in AI opponent
        // Run to the natural end of the game rather than a scripted stop.
        setStopAt(200, PhaseStep.UNTAP);
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
            execute();
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
    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence range) {
        String spool = System.getProperty("cardguru.interactive.spool");
        if (spool != null && playerName.equals("PlayerA")) {
            return new InteractiveTestPlayer(new TestComputerPlayer(playerName, range), spool);
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
    private static final long DECISION_TIMEOUT_MS = 120_000;

    private final String spool;
    private int seq = 0;

    InteractiveTestPlayer(TestComputerPlayer computerPlayer, String spool) {
        super(computerPlayer);
        this.spool = spool;
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
        req.addProperty("active", game.getActivePlayerId().equals(this.getId()) ? "A" : "B");
        req.add("state", observableState(game));
        return req;
    }

    /** Both players' public state, plus this (driven) player's own hand. */
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
                    hand.add(c.getName());
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
}
