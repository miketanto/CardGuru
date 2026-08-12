"""Phase 5 M3: build + verify the 28 extra training decks.

Pipeline:
1. Scan Mage.Sets set files for SetCardInfo -> card name -> [SET:num]
   (implementability ground truth at the pin).
2. Scan card classes for mana cost + types (curve/color sanity).
3. Emit .dck files for the curated archetype lists below; hard-fail on
   any card that is not implemented or has no set printing.
4. Cross-check every nonland card exists in rl/e2_features.tsv (the E2
   arm needs features for every pool card).

Deck design constraints (novelty sweep, not a metagame): 60 cards,
24 basic lands (mono) / 24 with duals-as-basics avoided, 36 spells as
4x9 distinct cards, choice-light to moderately interactive, all mono-
color or allied two-color with basics only - deck POWER is not the
variable under test, deck IDENTITY is.

Run: python3 rl/m3_decks.py [--outdir /home/user/mage/Mage.Tests]
     (also writes copies to rl/m3_decks/)
"""
import argparse
import glob
import os
import re
import sys

SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
CARDS_DIR = "/home/user/mage/Mage.Sets/src/mage/cards"
FEATURES = "/home/user/CardGuru/rl/e2_features.tsv"

# set code from the set file's constructor: super("Name", "CODE", ...)
SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')

BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest"}

# ---------------------------------------------------------------- decks
# name -> (basic land spread, [9 spells, 4x each])
DECKS = {
    # --- mono-white aggro/lifegain family
    "M3WhiteWeenie": ({"Plains": 24}, [
        "Savannah Lions", "Elite Vanguard", "Ajani's Pridemate",
        "Attended Knight", "Silverchase Fox", "Pacifism",
        "Divine Favor", "Serra Angel", "Pillarfield Ox"]),
    "M3WhiteSkies": ({"Plains": 24}, [
        "Suntail Hawk", "Concordia Pegasus", "Aven Sentry",
        "Shining Aerosaur", "Angelic Wall", "Divine Verdict",
        "Pacifism", "Inspired Charge", "Serra Angel"]),
    # --- mono-blue tempo/skies
    "M3BlueSkies": ({"Island": 24}, [
        "Cloudkin Seer", "Wind Drake", "Snapping Drake",
        "Phantom Warrior", "Frost Lynx", "Unsummon",
        "Essence Scatter", "Divination", "Air Elemental"]),
    "M3BlueControlLite": ({"Island": 24}, [
        "Omenspeaker", "Wall of Frost", "Murmuring Mystic",
        "Cancel", "Unsummon", "Anticipate",
        "Divination", "Frilled Sea Serpent", "Windreader Sphinx"]),
    # --- mono-black attrition
    "M3BlackAttrition": ({"Swamp": 24}, [
        "Typhoid Rats", "Child of Night", "Nightmare",
        "Gravedigger", "Murder", "Doom Blade",
        "Mind Rot", "Sign in Blood", "Sengir Vampire"]),
    "M3BlackAggro": ({"Swamp": 24}, [
        "Diregraf Ghoul", "Vampire Lacerator", "Walking Corpse",
        "Vampire Nighthawk", "Bone Splinters", "Duress",
        "Lazotep Reaver", "Spark Reaper", "Gray Merchant of Asphodel"]),
    # --- mono-red burn/aggro (distinct from BenchBurn cards)
    "M3RedRush": ({"Mountain": 24}, [
        "Raging Goblin", "Goblin Piker", "Ember Beast",
        "Krenko's Command", "Act of Treason", "Trumpet Blast",
        "Volcanic Hammer", "Canyon Minotaur", "Shivan Dragon"]),
    "M3RedSpells": ({"Mountain": 24}, [
        "Firebrand Archer", "Kiln Fiend", "Spellgorger Weird",
        "Flame Jab", "Needle Drop", "Searing Spear",
        "Magma Jet", "Chandra's Outrage", "Guttersnipe"]),
    # --- mono-green stompy (distinct from BenchMidrange cards)
    "M3GreenStompy": ({"Forest": 24}, [
        "Elvish Mystic", "Kalonian Tusker", "Leatherback Baloth",
        "Garruk's Companion", "Pelakka Wurm", "Rampant Growth",
        "Hunter's Ambush", "Terra Stomper", "Oakenform"]),
    "M3GreenRamp": ({"Forest": 24}, [
        "Arbor Elf", "Voyaging Satyr", "Farseek",
        "Cultivate", "Nissa's Pilgrimage", "Ulvenwald Hydra",
        "Colossal Dreadmaw", "Enlarge", "Craterhoof Behemoth"]),
    # --- allied pairs, 12+12 basics
    "M3AzoriusFliers": ({"Plains": 12, "Island": 12}, [
        "Suntail Hawk", "Wind Drake", "Warden of Evos Isle",
        "Aven Fisher", "Pacifism", "Unsummon",
        "Divination", "Serra Angel", "Air Elemental"]),
    "M3DimirMill": ({"Island": 12, "Swamp": 12}, [
        "Wight of Precinct Six", "Hedron Crab", "Mind Sculpt",
        "Tome Scour", "Doom Blade", "Cancel",
        "Divination", "Nemesis of Reason", "Consuming Aberration"]),
    "M3RakdosSac": ({"Swamp": 12, "Mountain": 12}, [
        "Footlight Fiend", "Fireblade Artist", "Spawn of Mayhem",
        "Bone Splinters", "Lightning Strike", "Rix Maadi Reveler",
        "Judith, the Scourge Diva", "Cackling Fiend", "Act of Treason"]),
    "M3GruulBeats": ({"Mountain": 12, "Forest": 12}, [
        "Zhur-Taa Goblin", "Burning-Tree Emissary", "Ghor-Clan Rampager",
        "Skarrgan Firebird", "Colossal Dreadmaw", "Searing Spear",
        "Giant Growth", "Gruul Spellbreaker", "Nylea's Disciple"]),
    "M3SelesnyaTokens": ({"Forest": 12, "Plains": 12}, [
        "Raise the Alarm", "Call of the Conclave", "Attended Knight",
        "Centaur's Herald", "Rootborn Defenses", "Common Bond",
        "Pacifism", "Wayfaring Temple", "Armada Wurm"]),
    # --- second wave, different mechanics per color
    "M3WhiteEquip": ({"Plains": 24}, [
        "Kor Duelist", "Glory Seeker", "Kitesail Apprentice",
        "Trusty Machete", "Bonesplitter", "Vulshok Morningstar",
        "Kor Outfitter", "Armament Master", "Divine Verdict"]),
    "M3BlueArtifacts": ({"Island": 24}, [
        "Etherium Sculptor", "Vedalken Certarch", "Riddlesmith",
        "Frogmite", "Somber Hoverguard", "Thoughtcast",
        "Trinket Mage", "Faerie Mechanist", "Broodstar"]),
    "M3BlackZombies": ({"Swamp": 24}, [
        "Shambling Ghoul", "Diregraf Ghoul", "Highborn Ghoul",
        "Butcher Ghoul", "Ghoulraiser", "Diregraf Captain",
        "Undead Warchief", "Cemetery Reaper", "Death Baron"]),
    "M3RedGoblins": ({"Mountain": 24}, [
        "Goblin Guide", "Foundry Street Denizen", "Goblin Wardriver",
        "Goblin Chieftain", "Goblin King", "Krenko's Command",
        "Dragon Fodder", "Goblin Chariot", "Siege-Gang Commander"]),
    "M3GreenElves": ({"Forest": 24}, [
        "Llanowar Elves", "Elvish Visionary", "Elvish Archdruid",
        "Imperious Perfect", "Sylvan Messenger", "Wellwisher",
        "Elvish Warmaster", "Elvish Vanguard", "Joraga Warcaller"]),
    # --- third wave, simple tribal/keyword variety
    "M3WhiteSoldiers": ({"Plains": 24}, [
        "Elite Vanguard", "Veteran Armorsmith", "Veteran Swordsmith",
        "Field Marshal", "Catapult Squad", "Raise the Alarm",
        "Captain of the Watch", "Assault Griffin", "Pacifism"]),
    "M3BlueWizards": ({"Island": 24}, [
        "Merfolk Trickster", "Naban, Dean of Iteration", "Vodalian Arcanist",
        "Wizard's Retort", "Watertrap Weaver", "Sage of Lat-Nam",
        "Naru Meha, Master Wizard", "Divination", "Snapping Drake"]),
    "M3BlackRats": ({"Swamp": 24}, [
        "Typhoid Rats", "Ravenous Rats", "Drainpipe Vermin",
        "Rancid Rats", "Crypt Rats", "Nezumi Cutthroat",
        "Gnat Miser", "Chittering Rats", "Murder"]),
    "M3RedDragons": ({"Mountain": 24}, [
        "Dragon Hatchling", "Dragon Fodder", "Seismic Stomp",
        "Dragonlord's Servant", "Dragon Tempest", "Volcanic Dragon",
        "Shivan Dragon", "Furnace Whelp", "Searing Spear"]),
    "M3GreenSpiders": ({"Forest": 24}, [
        "Blisterpod", "Netcaster Spider", "Giant Spider",
        "Penumbra Spider", "Prey Upon", "Titanic Growth",
        "Stingerfling Spider", "Arachnus Web", "Sentinel Spider"]),
    # --- fourth wave: allied pairs round 2
    "M3OrzhovLife": ({"Plains": 12, "Swamp": 12}, [
        "Vizkopa Guildmage", "Basilica Bell-Haunt", "Child of Night",
        "Ajani's Pridemate", "Murder", "Pacifism",
        "Indulgent Tormentor", "Serra Angel", "Sign in Blood"]),
    "M3IzzetSpells": ({"Island": 12, "Mountain": 12}, [
        "Goblin Electromancer", "Guttersnipe", "Spellgorger Weird",
        "Divination", "Searing Spear", "Unsummon",
        "Cancel", "Ral's Outburst", "Air Elemental"]),
    "M3SimicCounters": ({"Forest": 12, "Island": 12}, [
        "Experiment One", "Pollenbright Druid", "Skatewing Spy",
        "Trollbred Guardian", "Simic Fluxmage", "Titanic Growth",
        "Anticipate", "Bred for the Hunt", "Colossal Dreadmaw"]),
}


def scan_sets():
    info = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        code = m.group(1)
        for name, num in CARD_INFO_RE.findall(text):
            info.setdefault(name, (code, num))
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/home/user/mage/Mage.Tests")
    args = ap.parse_args()

    info = scan_sets()
    feats = set()
    with open(FEATURES) as f:
        f.readline()
        for line in f:
            feats.add(line.split("\t", 1)[0])

    missing = []
    os.makedirs("/home/user/CardGuru/rl/m3_decks", exist_ok=True)
    for deck, (lands, spells) in DECKS.items():
        assert len(spells) == 9, f"{deck}: needs exactly 9 spells"
        assert sum(lands.values()) == 24, f"{deck}: needs 24 lands"
        lines = [f"NAME:{deck}"]
        for name in spells:
            if name not in info:
                missing.append(f"{deck}: {name} NOT IMPLEMENTED")
                continue
            if name not in feats:
                missing.append(f"{deck}: {name} not in e2_features.tsv")
            code, num = info[name]
            lines.append(f"4 [{code}:{num}] {name}")
        for basic, n in lands.items():
            code, num = info[basic]
            lines.append(f"{n} [{code}:{num}] {basic}")
        content = "\n".join(lines) + "\n"
        for d in (args.outdir, "/home/user/CardGuru/rl/m3_decks"):
            with open(os.path.join(d, deck + ".dck"), "w") as f:
                f.write(content)
    if missing:
        print("MISSING:")
        print("\n".join(missing))
        sys.exit(1)
    print(f"OK: {len(DECKS)} decks written")


if __name__ == "__main__":
    main()
