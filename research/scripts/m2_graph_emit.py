"""M2 probe: emit an oracle-derived ability graph in the CardGuru record shape.

M0 recovered ability kinds; M1 recovered effect APIs. Neither touched the
distinctions the adversarial slice in research/graph-vs-flat-ablation.md turns
on, which are all about *parameters*:

  a01  cost-sacrifice vs effect-sacrifice   -> params.Cost
  a04  {T} as a cost vs 'tap' as an effect  -> params.Cost
  a05  'counter target spell' AND NOTHING MORE -> params.ValidTgts

M2 emits those params in Forge's own vocabulary -- `Sac<1/Creature>`, `T`,
`ValidTgts$ Card` -- so the *identical* compiled queries from the ablation can
run against the oracle-derived graph with no query rewriting. That is a
deliberately strict test: if the grammar had to be met halfway by hand-tuned
queries, the comparison would measure the query author, not the grammar.

Output is a dataset.jsonl.gz in exactly the shape cardguru.dataset.load expects,
so cardguru.index.SearchIndex can consume it unmodified.

Usage:
    python3 research/scripts/m2_graph_emit.py <forge_cards.jsonl.gz> <out.jsonl.gz>
"""
from __future__ import annotations

import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m0_oracle_segment import (  # noqa: E402
    ABILITY_WORD_RE, COST_LEAD_RE, LOYALTY_BRACKET_RE, LOYALTY_RE,
    NAMED_COST_RE, TRIGGER_RE, keyword_tokens, load_keyword_lexicon,
    load_records, oracle_lines,
)
from m1_effect_verbs import PRODUCTIONS, effect_span  # noqa: E402

# --- cost atoms ---------------------------------------------------------------

MANA_SYM_RE = re.compile(r"\{([^}]*)\}")
NUMWORD = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
           "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

SAC_RE = re.compile(
    r"\bsacrifice\s+(?P<n>a|an|one|two|three|\d+|X)?\s*(?P<other>another\s+)?"
    r"(?P<what>[A-Za-z][A-Za-z' ]{0,30}?)(?=$|,|\s*:)", re.I)
DISCARD_RE = re.compile(
    r"\bdiscard\s+(?P<n>a|an|one|two|three|\d+|X)?\s*(?P<what>card|cards|"
    r"[A-Za-z][A-Za-z' ]{0,20}?card)", re.I)
PAYLIFE_RE = re.compile(r"\bpay\s+(?P<n>\d+|X)\s+life\b", re.I)
# 'Sacrifice Viscera Seer' / 'Sacrifice this creature' -> Sac<1/CARDNAME>
SELF_WORDS = re.compile(r"^(this|it)\b", re.I)

TYPE_WORDS = {
    "creature": "Creature", "creatures": "Creature",
    "artifact": "Artifact", "artifacts": "Artifact",
    "enchantment": "Enchantment", "enchantments": "Enchantment",
    "land": "Land", "lands": "Land",
    "permanent": "Permanent", "permanents": "Permanent",
    "planeswalker": "Planeswalker", "card": "Card", "cards": "Card",
    "token": "Token", "goblin": "Goblin", "creature token": "Creature",
}


def _num(tok: str | None) -> str:
    if not tok:
        return "1"
    tok = tok.strip().lower()
    if tok == "x":
        return "X"
    if tok.isdigit():
        return tok
    return str(NUMWORD.get(tok, 1))


def cost_atoms(cost_text: str, card_name: str | None) -> str:
    """Render a cost span into Forge's space-joined atom string."""
    atoms: list[str] = []
    for sym in MANA_SYM_RE.findall(cost_text):
        s = sym.strip().upper()
        if s == "T":
            atoms.append("T")
        elif s == "Q":
            atoms.append("Q")
        else:
            atoms.append(s)
    text = MANA_SYM_RE.sub(" ", cost_text)

    m = LOYALTY_BRACKET_RE.match(cost_text.strip()) or LOYALTY_RE.match(cost_text.strip())
    if m:
        raw = m.group(0).strip("[]: ")
        n = raw.lstrip("+-−–") or "0"
        atoms.append(f"{'SubCounter' if raw[:1] in '-−–' else 'AddCounter'}<{n}/LOYALTY>")

    for sm in SAC_RE.finditer(text):
        what = (sm.group("what") or "").strip().lower()
        n = _num(sm.group("n"))
        if not what:
            continue
        if SELF_WORDS.match(what) or (card_name and card_name.lower().startswith(what[:12])):
            atoms.append("Sac<1/CARDNAME>")
        elif what in TYPE_WORDS:
            t = TYPE_WORDS[what]
            atoms.append(f"Sac<{n}/{t}.Other/another {what}>" if sm.group("other")
                         else f"Sac<{n}/{t}>")

    for dm in DISCARD_RE.finditer(text):
        atoms.append(f"Discard<{_num(dm.group('n'))}/Card>")
    for pm in PAYLIFE_RE.finditer(text):
        atoms.append(f"PayLife<{_num(pm.group('n'))}>")

    # dedupe preserving order
    seen, out = set(), []
    for a in atoms:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return " ".join(out)


# --- target restrictions ------------------------------------------------------

COUNTER_TGT_RE = re.compile(
    r"\bcounters?\s+target\s+(?P<restr>[a-z' ]*?)\bspell\b", re.I)

RESTR_MAP = {
    "": "Card", "creature": "Creature", "noncreature": "Card.nonCreature",
    "instant or sorcery": "Instant,Sorcery", "artifact": "Artifact",
    "enchantment": "Enchantment", "activated or triggered": "Card,Emblem",
}


def counter_targets(effect: str) -> dict:
    m = COUNTER_TGT_RE.search(effect)
    if not m:
        return {}
    restr = re.sub(r"\s+", " ", (m.group("restr") or "")).strip().lower()
    valid = RESTR_MAP.get(restr)
    if valid is None:
        valid = "".join(w.capitalize() for w in restr.split()) or "Card"
    return {"TargetType": "Spell", "ValidTgts": valid}


# --- emit ---------------------------------------------------------------------

def line_apis(effect: str) -> list[str]:
    out: list[str] = []
    for api, rx in PRODUCTIONS:
        if api not in out and rx.search(effect):
            out.append(api)
    return out


def is_activated(line: str) -> bool:
    if LOYALTY_RE.match(line) or LOYALTY_BRACKET_RE.match(line):
        return True
    head, sep, _ = line.partition(":")
    if not sep or len(head) > 80:
        return False
    h = head.strip()
    return bool(COST_LEAD_RE.match(h) or NAMED_COST_RE.match(h))


def cost_span(line: str) -> str:
    if LOYALTY_RE.match(line) or LOYALTY_BRACKET_RE.match(line):
        return line.partition(":")[0]
    return line.partition(":")[0]


def emit_face(rec: dict, lexicon, lower_lex) -> dict:
    types = rec.get("types") or ""
    is_spell = ("Instant" in types) or ("Sorcery" in types)
    name = rec.get("name")
    nodes: list[dict] = []
    edges: list[dict] = []
    nid = 0
    kid = 0

    for raw in oracle_lines(rec.get("oracle") or ""):
        kws = keyword_tokens(raw, lexicon, lower_lex)
        if kws:
            for k in kws:
                nodes.append({"id": f"kw{kid}", "kind": "K", "keyword": k,
                              "args": [], "raw": raw})
                kid += 1
            continue
        line = ABILITY_WORD_RE.sub("", raw, count=1)
        effect = effect_span(raw)
        apis = line_apis(effect)
        if not apis:
            continue

        activated = is_activated(line)
        if TRIGGER_RE.match(line):
            kind, api_kind = "T", None
        elif activated:
            kind, api_kind = "A", "AB"
        elif is_spell:
            kind, api_kind = "A", "SP"
        else:
            kind, api_kind = "S", None

        params: dict = {}
        if activated:
            atoms = cost_atoms(cost_span(line), name)
            if atoms:
                params["Cost"] = atoms
        root_id = None
        for i, api in enumerate(apis):
            node = {"id": f"ab{nid}", "kind": kind if i == 0 else "SVar",
                    "api": api, "params": dict(params) if i == 0 else {}}
            if i == 0:
                if api_kind:
                    node["apiKind"] = api_kind
                node["params"].update(counter_targets(effect))
                root_id = node["id"]
            else:
                node["apiKind"] = "DB"
                node["params"].update(counter_targets(effect))
                edges.append({"src": root_id, "dst": node["id"],
                              "type": "SubAbility"})
            nodes.append(node)
            nid += 1

    out = dict(rec)
    out["nodes"] = nodes
    out["edges"] = edges
    out["derivation"] = "oracle-grammar"
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    lexicon = load_keyword_lexicon()
    lower_lex = {k.lower(): k for k in lexicon}
    n = 0
    opener = gzip.open if argv[2].endswith(".gz") else open
    with opener(argv[2], "wt", encoding="utf-8") as out:
        out.write(json.dumps({"_meta": {"source_pin": "oracle-grammar-m2",
                                        "format": 1}}) + "\n")
        for rec in load_records(argv[1]):
            out.write(json.dumps(emit_face(rec, lexicon, lower_lex)) + "\n")
            n += 1
    print(json.dumps({"faces_emitted": n, "out": argv[2]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
