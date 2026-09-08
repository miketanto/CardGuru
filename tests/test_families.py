"""Disjunctive family mining: derive that one concept has several api names.

`shapes.py` splits an overloaded name into its meanings. This is the mirror
failure and the one the measured A/B keeps losing to — the compiler writes
{"api": "Destroy"} and silently answers a narrower question than it was asked,
because nothing in the ontology says `DestroyAll` is the same idea.

The tests below pin the two properties that make a mined family safe to put in
a prompt: it must not merge antonyms (the classic distributional-similarity
failure) and it must not merge the two ends of a chain (the reason "shares a
word" is not enough on its own).
"""
import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import families as fam  # noqa: E402


def face(name, oracle, nodes):
    return {"name": name, "oracle": oracle, "nodes": nodes, "edges": []}


def node(nid, api=None, mode=None, desc="", **params):
    n = {"id": nid, "params": dict(params, SpellDescription=desc)}
    if api:
        n["api"] = api
    if mode:
        n["params"]["Mode"] = mode
    return n


# A miniature corpus with one of each situation the miner has to get right.
#
#   Destroy / DestroyAll  a real family: same word, never on the same card
#   GainLife / LoseLife   antonyms: identical params, opposite words
#   Reveal  -> RevealHand a chain: same word, always on the same card
FACES = []
for i in range(40):
    FACES.append(face(f"Bolt{i}", "Destroy target creature.",
                      [node("a", api="Destroy", desc="Destroy target creature.",
                            ValidTgts="Creature")]))
for i in range(30):
    FACES.append(face(f"Wrath{i}", "Destroy all creatures.",
                      [node("a", api="DestroyAll", desc="Destroy all creatures.",
                            ValidCards="Creature")]))
for i in range(30):
    FACES.append(face(f"Heal{i}", "You gain 3 life.",
                      [node("a", api="GainLife", desc="You gain 3 life.",
                            LifeAmount="3", Defined="You")]))
for i in range(30):
    FACES.append(face(f"Drain{i}", "Target player loses 3 life.",
                      [node("a", api="LoseLife", desc="Target player loses 3 life.",
                            LifeAmount="3", Defined="Targeted")]))
for i in range(30):
    FACES.append(face(f"Peek{i}", "Reveal your hand. Reveal a card.",
                      [node("a", api="Reveal", desc="Reveal a card.",
                            RevealDefined="You"),
                       node("b", api="RevealHand", desc="Reveal your hand.",
                            RevealDefined="You")]))

# Filler, so the anchor lift has a realistic denominator. The statistic is
# "this word at N times its rate among nodes of the same kind"; in a corpus
# that is nothing but the four cases above, "destroy" is 12% of all api text
# and no word can be 4x the background. The real corpus is 191 apis wide.
_FILLER = ("scry surveil goad amass explore venture connive proliferate "
           "manifest incubate investigate populate).".split()[:12])
for i in range(240):
    w = _FILLER[i % len(_FILLER)]
    FACES.append(face(f"Filler{i}", f"You {w} for a permanent this turn.",
                      [node("a", api=f"Filler{i % 12}",
                            desc=f"You {w} for a permanent this turn.",
                            Defined="You")]))


@pytest.fixture(scope="module")
def mined(tmp_path_factory):
    d = tmp_path_factory.mktemp("families")
    path = os.path.join(d, "dataset.jsonl.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": {"source_pin": "abc123", "format": 1}}) + "\n")
        for rec in FACES:
            f.write(json.dumps(rec) + "\n")
    return fam.mine(path)


def members(mined, *names):
    """The family whose member set is exactly `names`, or None."""
    want = set(names)
    for f in mined["families"]:
        if {m["name"] for m in f["members"]} == want:
            return f
    return None


def family_containing(mined, name):
    return [f for f in mined["families"]
            if any(m["name"] == name for m in f["members"])]


def test_finds_the_singular_and_mass_variants_of_one_effect(mined):
    f = members(mined, "Destroy", "DestroyAll")
    assert f is not None, "the family the whole module exists for"
    assert f["kind"] == "api"
    assert "destroy" in f["anchors"]
    assert f["volume"] == 70


def test_a_polarity_word_never_selects_the_opposite_effect(mined):
    """GainLife and LoseLife have the same params, the same neighbours and the
    same card contexts — a cosine over any of those merges them, which is the
    textbook distributional failure and what the first version of this module
    did. The anchor is what separates them: "gain" must select one side only."""
    for f in mined["families"]:
        names = {m["name"] for m in f["members"]}
        if "gain" in f["anchors"]:
            assert "LoseLife" not in names
        if "loses" in f["anchors"]:
            assert "GainLife" not in names


def test_a_shared_noun_still_groups_opposites_and_says_so(mined):
    """Not a bug, and worth pinning so nobody 'fixes' it: "life" is on both
    sides, and a question that says only "life" really is ambiguous between
    them. The family carries its anchor, so the ambiguity is visible rather
    than buried."""
    f = members(mined, "GainLife", "LoseLife")
    assert f is not None and f["anchors"] == ["life"]


def test_does_not_merge_the_two_ends_of_a_chain(mined):
    """Reveal and RevealHand share the word "reveal" and pass the anchor test,
    but they are steps of one ability rather than alternatives: they are on the
    same card every time. Disjoining over them would be meaningless."""
    for f in mined["families"]:
        names = {m["name"] for m in f["members"]}
        assert not {"Reveal", "RevealHand"} <= names


def test_co_occurrence_lift_separates_the_two_cases(mined):
    """The number the peel is thresholded on, stated directly: substitutes sit
    at or below chance, complements far above it."""
    assert members(mined, "Destroy", "DestroyAll")["max_co_lift"] <= 1.0


def test_every_family_has_at_least_two_members(mined):
    assert mined["families"]
    for f in mined["families"]:
        assert len(f["members"]) >= 2


def test_members_are_ordered_by_volume(mined):
    for f in mined["families"]:
        counts = [m["nodes"] for m in f["members"]]
        assert counts == sorted(counts, reverse=True)


def test_anchors_must_appear_in_oracle_text(mined):
    """Forge descriptions carry template tokens (CARDNAME, EFFECTSOURCE) that
    are frequent and specific but are not words a question can contain. The
    oracle corpus is the player-facing rendering, and it has no such token."""
    for f in mined["families"]:
        assert "cardname" not in f["anchors"]


def test_meta_stamps_the_source_pin(mined):
    """A family set is only valid for the dataset it was mined from."""
    assert mined["_meta"]["forge_pin"] == "abc123"
    assert mined["_meta"]["cards"] == len(FACES)


def test_digest_is_prompt_sized(mined):
    assert len(fam.digest(mined)) < 4000


def test_digest_names_members_without_counts(mined):
    """The compiler is not choosing between members — it is being told to take
    all of them — so node counts would only be noise."""
    text = fam.digest(mined)
    assert "Destroy, DestroyAll" in text
    assert "(" not in text


def test_digest_truncates_by_rank_not_arbitrarily(mined):
    """A truncated digest must keep the families that cover the most cards
    under the most specific anchor, not whichever came out of the dict first."""
    scores = [f["rank_score"] for f in mined["families"]]
    assert scores == sorted(scores, reverse=True)


def test_mining_is_deterministic(tmp_path):
    """Found the expensive way: the greedy peel and the merge both iterate sets
    of facet tuples, whose order follows string hashes and therefore changes
    per interpreter run. The same command mined 89, 90 and 91 families on three
    runs. An artifact that differs from itself cannot be diffed against a Forge
    bump, and silently voids any A/B that regenerates it between arms."""
    import subprocess
    import sys

    d = tmp_path / "dataset.jsonl.gz"
    with gzip.open(d, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": {"source_pin": "p", "format": 1}}) + "\n")
        for rec in FACES:
            f.write(json.dumps(rec) + "\n")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = ("import sys, json; sys.path.insert(0, %r);"
            "from cardguru import families as F;"
            "print(F.digest(F.mine(%r), max_families=10**6))" % (root, str(d)))
    outs = set()
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outs.add(subprocess.run([sys.executable, "-c", code], env=env,
                                capture_output=True, text=True,
                                check=True).stdout)
    assert len(outs) == 1, "digest must not depend on PYTHONHASHSEED"


def test_load_missing_artifact_returns_none(tmp_path):
    assert fam.load(str(tmp_path / "nope.json")) is None


def test_load_corrupt_artifact_returns_none(tmp_path):
    p = tmp_path / "families.json"
    p.write_text("{ not json")
    assert fam.load(str(p)) is None


def test_prompt_degrades_without_the_artifact(monkeypatch):
    from cardguru import nl_compiler

    monkeypatch.setenv("CARDGURU_FAMILIES", "/no/such/families.json")
    assert nl_compiler._family_block() == ""


def test_prompt_families_can_be_switched_off(monkeypatch, tmp_path, mined):
    """The control arm of the A/B. It has to be a switch and not a deleted
    file, because the file is also what `cardguru families` writes."""
    from cardguru import nl_compiler

    p = tmp_path / "families.json"
    p.write_text(json.dumps(mined))
    monkeypatch.setenv("CARDGURU_FAMILIES", str(p))
    assert nl_compiler._family_block() != ""
    monkeypatch.setenv("CARDGURU_FAMILIES", "off")
    assert nl_compiler._family_block() == ""


def test_prompt_tells_the_compiler_what_to_do_with_a_family(tmp_path,
                                                            monkeypatch, mined):
    """A list of names is not actionable on its own — the block has to say the
    shape it wants, or the compiler reads it as vocabulary it already had."""
    from cardguru import nl_compiler

    p = tmp_path / "families.json"
    p.write_text(json.dumps(mined))
    monkeypatch.setenv("CARDGURU_FAMILIES", str(p))
    block = nl_compiler._family_block()
    assert '"any"' in block
    assert "Destroy, DestroyAll" in block


def test_build_writes_and_stamps_size(tmp_path):
    d = tmp_path / "dataset.jsonl.gz"
    with gzip.open(d, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": {"source_pin": "p", "format": 1}}) + "\n")
        for rec in FACES:
            f.write(json.dumps(rec) + "\n")
    out = tmp_path / "families.json"
    got = fam.build(str(d), str(out))
    assert out.exists() and got["_meta"]["bytes"] > 0
    assert json.loads(out.read_text())["families"] == got["families"]
