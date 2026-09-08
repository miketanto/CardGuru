"""Belief is probability, not rules — so it tests without the engine.

A synthetic three-archetype corpus exercises classification (distinctive
cards pin the deck, shared cards don't), the hidden-pool subtraction,
determinization sampling, and the trick-rate summary a robust line needs.
"""
import random

import pytest

from cardguru import believe

CORPUS = [
    {"archetype": "Red", "cards": {"Mountain": 20, "Bolt": 4, "Goblin": 4,
                                   "Shared Bear": 2},
     "tricks": [{"card": "Bolt", "kind": "removal", "damage": 3}]},
    {"archetype": "Green", "cards": {"Forest": 20, "Growth": 4, "Wurm": 4,
                                     "Shared Bear": 2},
     "tricks": [{"card": "Growth", "kind": "pump", "power": 3}]},
    {"archetype": "Blue", "cards": {"Island": 20, "Merfolk": 4, "Drake": 4},
     "tricks": []},
]


def test_distinctive_card_pins_the_archetype():
    post = believe.classify(["Goblin"], CORPUS)
    assert post[0]["archetype"] == "Red"
    assert post[0]["p"] > 0.99            # Goblin is unique to Red


def test_shared_card_is_weak_evidence_and_basics_are_ignored():
    # "Shared Bear" is in Red and Green equally; lands carry no signal
    post = {r["archetype"]: r["p"]
            for r in believe.classify(["Shared Bear", "Mountain"], CORPUS)}
    assert abs(post["Red"] - post["Green"]) < 1e-9   # tie between the two
    assert post["Blue"] == 0.0
    # a pure-basics/empty observation falls back to the flat prior
    flat = believe.classify(["Mountain"], CORPUS)
    assert abs(flat[0]["p"] - 1 / 3) < 1e-9


def test_believed_remaining_subtracts_seen():
    deck = CORPUS[0]["cards"]
    rem = believe.believed_remaining(CORPUS[0], ["Bolt", "Bolt", "Goblin"])
    assert rem["Bolt"] == 2 and rem["Goblin"] == 3
    assert "Shared Bear" in rem


def test_sample_hidden_is_deterministic_by_seed_and_bounded():
    rem = {"Bolt": 4, "Goblin": 4, "Mountain": 10}
    a = believe.sample_hidden(rem, 7, 5, random.Random(1))
    b = believe.sample_hidden(rem, 7, 5, random.Random(1))
    assert a == b and len(a) == 5 and all(len(h) == 7 for h in a)
    tiny = believe.sample_hidden({"Bolt": 2}, 7, 3, random.Random(1))
    assert all(h == ["Bolt", "Bolt"] for h in tiny)   # can't hold more


def test_trick_rate_tracks_the_believed_pool():
    seen = ["Goblin"]                      # -> Red, which holds Bolt
    hot = believe.response_probability(seen, CORPUS, hand_size=7, k=200,
                                       rng=random.Random(3))
    assert hot["archetype"] == "Red"
    assert 0.0 < hot["trick_rate"] <= 1.0
    # Blue has no tricks -> a Blue read is never blown out in combat
    cold = believe.response_probability(["Merfolk"], CORPUS, hand_size=7,
                                        k=50, rng=random.Random(3))
    assert cold["archetype"] == "Blue" and cold["trick_rate"] == 0.0


def test_real_corpus_loads_and_classifies():
    import os
    if not os.path.isdir("meta_decks"):
        pytest.skip("meta corpus not present")
    corpus = believe.load_corpus("meta_decks")
    assert len(corpus) >= 3
    post = believe.classify(["Monastery Swiftspear", "Lightning Bolt"], corpus)
    assert post[0]["archetype"] == "Mono-Red Aggro"
