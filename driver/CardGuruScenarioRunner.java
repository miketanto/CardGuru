package org.mage.test.serverside;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.Arrays;

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
        } catch (Throwable e) {   // AssertionError (strict mode) or engine exception
            out.addProperty("status", "error");
            out.addProperty("error", e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        out.addProperty("millis", System.currentTimeMillis() - t0);
        return out;
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
                    castSpell(a.get("turn").getAsInt(), phase(a),
                            player(a.get("player").getAsString()),
                            a.get("card").getAsString());
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
                    addTarget(player(a.get("player").getAsString()),
                            a.get("value").getAsString());
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
