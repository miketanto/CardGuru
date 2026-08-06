import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.forge_parser import _parse_face, parse_keyword, parse_params  # noqa: E402

RAGAVAN = textwrap.dedent("""\
    Name:Ragavan, Nimble Pilferer
    ManaCost:R
    Types:Legendary Creature Monkey Pirate
    PT:2/1
    T:Mode$ DamageDone | ValidSource$ Card.Self | ValidTarget$ Player | CombatDamage$ True | Execute$ TrigTreasure | TriggerDescription$ Whenever CARDNAME deals combat damage to a player, create a Treasure token and exile the top card of that player's library.
    SVar:TrigTreasure:DB$ Token | TokenScript$ c_a_treasure_sac | TokenOwner$ You | SubAbility$ TrigExile
    SVar:TrigExile:DB$ Dig | Defined$ TriggeredTarget | DigNum$ 1 | ChangeNum$ All | DestinationZone$ Exile | RememberChanged$ True | SubAbility$ DBEffect
    SVar:DBEffect:DB$ Effect | StaticAbilities$ STPlay | ForgetOnMoved$ Exile | RememberObjects$ Remembered | SubAbility$ DBCleanup
    SVar:STPlay:Mode$ Continuous | MayPlay$ True | Affected$ Card.IsRemembered+nonLand | AffectedZone$ Exile | Description$ Until end of turn, you may cast that card.
    SVar:DBCleanup:DB$ Cleanup | ClearRemembered$ True
    K:Dash:1 R
    Oracle:Whenever Ragavan...
""").splitlines()

URZAS_SAGA = textwrap.dedent("""\
    Name:Urza's Saga
    ManaCost:no cost
    Types:Enchantment Land Urza's Saga
    K:Chapter:3:Animate1,Animate2,Tutor
    SVar:Animate1:DB$ Animate | Defined$ Self | Abilities$ ABMana | Duration$ Permanent
    SVar:ABMana:AB$ Mana | Cost$ T | Produced$ C
    SVar:Animate2:DB$ Animate | Defined$ Self | Abilities$ ABToken | Duration$ Permanent
    SVar:ABToken:AB$ Token | Cost$ 2 T | TokenScript$ c_0_0_a_construct_total_artifacts
    SVar:Tutor:DB$ ChangeZone | Origin$ Library | Destination$ Battlefield | ChangeType$ Artifact.ManaCost0,Artifact.ManaCost1 | ChangeNum$ 1
    Oracle:...
""").splitlines()

RANGER_CLASS = textwrap.dedent("""\
    Name:Ranger Class
    ManaCost:1 G
    Types:Enchantment Class
    T:Mode$ ChangesZone | Origin$ Any | Destination$ Battlefield | ValidCard$ Card.Self | Execute$ TrigToken
    SVar:TrigToken:DB$ Token | TokenScript$ g_2_2_wolf | TokenOwner$ You
    K:Class:2:1 G:AddTrigger$ TriggerAttackersDeclared
    SVar:TriggerAttackersDeclared:Mode$ AttackersDeclared | AttackingPlayer$ You | Execute$ TrigPutCounter
    SVar:TrigPutCounter:DB$ PutCounter | ValidTgts$ Creature.attacking | CounterType$ P1P1 | CounterNum$ 1
    K:Class:3:3 G:AddStaticAbility$ SMayLook & SMayPlay
    SVar:SMayLook:Mode$ Continuous | Affected$ Card.TopLibrary+YouCtrl | MayLookAt$ You
    SVar:SMayPlay:Mode$ Continuous | Affected$ Creature.nonLand+TopLibrary+YouCtrl | MayPlay$ True
    Oracle:...
""").splitlines()


def edges_of(face, etype=None):
    return [(e["src"], e["dst"], e["type"]) for e in face.edges
            if etype is None or e["type"] == etype]


def test_parse_params():
    p = parse_params("SP$ DealDamage | Cost$ R | NumDmg$ 2 | Flag")
    assert p["SP"] == "DealDamage" and p["Cost"] == "R" and p["Flag"] is True


def test_parse_keyword_args():
    k = parse_keyword("Class:2:1 G:AddTrigger$ X")
    assert k["name"] == "Class" and k["args"] == ["2", "1 G", "AddTrigger$ X"]


def test_ragavan_graph():
    face = _parse_face(RAGAVAN, "r/ragavan.txt", 0)
    ids = {n["id"] for n in face.nodes}
    assert {"ab0", "TrigTreasure", "TrigExile", "DBEffect", "STPlay", "DBCleanup", "kw0"} <= ids
    assert ("ab0", "TrigTreasure", "Execute") in edges_of(face)
    assert ("TrigTreasure", "TrigExile", "SubAbility") in edges_of(face)
    assert ("DBEffect", "STPlay", "StaticAbilities") in edges_of(face)
    trig = next(n for n in face.nodes if n["id"] == "ab0")
    assert trig["kind"] == "T" and trig["mode"] == "DamageDone"
    kw = next(n for n in face.nodes if n["id"] == "kw0")
    assert kw["keyword"] == "Dash" and kw["args"] == ["1 R"]


def test_saga_chapter_edges():
    face = _parse_face(URZAS_SAGA, "u/urzas_saga.txt", 0)
    chapter_edges = edges_of(face, "Chapter")
    assert ("kw0", "Animate1", "Chapter") in chapter_edges
    assert ("kw0", "Animate2", "Chapter") in chapter_edges
    assert ("kw0", "Tutor", "Chapter") in chapter_edges
    # Animate -> granted ability edges via Abilities$
    assert ("Animate1", "ABMana", "Abilities") in edges_of(face)


def test_class_level_edges():
    face = _parse_face(RANGER_CLASS, "r/ranger_class.txt", 0)
    assert ("kw0", "TriggerAttackersDeclared", "AddTrigger") in edges_of(face)
    assert ("kw1", "SMayLook", "AddStaticAbility") in edges_of(face)
    assert ("kw1", "SMayPlay", "AddStaticAbility") in edges_of(face)
    # SVar-defined trigger chains onward
    assert ("TriggerAttackersDeclared", "TrigPutCounter", "Execute") in edges_of(face)
