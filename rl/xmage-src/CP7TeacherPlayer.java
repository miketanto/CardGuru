package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.abilities.ActivatedAbility;
import mage.abilities.PlayLandAbility;
import mage.abilities.SpellAbility;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.Game;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * 7d piece (1b): XMage's ComputerPlayer7 as an imitation TEACHER on the v7
 * wire (V7-VALIDATION "7d piece (1b) design"). The seat plays exactly as
 * CP7 does; at every priority window where RLPlayer would consult its
 * policy it ALSO emits the consult RLPlayer would have emitted - same
 * candidate list (getPlayable, phantom-land filter, mana-ability filter
 * unless rl.manaCands, same name|rule order), same EntityView, same
 * CandMeta with the v7 afterstates, same tracker - labelled with the
 * index of the candidate CP7 then acted on:
 *   y = 0     CP7 passed (no non-mana activation in the window)
 *   y = i+1   CP7's first activation was playable.get(i) (sourceId|rule)
 *   y = -1    CP7 acted on something outside the candidate set
 * The consult state is taken BEFORE super.priority(game) runs; the label
 * is read from the activateAbility interception AFTER it; the consult is
 * then sent (reply ignored - CP7 already acted). Extra activations in the
 * same window are counted (teacherMultiAct), not labelled.
 *
 * PRIORITY-ONLY for the first recording: CP7 declares attackers/blockers
 * through ComputerPlayer6.declareAttackers/declareBlockers, and lifting
 * RLPlayer.jointAttacks/jointBlocks (the CombatMath candidate lists) out
 * of RLPlayer was not cheap enough to do blind while the lane owned the
 * engine. The joint consults are therefore ABSENT from a cp7-seat
 * recording (not even unlabelled), and BC trains on priority consults
 * only - stated in the recording row.
 *
 * Simulations: ComputerPlayer6 replaces every player of its simulated
 * game copies with SimulatedPlayer2, so this object's overrides never see
 * a simulation; the isSimulation() guards are belt and braces.
 */
public class CP7TeacherPlayer extends mage.player.ai.ComputerPlayer7 {

    /** the recording policy (the echo server); null = plain CP7 */
    public PolicyClient policy;
    public long benchSeed = 0;
    /** 3d: the opponent's open decklist, set by EpisodeRunner (tracker) */
    public java.util.Map<String, RLKnowledgeWatcher.DeckCard> oppDeckInfo;
    /** the RL seat's budget: windows past it are played unlabelled */
    public long consultBudget = Long.getLong("rl.consultBudget", 20000L);
    /** 7a amendment: mana abilities are candidates only with rl.manaCands */
    public boolean manaCands = Boolean.getBoolean("rl.manaCands");

    public long windows = 0, consults = 0, autoPassK0 = 0, manaCandsDropped = 0;
    public long teacherLabelled = 0, teacherPassed = 0, teacherOutside = 0,
            teacherMultiAct = 0, teacherBudgetSkipped = 0;

    private boolean capturing = false;
    private ActivatedAbility captured = null;
    private int extraActs = 0;

    public CP7TeacherPlayer(String name, RangeOfInfluence range, int skill) {
        super(name, range, skill);
    }

    private UUID opponentId(Game game) {
        for (UUID opp : game.getOpponents(playerId)) {
            return opp;
        }
        return playerId;
    }

    private void ensureTracker(Game game) {
        if (StateEncoder.ENCODER_V >= 7) {
            RLKnowledgeWatcher.ensure(game, playerId, opponentId(game), oppDeckInfo);
        }
    }

    @Override
    public boolean activateAbility(ActivatedAbility ability, Game game) {
        if (capturing && !game.isSimulation() && !ability.isManaAbility()) {
            if (captured == null) {
                captured = ability;
            } else {
                extraActs++;
            }
        }
        return super.activateAbility(ability, game);
    }

    @Override
    public boolean priority(Game game) {
        if (policy == null || game.isSimulation() || !canRespond()
                || StateEncoder.ENCODER_V < 7) {
            return super.priority(game);
        }
        windows++;
        ensureTracker(game);
        boolean myTurn = playerId.equals(game.getActivePlayerId());
        boolean sorceryWindow = myTurn && game.getStack().isEmpty()
                && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN);
        List<ActivatedAbility> playable;
        try {
            playable = new ArrayList<>(getPlayable(game, true));
        } catch (Exception e) {
            return super.priority(game);
        }
        // exactly RLPlayer.priority's filters and order
        playable.removeIf(a -> a instanceof PlayLandAbility && !sorceryWindow);
        if (!manaCands) {
            int before = playable.size();
            playable.removeIf(a -> a.isManaAbility());
            manaCandsDropped += before - playable.size();
        }
        if (playable.isEmpty()) {
            // the RL seat auto-passes k=0 without a consult; CP7 plays the
            // window as itself (there is nothing it could do but pass)
            autoPassK0++;
            return super.priority(game);
        }
        playable.sort(Comparator.comparing(a -> {
            MageObject o = game.getObject(a.getSourceId());
            return (o == null ? "?" : o.getName()) + "|" + a.getRule();
        }));
        if (consults >= consultBudget) {
            teacherBudgetSkipped++;
            return super.priority(game);
        }
        // the pre-action consult, built as RLPlayer.priority builds it
        float[][] cands = new float[playable.size() + 1][];
        StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length).pass(0);
        int untappedNow = StateEncoder.untappedLands(game, playerId);
        cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            meta.set(i + 1, a instanceof PlayLandAbility ? StateEncoder.C_LAND
                    : a instanceof SpellAbility ? StateEncoder.C_SPELL
                    : StateEncoder.C_ACTIVATE, a.getSourceId());
            Card card = game.getCard(a.getSourceId());
            cands[i + 1] = StateEncoder.forCard(
                    a instanceof PlayLandAbility
                            ? StateEncoder.T_LAND : StateEncoder.T_SPELL,
                    card, game);
            meta.after(i + 1, StateEncoder.v7AfterPlayable(a, card, game, playerId, untappedNow));
        }
        meta.consultsSoFar = consults;
        StateEncoder.EntityView view =
                StateEncoder.encodeEntityView(game, playerId, opponentId(game));

        // CP7 decides and acts
        capturing = true;
        captured = null;
        extraActs = 0;
        boolean r;
        try {
            r = super.priority(game);
        } finally {
            capturing = false;
        }
        int y;
        if (captured == null) {
            y = 0;
            teacherPassed++;
        } else {
            y = matchLabel(captured, playable);
        }
        if (extraActs > 0) {
            teacherMultiAct++;
        }
        if (y >= 0) {
            teacherLabelled++;
        } else {
            teacherOutside++;
        }
        consults++;
        if (policy instanceof SocketPolicyClient) {
            ((SocketPolicyClient) policy).teacherY = y;
        }
        policy.choose(view, cands, 0f, meta);   // reply ignored: CP7 acted
        return r;
    }

    /** index of the acted ability in RLPlayer's candidate space (1-based;
     *  -1 = outside the set), keyed sourceId|rule as shadowLabel does */
    private static int matchLabel(ActivatedAbility chosen, List<ActivatedAbility> playable) {
        String key = chosen.getSourceId() + "|" + chosen.getRule();
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            if ((a.getSourceId() + "|" + a.getRule()).equals(key)) {
                return i + 1;
            }
        }
        return -1;
    }
}
