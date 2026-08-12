package org.mage.test.benchmark;

/**
 * Phase 5 open-mana experiment: D1h — the "draw-go" pole. Identical to
 * SearchPlayer except flash/instant-speed cards are NEVER cast at
 * sorcery speed (search candidates and the D0 fallback both hold
 * them). The mana they would have spent stays open, so the v3
 * instant-speed branches (opponent end step, counterspells on the
 * stack, ninjutsu at declare-blockers) fire with mana available —
 * the line the greedy evaluator can never choose because it has no
 * option-value term. Calibrating D1h against D1 measures what
 * open-mana timing is actually worth in this environment.
 */
public class SearchPlayerHold extends SearchPlayer {

    public SearchPlayerHold(String name) {
        super(name);
        holdFlashSearch = true;
        holdFlashAtMain = true;
    }
}
