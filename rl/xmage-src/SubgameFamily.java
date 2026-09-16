package org.mage.test.benchmark.rl;

import mage.abilities.Ability;
import mage.abilities.SpellAbility;
import mage.cards.Card;
import mage.cards.repository.CardCriteria;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import mage.constants.CardType;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

/**
 * GENERATE - SOLVE - FILTER for a tier-1 subgame family.
 *
 * rl/SUBGAME-DESIGN.md closes with the reason this file exists: "an
 * instance is not a design, it is a search result". T1.HOLD as authored
 * is one board that happened to survive an exact solve; a family is what
 * you get when boards are drawn from a stated parameter range, every one
 * is solved exactly, and only the ones meeting pre-registered criteria
 * are kept.
 *
 * Modes:
 *   pool &lt;setCodes&gt;        engine-verified vanilla creatures - abilities
 *                          are SpellAbility and nothing else, P/T are
 *                          literal integers, no supertypes. Printed as
 *                          POOL rows for a checked-in pool file, so no
 *                          card in a family is ever taken on trust.
 *   gen &lt;poolFile&gt; &lt;seed&gt; &lt;n&gt; [shard] [shards]
 *                          draw n boards, solve each exactly, print one
 *                          INST row per board with its label.
 *   gate1 &lt;poolFile&gt; &lt;instFile&gt; &lt;delta&gt;
 *                          horizon insensitivity: re-solve each kept
 *                          instance with `delta` more filler on both
 *                          sides and report whether the optimal class
 *                          moved.
 *
 * THE UNIQUENESS GATE IS OVER SYMMETRY CLASSES, not over masks. Two
 * copies of the same vanilla body are interchangeable at the root, so
 * "attack with lion #1" and "attack with lion #2" are two masks denoting
 * one decision. Counting masks would fail uniqueness on every board with
 * a duplicate. Classes are the multiset of attacker NAMES.
 */
public final class SubgameFamily {

    // ------------------------------------------------------------- pool

    public static final class PoolCard {
        public final String name;
        public final int power;
        public final int toughness;
        PoolCard(String name, int power, int toughness) {
            this.name = name;
            this.power = power;
            this.toughness = toughness;
        }
    }

    /** Vanilla in the strict sense: the only ability the card has is the
     *  one that casts it. Rule-text emptiness is NOT enough - Hillcomber
     *  Giant has an empty graph vector in cards_v1 and mountainwalk in the
     *  engine (rl/SUBGAME-T1-BUILD.md). */
    private static boolean isVanilla(Card c) {
        for (Ability a : c.getAbilities()) {
            if (!(a instanceof SpellAbility)) {
                return false;
            }
        }
        return true;
    }

    private static boolean literalPT(Card c) {
        return c.getPower().toString().matches("\\d+")
                && c.getToughness().toString().matches("\\d+");
    }

    private static void poolMode(String[] args) {
        String[] sets = (args.length > 1 ? args[1] : "M10,M11,M12,M13,M14,M15")
                .split(",");
        CardCriteria crit = new CardCriteria().setCodes(sets).types(CardType.CREATURE);
        List<CardInfo> found = CardRepository.instance.findCards(crit);
        Map<String, PoolCard> byPT = new TreeMap<>();
        Set<String> seen = new TreeSet<>();
        int scanned = 0;
        for (CardInfo info : found) {
            if (!seen.add(info.getName())) {
                continue;
            }
            scanned++;
            Card c = info.createCard();
            if (c == null || !c.getSuperType().isEmpty()) {
                continue;
            }
            if (!literalPT(c) || !isVanilla(c)) {
                continue;
            }
            int p = c.getPower().getValue();
            int t = c.getToughness().getValue();
            if (p < 1 || p > 5 || t < 1 || t > 5) {
                continue;
            }
            String key = p + "/" + t;
            // one representative per P/T, alphabetically first, so the
            // pool is a function of the sets and not of scan order
            PoolCard prev = byPT.get(key);
            if (prev == null || c.getName().compareTo(prev.name) < 0) {
                byPT.put(key, new PoolCard(c.getName(), p, t));
            }
        }
        System.out.println("# vanilla pool from sets " + Arrays.toString(sets)
                + " - " + scanned + " distinct creature names scanned");
        for (Map.Entry<String, PoolCard> e : byPT.entrySet()) {
            PoolCard pc = e.getValue();
            System.out.println("POOL\t" + pc.name + "\t" + pc.power + "\t" + pc.toughness);
        }
    }

    public static Map<String, PoolCard> readPool(String path) throws Exception {
        Map<String, PoolCard> out = new LinkedHashMap<>();
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (!line.startsWith("POOL\t")) {
                    continue;
                }
                String[] f = line.split("\t");
                out.put(f[1], new PoolCard(f[1], Integer.parseInt(f[2]),
                        Integer.parseInt(f[3])));
            }
        }
        return out;
    }

    // ------------------------------------------------------- the board

    /** A generated board. Kept as data so a row in the family file
     *  reconstructs exactly the Spec that was solved. */
    public static final class Board {
        public String id;
        public int aLife, aFiller, bLife, bFiller;
        public List<String> aBodies = new ArrayList<>();
        public List<String> bBodies = new ArrayList<>();

        public SubgameRunner.Spec toSpec(int fillerDelta) {
            SubgameRunner.Spec s = new SubgameRunner.Spec();
            s.name = id;
            s.a.life = aLife;
            s.a.filler = aFiller + fillerDelta;
            for (String n : aBodies) {
                s.a.battlefield.add(SubgameRunner.Body.of(n, 1));
            }
            s.b.life = bLife;
            s.b.filler = bFiller + fillerDelta;
            for (String n : bBodies) {
                // a trailing '*' means the body is TAPPED: it cannot block
                // this turn but untaps and attacks on B's turn. Without
                // tapped defenders every admissible board is a hold - see
                // the SWING note in admissible().
                boolean tapped = n.endsWith("*");
                s.b.battlefield.add(SubgameRunner.Body.of(
                        tapped ? n.substring(0, n.length() - 1) : n, 1, tapped));
            }
            s.aOnPlay = true;
            return s;
        }

        public String fields() {
            return aLife + "\t" + aFiller + "\t" + String.join(";", aBodies)
                    + "\t" + bLife + "\t" + bFiller + "\t" + String.join(";", bBodies);
        }

        public static Board parse(String id, String[] f, int off) {
            Board b = new Board();
            b.id = id;
            b.aLife = Integer.parseInt(f[off]);
            b.aFiller = Integer.parseInt(f[off + 1]);
            b.aBodies = Arrays.asList(f[off + 2].split(";"));
            b.bLife = Integer.parseInt(f[off + 3]);
            b.bFiller = Integer.parseInt(f[off + 4]);
            b.bBodies = Arrays.asList(f[off + 5].split(";"));
            return b;
        }
    }

    /**
     * A stats-only admission test, applied BEFORE the solve.
     *
     * The first uniform draw (seed 11, ranges below) produced six boards
     * where every first action wins and two where none does - zero usable
     * instances in eight solves, at up to 90 s each. The reason is not
     * subtle: if one side is ahead on board and on life, the opening
     * attack cannot be the thing that decides the game, because A has
     * many later decisions to recover in. A first decision is only
     * load-bearing when it is irrecoverable.
     *
     * So both sides must be one swing from death:
     *   1. sum(B power) >= A life - an unanswered crack-back kills A, so
     *      attacking with everything is a real risk;
     *   2. sum(A power) >= B life - A's full swing is lethal if unblocked,
     *      so holding is a real cost.
     * Neither condition mentions the solver, and both are recorded here
     * rather than tuned after seeing labels.
     *
     * WHAT THIS ALONE CANNOT PRODUCE. Attacking taps the attacker, so on
     * a board where both sides are one swing from lethal and every body
     * is untapped, whoever swings first dies to the crack-back - every
     * instance is a hold, and the "never attack" baseline scores 1.000 on
     * the whole family. B's bodies are therefore tapped with probability
     * 0.4 (B just attacked), which is what lets an attacking answer be
     * correct on some boards. The tapped flag is part of the generator,
     * not a per-instance rescue.
     */
    static boolean admissible(Board b, Map<String, PoolCard> pool) {
        int aPower = 0, bPower = 0;
        for (String n : b.aBodies) {
            aPower += pool.get(bare(n)).power;
        }
        for (String n : b.bBodies) {
            // tapped or not: a tapped creature untaps before B's attack,
            // so it counts toward the crack-back
            bPower += pool.get(bare(n)).power;
        }
        return bPower >= b.aLife && aPower >= b.bLife;
    }

    /** Strip the tapped marker. */
    static String bare(String n) {
        return n.endsWith("*") ? n.substring(0, n.length() - 1) : n;
    }

    static boolean tapped(String n) {
        return n.endsWith("*");
    }

    /**
     * PRE-REGISTERED parameter ranges. Everything the concept does not
     * need is randomised (rl/SUBGAME-DESIGN.md "Randomising everything
     * the concept does not need"); the ranges are bounded by solve cost,
     * which triples per two extra filler cards and doubles per extra
     * attacker.
     */
    static Board draw(Random rnd, List<PoolCard> pool, int index) {
        Board b = new Board();
        b.id = "T1.GEN." + index;
        int na = 1 + rnd.nextInt(3);            // 1..3 attackers
        int nb = 1 + rnd.nextInt(2);            // 1..2 blockers
        for (int i = 0; i < na; i++) {
            b.aBodies.add(pool.get(rnd.nextInt(pool.size())).name);
        }
        for (int i = 0; i < nb; i++) {
            // 40% tapped: B just attacked, so it cannot block this turn.
            // This is the axis that makes an attacking answer possible at
            // all - see admissible().
            b.bBodies.add(pool.get(rnd.nextInt(pool.size())).name
                    + (rnd.nextInt(100) < 40 ? "*" : ""));
        }
        Collections.sort(b.aBodies);
        Collections.sort(b.bBodies);
        b.aLife = 1 + rnd.nextInt(8);           // 1..8
        b.bLife = 1 + rnd.nextInt(8);
        b.aFiller = 3 + rnd.nextInt(4);         // 3..6
        b.bFiller = 3 + rnd.nextInt(4);
        return b;
    }

    // ------------------------------------------------- symmetry classes

    /** The multiset of attacker names a mask denotes, in canonical
     *  (name-sorted) attacker order - which for a fresh board is exactly
     *  the sorted body list. */
    static String maskClass(List<String> sortedBodies, int mask) {
        List<String> names = new ArrayList<>();
        for (int i = 0; i < sortedBodies.size(); i++) {
            if ((mask & (1 << i)) != 0) {
                names.add(sortedBodies.get(i));
            }
        }
        return names.isEmpty() ? "-" : String.join(";", names);
    }

    static Set<String> classesOf(List<String> sortedBodies, List<Integer> masks) {
        Set<String> out = new TreeSet<>();
        for (int m : masks) {
            out.add(maskClass(sortedBodies, m));
        }
        return out;
    }

    // ------------------------------------------- stats-only heuristics

    /**
     * Baselines that need no search - the bar an instance has to clear to
     * be worth scoring a network on. Pre-registered here, all four, so
     * none can be swapped in after seeing which one loses.
     */
    static int heuristic(String which, Board b, Map<String, PoolCard> pool) {
        int n = b.aBodies.size();
        int all = (1 << n) - 1;
        switch (which) {
            case "allin":
                return all;
            case "never":
                return 0;
            case "bodycount": {
                int untapped = 0;
                for (String n2 : b.bBodies) {
                    if (!tapped(n2)) {
                        untapped++;
                    }
                }
                return b.aBodies.size() > untapped ? all : 0;
            }
            case "safeattack": {
                // attack with exactly those bodies that survive any single
                // block: toughness strictly greater than the best power
                // among the creatures that can actually block
                int maxBlockerPower = 0;
                for (String n2 : b.bBodies) {
                    if (!tapped(n2)) {
                        maxBlockerPower = Math.max(maxBlockerPower, pool.get(bare(n2)).power);
                    }
                }
                int mask = 0;
                for (int i = 0; i < n; i++) {
                    if (pool.get(b.aBodies.get(i)).toughness > maxBlockerPower) {
                        mask |= (1 << i);
                    }
                }
                return mask;
            }
            default:
                throw new IllegalArgumentException(which);
        }
    }

    static final String[] HEURISTICS = {"allin", "never", "bodycount", "safeattack"};

    // -------------------------------------------------------- solving

    public static final class Solved {
        public String label;
        public int value;
        public int rootOptions;
        public List<Integer> optMasks;
        public Set<String> optClasses;
        public long replays;
        public boolean capHit;
        public long noWinner;
        public double secs;
    }

    static Solved solve(Board b, int fillerDelta, long cap) {
        SubgameRunner.Spec spec = b.toSpec(fillerDelta);
        long t0 = System.nanoTime();
        SubgameSolver s = new SubgameSolver(spec);
        s.cap = cap;
        SubgameSolver.Node root = s.solve(new int[0]);
        Solved out = new Solved();
        out.value = root.value;
        out.rootOptions = root.options;
        out.optMasks = s.optimalRootChoices(root);
        out.optClasses = classesOf(b.aBodies, out.optMasks);
        out.replays = s.replays;
        out.capHit = s.capHit;
        out.noWinner = s.noWinner;
        out.secs = (System.nanoTime() - t0) / 1e9;

        if (root.seat == null || !"A".equals(root.seat) || !"atk".equals(root.kind)) {
            out.label = "BADROOT";
        } else if (out.capHit) {
            out.label = "CAPPED";
        } else if (out.noWinner > 0) {
            out.label = "NOTERM";
        } else if (out.value == 0) {
            out.label = "DEAD";            // A loses down every line
        } else if (out.optClasses.size() >= distinctClasses(b.aBodies)) {
            out.label = "TRIVIAL";         // every decision wins
        } else if (out.optClasses.size() > 1) {
            out.label = "MULTI";           // wins, but not uniquely
        } else if ("-".equals(out.optClasses.iterator().next())) {
            out.label = "HOLD";            // holding back is the only win
        } else {
            out.label = "SWING";           // one specific attack is the only win
        }
        return out;
    }

    static int distinctClasses(List<String> sortedBodies) {
        Set<String> all = new TreeSet<>();
        for (int m = 0; m < (1 << sortedBodies.size()); m++) {
            all.add(maskClass(sortedBodies, m));
        }
        return all.size();
    }

    // ------------------------------------------------- discrimination

    /** Uniform-random play by BOTH seats, sharing one RNG. Per-sample
     *  seeding is what produced the bogus 200/200 in the probe
     *  (rl/SUBGAME-T1-BUILD.md), so the stream is shared on purpose. */
    static double randomWinRate(Board b, int samples, Random rnd) {
        int wins = 0;
        SubgameRunner.Spec spec = b.toSpec(0);
        for (int i = 0; i < samples; i++) {
            SubgameRunner.Result r = SubgameRunner.scripted(spec, new int[0], rnd);
            if ("A".equals(r.winner)) {
                wins++;
            }
        }
        return wins / (double) samples;
    }

    // ------------------------------------------------------------ main

    private static void genMode(String[] args) throws Exception {
        Map<String, PoolCard> pool = readPool(args[1]);
        List<PoolCard> list = new ArrayList<>(pool.values());
        long seed = Long.parseLong(args[2]);
        int n = Integer.parseInt(args[3]);
        int shard = args.length > 4 ? Integer.parseInt(args[4]) : 0;
        int shards = args.length > 5 ? Integer.parseInt(args[5]) : 1;
        long cap = Long.getLong("subgame.replayCap", 40000L);
        int randSamples = Integer.getInteger("subgame.randSamples", 200);

        Random draws = new Random(seed);
        Random play = new Random(seed ^ 0x5DEECE66DL);
        System.out.println("# id\tlabel\tvalue\taLife\taFiller\taBodies\tbLife\tbFiller"
                + "\tbBodies\trootOpts\tclasses\toptClasses\trandA\treplays\tsecs\theur");
        int screenSamples = Integer.getInteger("subgame.screenSamples", 60);
        double screenLo = Double.parseDouble(System.getProperty("subgame.screenLo", "0.10"));
        double screenHi = Double.parseDouble(System.getProperty("subgame.screenHi", "0.90"));

        int drawn = 0, rejStats = 0, rejScreen = 0, kept = 0;
        while (kept < n) {
            Board b = draw(draws, list, drawn++);
            if (!admissible(b, pool)) {
                rejStats++;
                continue;
            }
            // CHEAP SCREEN, and it is gate 2 rather than a shortcut. A
            // board that uniform-random play already wins or loses at
            // ceiling has no discrimination to measure, and the design
            // requires it be cut. A playout costs ~26 ms against ~50 s for
            // an exact solve, so applying the gate BEFORE the solve is
            // what makes the search affordable.
            //
            // The consequence is stated rather than hidden: the family is
            // SELECTED on random-play win rate, so the randA column is the
            // gate, not an unbiased estimate of random play on admissible
            // boards. It is re-measured on an independent sample below so
            // the reported number is at least not the screen's own draw.
            double screen = randomWinRate(b, screenSamples, play);
            if (screen < screenLo || screen > screenHi) {
                rejScreen++;
                continue;
            }
            int idx = kept++;
            if (idx % shards != shard) {
                continue;                   // same draw stream in every shard
            }
            Solved s = solve(b, 0, cap);
            StringBuilder heur = new StringBuilder();
            for (String h : HEURISTICS) {
                int m = heuristic(h, b, pool);
                boolean ok = s.optClasses.contains(maskClass(b.aBodies, m));
                heur.append(heur.length() == 0 ? "" : ",").append(h)
                        .append(ok ? "=1" : "=0");
            }
            double rand = ("HOLD".equals(s.label) || "SWING".equals(s.label))
                    ? randomWinRate(b, randSamples, play) : -1;
            System.out.println("INST\t" + b.id + "\t" + s.label + "\t" + s.value
                    + "\t" + b.fields()
                    + "\t" + s.rootOptions
                    + "\t" + distinctClasses(b.aBodies)
                    + "\t" + String.join("|", s.optClasses)
                    + "\t" + (rand < 0 ? "-" : String.format("%.3f", rand))
                    + "\t" + s.replays
                    + "\t" + String.format("%.1f", s.secs)
                    + "\t" + heur);
            System.out.flush();
        }
        System.out.println("# admission: drawn=" + drawn
                + " rejStats=" + rejStats + " rejScreen=" + rejScreen
                + " admitted=" + kept + " rate="
                + String.format("%.3f", kept / (double) drawn));
    }

    private static void gate1Mode(String[] args) throws Exception {
        Map<String, PoolCard> pool = readPool(args[1]);
        int delta = args.length > 3 ? Integer.parseInt(args[3]) : 2;
        long cap = Long.getLong("subgame.replayCap", 200000L);
        try (BufferedReader r = new BufferedReader(new FileReader(args[2]))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (!line.startsWith("INST\t")) {
                    continue;
                }
                String[] f = line.split("\t");
                String id = f[1];
                String label = f[2];
                if (!"HOLD".equals(label) && !"SWING".equals(label)) {
                    continue;
                }
                Board b = Board.parse(id, f, 4);
                String before = f[10];
                Solved s = solve(b, delta, cap);
                String after = String.join("|", s.optClasses);
                boolean same = before.equals(after) && s.value == Integer.parseInt(f[3]);
                System.out.println("GATE1\t" + id + "\t" + label
                        + "\tdelta=" + delta
                        + "\tbefore=" + before + "\tafter=" + after
                        + "\tvalue=" + s.value
                        + "\tstable=" + (same ? 1 : 0)
                        + "\tlabelAfter=" + s.label
                        + "\treplays=" + s.replays
                        + "\tsecs=" + String.format("%.1f", s.secs));
                System.out.flush();
            }
        }
    }

    public static void main(String[] args) throws Exception {
        mage.cards.repository.CardScanner.scan();
        if (args.length == 0) {
            System.out.println("usage: pool <sets> | gen <pool> <seed> <n> [shard] [shards]"
                    + " | gate1 <pool> <instFile> [delta]");
            return;
        }
        switch (args[0]) {
            case "pool":
                poolMode(args);
                return;
            case "gen":
                genMode(args);
                return;
            case "gate1":
                gate1Mode(args);
                return;
            default:
                System.out.println("unknown mode: " + args[0]);
        }
    }

    private SubgameFamily() {
    }
}
