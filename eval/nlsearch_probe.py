"""Coverage probe for the lexicon-driven NL search (cardguru.nlsearch).

Measures the boundary honestly: attribute-shaped questions it should answer,
and structure-shaped questions it should NOT (those belong to the query DSL
and the ability-graph index). A question "parses" when every non-stopword
token was bound to a facet, a numeric or a negation.

Run: python3 eval/nlsearch_probe.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.nlsearch import GameProfile, build_lexicon, load_corpus, run

# Shape A: named card properties. The lexicon should bind every content word.
ATTRIBUTE = [
    "card in blue that has flash",
    "green creature with trample",
    "legendary human wizard",
    "blue instant that costs 2 or less",
    "red creature with power 4 or more",
    "artifact with equip",
    "cards in white without flying",
    "black or red creature with lifelink",
    "white enchantment",
    "legendary artifact creature",
    "green creature with reach and vigilance",
    "blue or black instant costing 1",
    "creature with deathtouch and lifelink",
    "snow land",
    "elf druid",
    "red sorcery costing 3 or less",
    "zombie with menace",
    "planeswalker in white",
    "creature with ward",
    "colorless artifact with cost 2",
]

# Shape B: card STRUCTURE, not card properties. Expected to fall through —
# these are what the ability-graph DSL exists for.
STRUCTURAL = [
    "creatures that sacrifice a creature as a cost to add mana",
    "cards that double the tokens you create",
    "spells that counter target spell and nothing else",
    "sagas whose chapters put a creature onto the battlefield",
    "cards that let you play lands from your graveyard",
]


def probe(profile_path, corpus_path):
    profile = GameProfile.load(profile_path)
    corpus = load_corpus(corpus_path)
    lex = build_lexicon(corpus, profile)
    out = {"corpus": len(corpus), "lexicon_terms": len(lex.terms),
           "attribute": [], "structural": []}
    for bucket, questions in (("attribute", ATTRIBUTE), ("structural", STRUCTURAL)):
        for q in questions:
            r = run(q, corpus, profile, lex, limit=3)
            out[bucket].append({
                "q": q,
                "reading": r["interpretation"],
                "clean": not r["unparsed"] and not r["low_confidence"],
                "unparsed": r["unparsed"],
                "hits": r["total"],
                "sample": [c["name"] for c in r["results"]],
            })
    return out


if __name__ == "__main__":
    res = probe("profiles/mtg.json", "eval/rulesguru/cards_index.json")
    a = res["attribute"]
    clean = [x for x in a if x["clean"]]
    print(f"corpus {res['corpus']} cards, lexicon {res['lexicon_terms']} terms\n")
    print(f"ATTRIBUTE-shaped: {len(clean)}/{len(a)} fully bound "
          f"({len([x for x in clean if not x['hits']])} bound but 0 hits — a "
          f"correct empty answer is not a parse failure)")
    for x in a:
        flag = "  " if x["clean"] else "!!"
        print(f" {flag} {x['q']}\n       {x['reading']}  [{x['hits']}]"
              + (f"  unparsed={x['unparsed']}" if x["unparsed"] else ""))
    s = res["structural"]
    leaked = [x for x in s if x["clean"] and x["hits"] > 0]
    print(f"\nSTRUCTURE-shaped: {len(s) - len(leaked)}/{len(s)} correctly "
          f"fall through (a 'clean' parse here would be a FALSE CONFIDENCE)")
    for x in s:
        print(f"    {x['q']}\n       {x['reading']}  [{x['hits']}]"
              + (f"  unparsed={x['unparsed']}" if x["unparsed"] else ""))
    with open("eval/nlsearch_probe.json", "w") as f:
        json.dump(res, f, indent=1)
