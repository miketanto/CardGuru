"""Opponent modeling under hidden information: from cards seen to a response
distribution.

Tiers 1-3 handed the agent the opponent's responses — enumerated, certain.
Real Magic does not: you see a few of the opponent's cards and must infer
the rest. This module is the PokeChamp opponent-model slot, transposed. It
never touches the engine; it turns public evidence into a believed deck and
that deck into the *sampled* response sets minimax then runs over.

The pipeline, each step pure and testable:

  classify(seen, corpus)        cards the opponent has revealed -> a
                                posterior over meta archetypes (overlap
                                scored, normalized). This is where MTG is
                                EASIER than Pokemon: a defined meta means a
                                handful of seen cards usually pins the deck.
  believed_remaining(deck,seen) the archetype's list minus what's accounted
                                for = what could still be in hand/library.
  sample_hidden(remaining, ...) determinization: draw K plausible hands the
                                opponent could be holding.
  trick_responses(hand, board)  from a believed hand, the responses that
                                change combat math — the instant-speed pump
                                or removal they might hold, plus the blocks
                                their untapped creatures allow.

A "meta deck" is a small JSON: {"archetype", "cards": {name: count},
"tricks": [{card, kind, ...}]}. The corpus lives in meta_decks/ (kept out
of the gitignored data/ tree since it is source, not a build artifact).
`tricks` names the deck's known instant-speed combat interaction so the
sampler can ask "is a trick live in this determinization?" without parsing
oracle text here (the encoder already renders text; belief is about
probability, not rules).
"""
from __future__ import annotations

import json
import os
import random

DEFAULT_CORPUS = "meta_decks"


def load_corpus(path: str = DEFAULT_CORPUS) -> list[dict]:
    decks = []
    if not os.path.isdir(path):
        return decks
    for fn in sorted(os.listdir(path)):
        if fn.endswith(".json"):
            with open(os.path.join(path, fn), encoding="utf-8") as f:
                decks.append(json.load(f))
    return decks


def classify(seen: list[str], corpus: list[dict]) -> list[dict]:
    """Posterior over archetypes given cards seen.

    Score = fraction of seen cards the archetype's 75 can account for,
    weighted by how *distinctive* each seen card is (a card in one
    archetype is stronger evidence than a card in all of them). Basic lands
    carry no signal and are ignored. Returns archetypes ranked by
    normalized probability; an empty/uninformative `seen` yields the flat
    prior so a caller always gets a usable distribution.
    """
    informative = [c for c in seen if not _is_basic(c)]
    n_decks = len(corpus)
    if not corpus:
        return []
    # how many archetypes each card appears in (distinctiveness)
    appears_in = {}
    for deck in corpus:
        for name in deck.get("cards", {}):
            appears_in[name] = appears_in.get(name, 0) + 1
    scores = []
    for deck in corpus:
        cards = deck.get("cards", {})
        s = 0.0
        for name in informative:
            if name in cards:
                s += 1.0 / appears_in.get(name, n_decks)  # rarer = stronger
        scores.append(s)
    total = sum(scores)
    if total == 0:
        p = 1.0 / n_decks
        return [{"archetype": d["archetype"], "p": p, "deck": d}
                for d in corpus]
    ranked = sorted(
        ({"archetype": d["archetype"], "p": s / total, "deck": d}
         for d, s in zip(corpus, scores)),
        key=lambda r: r["p"], reverse=True)
    return ranked


def believed_remaining(deck: dict, seen: list[str]) -> dict[str, int]:
    """The archetype's cards minus what's been seen — the hidden pool.

    Seen copies are removed one-for-one; a card seen more often than the
    list expects simply floors at zero (the belief was imperfect, not the
    evidence wrong).
    """
    remaining = dict(deck.get("cards", {}))
    for name in seen:
        if remaining.get(name, 0) > 0:
            remaining[name] -= 1
    return {k: v for k, v in remaining.items() if v > 0}


def sample_hidden(remaining: dict[str, int], hand_size: int, k: int,
                  rng: random.Random) -> list[list[str]]:
    """K plausible hidden hands drawn without replacement from the pool.

    Determinization: each sample is one concrete world the opponent might
    be in. A pool smaller than hand_size yields the whole pool (they can't
    hold what they don't have). Duplicate samples are allowed — their
    repetition IS the probability that world matters.
    """
    pool = [name for name, n in remaining.items() for _ in range(n)]
    hands = []
    for _ in range(k):
        if len(pool) <= hand_size:
            hands.append(sorted(pool))
        else:
            hands.append(sorted(rng.sample(pool, hand_size)))
    return hands


def trick_in_hand(deck: dict, hand: list[str]) -> list[dict]:
    """Which of the deck's named combat tricks a believed hand is holding."""
    held = []
    for trick in deck.get("tricks", []):
        if trick["card"] in hand:
            held.append(trick)
    return held


def response_probability(seen: list[str], corpus: list[dict], hand_size: int,
                         k: int, rng: random.Random) -> dict:
    """End-to-end belief summary for a decision.

    Returns the top archetype, its posterior, K sampled hidden hands, and
    the fraction of samples in which at least one combat trick is live —
    the single number a robust line most needs ("how often does attacking
    into open mana get blown out?").
    """
    posterior = classify(seen, corpus)
    if not posterior:
        return {"archetype": None, "p": 0.0, "hands": [], "trick_rate": 0.0}
    top = posterior[0]
    remaining = believed_remaining(top["deck"], seen)
    hands = sample_hidden(remaining, hand_size, k, rng)
    live = sum(1 for h in hands if trick_in_hand(top["deck"], h))
    return {"archetype": top["archetype"], "p": top["p"],
            "remaining": remaining, "hands": hands,
            "trick_rate": live / len(hands) if hands else 0.0}


def materialize_responses(deck: dict, blocker: str,
                          attackers: list[tuple[str, int, int]]) -> list[dict]:
    """Turn a believed deck into concrete opponent_responses for grading.

    The opponent's hand is never seen, so we cannot know which response
    they *will* make — but the believed archetype bounds which they COULD.
    We emit every response the belief says is possible, and minimax grading
    requires the line to beat all of them:

      - no block (always possible)
      - block the biggest attacker with `blocker` (if the opponent has one)
      - the opponent's single BEST removal: across the removal tricks the
        deck can hold, the one cast on the attacker that removes the most
        power. Killing an attacker removes its combat damage, which is what
        actually changes lethal math (a mere pump on a blocker does not: a
        blocked attacker deals no face damage either way). Only the best is
        emitted — the opponent makes one response, and the worst case for
        the agent is their strongest answer.

    `attackers` is (name, power, toughness) for the agent's creatures, so
    the materializer can pick the removal's best target. Responses are scripted
    action lists mergeable into the agent's line, exactly like the
    enumerated T3 responses — belief changes where the set comes from, not
    how it grades. The generator seats the trick + a matching untapped land
    on the opponent so each scripted cast is legal; the trick is cast in
    the DECLARE_ATTACKERS step, before combat damage.
    """
    responses = [[]]
    if blocker and attackers:
        biggest = max(attackers, key=lambda a: a[1])[0]
        responses.append([{"do": "block", "turn": 1, "player": "B",
                           "blocker": blocker, "attacker": biggest}])
    best = None  # (power_removed, trick_card, target_name)
    for trick in deck.get("tricks", []):
        if trick.get("kind") != "removal":
            continue
        dmg = trick.get("damage", 0)
        killable = [(name, p, t) for name, p, t in attackers if t <= dmg]
        if not killable:
            continue
        name, p, _ = max(killable, key=lambda a: a[1])
        if best is None or p > best[0]:
            best = (p, trick["card"], name)
    if best is not None:
        _, card, target = best
        responses.append([
            {"do": "cast", "turn": 1, "phase": "DECLARE_ATTACKERS",
             "player": "B", "card": card},
            {"do": "target", "player": "B", "value": target},
        ])
    return responses


def best_removal_card(deck: dict, attackers: list[tuple[str, int, int]]):
    """The card materialize_responses will use for the removal response, so
    the generator can seat exactly that card in the opponent's hand."""
    for r in materialize_responses(deck, "", attackers):
        for a in r:
            if a.get("do") == "cast":
                return a["card"]
    return None


def _is_basic(name: str) -> bool:
    return name in ("Plains", "Island", "Swamp", "Mountain", "Forest",
                    "Wastes")
