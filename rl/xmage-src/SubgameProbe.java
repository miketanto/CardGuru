package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.game.Game;
import mage.game.permanent.Permanent;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;

/**
 * Puts a policy at a SOLVED subgame position and asks one question:
 * did it choose an optimal action, and could it have?
 *
 * Two numbers come out, and they are different failures:
 *   EXPRESSIBLE - is any optimal action present in the candidate list
 *                 the policy selects from? This is 15/C's coverage
 *                 question, verified per position instead of estimated.
 *                 A "no" is an action-space finding and the policy is
 *                 not scored on that position.
 *   OPTIMAL     - given it was expressible, did the policy pick it?
 *
 * Both are measured in SOLVER space: an attack is the set of attacking
 * creature ids, mapped onto a bitmask over the canonically ordered
 * available attackers. Mapping by id rather than by position matters -
 * RLPlayer sorts its own candidates by name only, LinePlayer by name
 * then id, and comparing positions across those two orderings would
 * silently compare different creatures.
 */
public final class SubgameProbe {

    /** Canonical order, shared with LinePlayer: name, then id. */
    static List<Permanent> canonicalAttackers(Game game, ProbePlayer me) {
        List<Permanent> avail = new ArrayList<>(me.getAvailableAttackers(game));
        avail.sort(Comparator.comparing(MageObject::getName)
                .thenComparing(p -> p.getId().toString()));
        return avail;
    }

    static int maskOf(List<Permanent> canonical, Set<UUID> chosen) {
        int mask = 0;
        for (int i = 0; i < canonical.size(); i++) {
            if (chosen.contains(canonical.get(i).getId())) {
                mask |= (1 << i);
            }
        }
        return mask;
    }

    /** An RL seat that records its FIRST attack decision in solver space,
     *  together with every attack option its candidate list could have
     *  expressed. */
    public static final class ProbePlayer extends RLPlayer {

        public int chosenMask = -1;
        public final Set<Integer> candidateMasks = new TreeSet<>();
        public boolean recorded = false;

        public ProbePlayer(String name) {
            super(name);
        }

        @Override
        public void selectAttackers(Game game, UUID attackingPlayerId) {
            boolean first = !recorded;
            List<Permanent> canonical = first
                    ? canonicalAttackers(game, this) : null;

            if (first && !canonical.isEmpty()) {
                // what the candidate generator could have offered, in
                // solver space - JointCands is the same call RLPlayer
                // makes, so this is its list and not a reconstruction
                UUID defender = null;
                for (UUID opp : game.getOpponents(getId())) {
                    defender = opp;
                    break;
                }
                List<Permanent> avail = new ArrayList<>(getAvailableAttackers(game));
                avail.sort(Comparator.comparing(MageObject::getName));
                JointCands.Attack ja = JointCands.attacks(game, defender, avail,
                        getLife(), StateEncoder.ENCODER_V >= 7, s -> { });
                for (CombatMath.AttackOption opt : ja.kept) {
                    Set<UUID> ids = new HashSet<>();
                    for (int i = 0; i < opt.attack.length && i < ja.pick.size(); i++) {
                        if (opt.attack[i]) {
                            ids.add(ja.pick.get(i).getId());
                        }
                    }
                    candidateMasks.add(maskOf(canonical, ids));
                }
            }

            super.selectAttackers(game, attackingPlayerId);

            if (first && canonical != null && !canonical.isEmpty()) {
                Set<UUID> declared = new HashSet<>(game.getCombat().getAttackers());
                chosenMask = maskOf(canonical, declared);
                recorded = true;
            }
        }
    }

    /** What one position's probe returned. */
    public static final class Result {
        public int samples;
        public int expressible;
        public int optimalPicks;
        public final Set<Integer> cands = new TreeSet<>();
        public final Set<Integer> seenChoices = new TreeSet<>();
    }

    /**
     * Probe ONE position whose optimal action set is already known.
     *
     * `optimal` is a set of MASKS, and for a family it is every mask in
     * the optimal symmetry class rather than the single mask the solver
     * happened to return: two copies of one vanilla body are one
     * decision, so offering either satisfies expressibility.
     *
     * `shared` must be one client for the whole battery - see the note in
     * main(); passing a fresh one per sample is a measured way to get a
     * clean-looking wrong number.
     */
    public static Result probe(SubgameRunner.Spec spec, Set<Integer> optimal,
                               int samples, int port, RandomPolicyClient shared)
            throws java.io.IOException {
        Result out = new Result();
        for (int i = 0; i < samples; i++) {
            ProbePlayer p = new ProbePlayer("A");
            p.policy = port > 0
                    ? new SocketPolicyClient(port, "eval", samples)
                    : shared;
            p.resetPerEpisode();
            p.benchSeed = 7000L + i;
            SubgameRunner.run(spec, p, new int[0], p);
            if (p.chosenMask >= 0) {
                out.samples++;
                out.seenChoices.add(p.chosenMask);
                out.cands.addAll(p.candidateMasks);
                for (int o : optimal) {
                    if (p.candidateMasks.contains(o)) {
                        out.expressible++;
                        break;
                    }
                }
                if (optimal.contains(p.chosenMask)) {
                    out.optimalPicks++;
                }
            }
            if (port > 0) {
                break;      // argmax policy is deterministic; one is enough
            }
        }
        return out;
    }

    public static void main(String[] args) throws Exception {
        mage.cards.repository.CardScanner.scan();
        int samples = args.length > 0 ? Integer.parseInt(args[0]) : 200;
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 0;
        String small = args.length > 2 ? args[2] : "Silvercoat Lion";
        String big = args.length > 3 ? args[3] : "Trokin High Guard";

        SubgameRunner.Spec spec = SubgameRunner.t1Hold(small, big);

        // 1. ground truth
        SubgameSolver solver = new SubgameSolver(spec);
        SubgameSolver.Node root = solver.solve(new int[0]);
        List<Integer> optimal = solver.optimalRootChoices(root);

        // 2. the policy, at that position
        int optimalPicks = 0;
        int expressible = 0;
        Set<Integer> seenChoices = new TreeSet<>();
        Set<Integer> cands = new TreeSet<>();
        // ONE random client for the whole battery. A fresh
        // RandomPolicyClient(7000+i) per sample looked equivalent and is
        // not: at v5+ there is a single consult per combat, so only the
        // FIRST nextInt of each seed is ever used, and java.util.Random
        // gives the same first value for long runs of consecutive seeds.
        // That made a uniform policy look like it played optimally 200/200.
        RandomPolicyClient shared = new RandomPolicyClient(7000L);
        for (int i = 0; i < samples; i++) {
            ProbePlayer p = new ProbePlayer("A");
            p.policy = port > 0
                    ? new SocketPolicyClient(port, "eval", samples)
                    : shared;
            p.resetPerEpisode();
            p.benchSeed = 7000L + i;
            SubgameRunner.run(spec, p, new int[0], p);
            if (Boolean.getBoolean("probe.trace") && i < 8) {
                System.out.println("TRACE|i=" + i + "|chosen=" + p.chosenMask
                        + "|cands=" + p.candidateMasks + "|recorded=" + p.recorded);
            }
            if (p.chosenMask >= 0) {
                seenChoices.add(p.chosenMask);
                cands.addAll(p.candidateMasks);
                boolean anyOptimalOffered = false;
                for (int o : optimal) {
                    if (p.candidateMasks.contains(o)) {
                        anyOptimalOffered = true;
                    }
                }
                if (anyOptimalOffered) {
                    expressible++;
                }
                if (optimal.contains(p.chosenMask)) {
                    optimalPicks++;
                }
            }
            if (port > 0) {
                break;      // argmax policy is deterministic; one is enough
            }
        }
        int n = port > 0 ? 1 : samples;
        System.out.println("PROBE|" + spec.name
                + "|policy=" + (port > 0 ? "socket" : "random")
                + "|samples=" + n
                + "|optimalActions=" + optimal
                + "|candidateMasks=" + cands
                + "|expressible=" + expressible + "/" + n
                + "|optimalPicks=" + optimalPicks + "/" + n
                + "|rate=" + String.format("%.3f", optimalPicks / (double) n)
                + "|choicesSeen=" + seenChoices);
    }

    private SubgameProbe() {
    }
}
