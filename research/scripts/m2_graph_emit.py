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
from m3_modes_events import (  # noqa: E402
    chain_edge_type, replacement_event, static_mode, trigger_mode,
)

# --- cost atoms ---------------------------------------------------------------

MANA_SYM_RE = re.compile(r"\{([^}]*)\}")
NUMWORD = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
           "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

# The whole sacrifice noun phrase, parsed structurally afterwards rather than
# by one over-clever regex. Stops at the clause end or an 'unless' rider.
SAC_RE = re.compile(
    r"\bsacrifices?\s+(?P<np>[^,:.]+?)(?=$|[,:.]|\s+unless\b)", re.I)
DISCARD_RE = re.compile(
    r"\bdiscard\s+(?P<n>a|an|one|two|three|\d+|X)?\s*(?P<what>card|cards|"
    r"[A-Za-z][A-Za-z' ]{0,20}?card)", re.I)
PAYLIFE_RE = re.compile(r"\bpay\s+(?P<n>\d+|X)\s+life\b", re.I)
# 'Tap two untapped creatures you control' -> tapXType<2/Creature>
TAPX_RE = re.compile(
    r"\btaps?\s+(?P<n>a|an|one|two|three|four|five|\d+|X)\s+untapped\s+"
    r"(?P<what>[A-Za-z][A-Za-z' ]*?)(?:\s+you control)?(?=$|[,:.])", re.I)

MINUS_SIGNS = ("-", "\u2212", "\u2013")
LOYALTY_COST_RE = re.compile(r"^\[?([+\u2212\u2013-]?)(\d+)\]?\s*$")
LEAD_COUNT_RE = re.compile(
    r"^(?P<n>a|an|one|two|three|four|five|\d+|X)\b\s*", re.I)
OTHER_RE = re.compile(r"^(another|other)\b\s*", re.I)
# 'this creature', 'this enchantment', 'this token', 'it'
SELF_PHRASE_RE = re.compile(
    r"^(?:it|this(?:\s+\w+)?)$", re.I)

TYPE_WORDS = {
    "creature": "Creature", "creatures": "Creature",
    "artifact": "Artifact", "artifacts": "Artifact",
    "enchantment": "Enchantment", "enchantments": "Enchantment",
    "land": "Land", "lands": "Land",
    "permanent": "Permanent", "permanents": "Permanent",
    "planeswalker": "Planeswalker", "planeswalkers": "Planeswalker",
    "card": "Card", "cards": "Card", "token": "Token", "tokens": "Token",
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


TRAILING_QUALIFIER_RE = re.compile(
    r"\s+(?:you control|an opponent controls|you own|from your .*)$", re.I)


def _singular(word: str) -> str:
    """'Islands' -> 'Island'. Forge selectors name the singular subtype."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _type_token(part: str) -> tuple[str, list[str]] | None:
    """Map one noun phrase to a (head, qualifiers) Forge type selector.

    Card types are lowercase in oracle text ('a creature'); subtypes are
    capitalised ('a Goblin'). That convention does the disambiguation, which is
    what the old `card_name.startswith(...)` heuristic got wrong.
    """
    part = part.strip()
    if not part:
        return None
    low = part.lower()
    if low in TYPE_WORDS:
        return TYPE_WORDS[low], []
    words = part.split()
    base = words[-1]
    head = TYPE_WORDS.get(base.lower())
    if head:
        # 'suspected creature', 'another colorless creature'
        quals = [w.capitalize() for w in words[:-1]
                 if w.lower() not in ("a", "an", "the")]
        return head, quals
    if base[:1].isupper():          # bare subtype: Goblin, Eldrazi, Sliver
        return _singular(base), []
    return None


def parse_sac_np(np: str, card_name: str | None) -> str | None:
    """Parse the noun phrase after 'Sacrifice' into a Sac<...> cost atom."""
    np = TRAILING_QUALIFIER_RE.sub("", np.strip()).strip()
    if not np:
        return None

    m = LEAD_COUNT_RE.match(np)
    n = _num(m.group("n")) if m else "1"
    rest = np[m.end():] if m else np

    om = OTHER_RE.match(rest)
    other = bool(om)
    if om:
        rest = rest[om.end():]
    rest = rest.strip()
    if not rest:
        return None

    # self-sacrifice: 'Sacrifice Viscera Seer', 'Sacrifice this creature'
    names = set()
    if card_name:
        names.add(card_name.lower())
        names.add(card_name.split(",")[0].strip().lower())
    if rest.lower() in names or SELF_PHRASE_RE.match(rest):
        return "Sac<1/CARDNAME>"

    parts = [p for p in re.split(r"\s+or\s+|\s*,\s*|\s+and/or\s+", rest) if p.strip()]
    parsed = [t for t in (_type_token(p) for p in parts) if t]
    if not parsed:
        return None
    # Forge conjoins qualifiers with '+': Creature.Colorless+Other
    tokens = []
    for head, quals in parsed:
        q = list(quals) + (["Other"] if other else [])
        tokens.append(f"{head}.{'+'.join(q)}" if q else head)
    if other:
        return f"Sac<{n}/{';'.join(tokens)}/another {rest}>"
    return f"Sac<{n}/{';'.join(tokens)}>"


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

    # Loyalty costs arrive here WITHOUT their colon -- cost_span() has already
    # split on it -- so match the bare '[+1]' / '-2' form. Anchoring on the
    # colon here meant planeswalker costs never emitted a LOYALTY atom at all.
    lm = LOYALTY_COST_RE.match(cost_text.strip())
    if lm:
        sign, n = lm.group(1), lm.group(2)
        kind = "SubCounter" if sign in MINUS_SIGNS else "AddCounter"
        atoms.append(f"{kind}<{n}/LOYALTY>")

    for sm in SAC_RE.finditer(text):
        atom = parse_sac_np(sm.group("np") or "", card_name)
        if atom:
            atoms.append(atom)

    for tm in TAPX_RE.finditer(text):
        tok = _type_token((tm.group("what") or "").strip())
        if tok:
            head, quals = tok
            sel = f"{head}.{'+'.join(quals)}" if quals else head
            atoms.append(f"tapXType<{_num(tm.group('n'))}/{sel}>")

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
    r"\bcounters?\s+target\s+(?P<pre>[a-z' ]*?)\bspell\b(?P<post>[^.]*)", re.I)

RESTR_MAP = {
    "": "Card", "creature": "Creature", "noncreature": "Card.nonCreature",
    "instant or sorcery": "Instant,Sorcery", "artifact": "Artifact",
    "enchantment": "Enchantment", "activated or triggered": "Card,Emblem",
}

# 'unless its controller pays {2}' is an UnlessCost, not a targeting
# restriction -- Mana Leak still counters any kind of spell.
UNLESS_RE = re.compile(r"\bunless\b.*$", re.I | re.S)
CONTINUATION_RE = re.compile(r"\s*,\s*(?:then|and)\b.*$", re.I | re.S)
CMC_LE_RE = re.compile(r"\bmana value (\d+|X) or less\b", re.I)
CMC_GE_RE = re.compile(r"\bmana value (\d+|X) or greater\b", re.I)
YOU_DONT_RE = re.compile(r"\byou don'?t control\b", re.I)
OPP_CTRL_RE = re.compile(r"\ban opponent controls\b", re.I)
ABILITY_TGT_RE = re.compile(r"\b(?:activated|triggered) ability\b", re.I)
POST_NOISE_RE = re.compile(r"^[\s,;]*(?:(?:or|and)[\s,;]*)*$", re.I)


def counter_targets(effect: str) -> dict:
    m = COUNTER_TGT_RE.search(effect)
    if not m:
        return {}
    pre = re.sub(r"\s+", " ", (m.group("pre") or "")).strip().lower()
    valid = RESTR_MAP.get(pre)
    if valid is None:
        valid = "".join(w.capitalize() for w in pre.split()) or "Card"

    post = UNLESS_RE.sub("", m.group("post") or "")
    # ", then proliferate" / ", and draw a card" continue the spell,
    # they do not restrict what it may target.
    post = CONTINUATION_RE.sub("", post)
    target_type = "Spell"
    if ABILITY_TGT_RE.search(post):
        target_type = "Spell,Activated,Triggered"
        valid = "Card,Emblem"
        post = ABILITY_TGT_RE.sub("", post)

    # Post-nominal restrictions. Fail CLOSED: anything left over that is not
    # recognised still marks the target as restricted, because emitting a bare
    # 'Card' would assert the spell counters ANYTHING. That is the Disdainful
    # Stroke failure -- cardguru/answers.py reads ValidTgts as a stack
    # restriction (cmc gates), so a false 'unrestricted' is a
    # confidently-wrong answer, not just a ranking error.
    if (cm := CMC_LE_RE.search(post)):
        valid += f".cmcLE{cm.group(1)}"
    elif (cm := CMC_GE_RE.search(post)):
        valid += f".cmcGE{cm.group(1)}"
    elif YOU_DONT_RE.search(post):
        valid += ".YouDontCtrl"
    elif OPP_CTRL_RE.search(post):
        valid += ".OppCtrl"
    elif not POST_NOISE_RE.match(post):
        valid += ".restricted"
    return {"TargetType": target_type, "ValidTgts": valid}


# --- emit ---------------------------------------------------------------------

def line_apis(effect: str) -> list[str]:
    """APIs in the order they appear in the *text*, not in PRODUCTIONS order.

    Ordering by production-list position made the first-declared API the
    ability root: 'Counter target spell. You gain 3 life.' rooted at GainLife
    with Counter demoted to a sub-ability, so any query asking for an SP-kind
    Counter node missed the card.
    """
    first_at: dict[str, int] = {}
    for api, rx in PRODUCTIONS:
        m = rx.search(effect)
        if m and (api not in first_at or m.start() < first_at[api]):
            first_at[api] = m.start()
    return sorted(first_at, key=lambda a: (first_at[a], a))


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
        activated = is_activated(line)
        if not apis:
            # The ability exists even when no production names its effect.
            # Dropping the line entirely also dropped its cost and its mode,
            # which is what made cost-shaped queries miss cards whose effect
            # verb happens to be outside the lexicon, and left static
            # abilities almost entirely unrepresented. Emit an api-less node.
            apis = [None]
        # M3: ability kind now distinguishes replacement effects, and each kind
        # carries its Forge mode/event vocabulary.
        rep = None if (is_spell or activated) else replacement_event(line)
        if TRIGGER_RE.match(line):
            kind, api_kind = "T", None
        elif activated:
            kind, api_kind = "A", "AB"
        elif is_spell:
            kind, api_kind = "A", "SP"
        elif rep:
            kind, api_kind = "R", None
        else:
            kind, api_kind = "S", None

        node_mode = None
        params: dict = {}
        if kind == "T":
            node_mode = trigger_mode(line)
        elif kind == "R":
            params["Event"] = rep[0]
            params.update(rep[1])
        elif kind == "S":
            node_mode, sp = static_mode(line)
            params.update(sp)
        if activated:
            atoms = cost_atoms(cost_span(line), name)
            if atoms:
                params["Cost"] = atoms
        root_id = None
        for i, api in enumerate(apis):
            node = {"id": f"ab{nid}", "kind": kind if i == 0 else "SVar",
                    "params": dict(params) if i == 0 else {}}
            if api is not None:
                node["api"] = api
            # Target restrictions belong to the Counter node itself, not to
            # whatever else the same sentence happens to do.
            if api == "Counter":
                node["params"].update(counter_targets(effect))
            if i == 0:
                if api_kind:
                    node["apiKind"] = api_kind
                if node_mode:
                    node["mode"] = node_mode
                root_id = node["id"]
            else:
                node["apiKind"] = "DB"
                edges.append({"src": root_id, "dst": node["id"],
                              "type": chain_edge_type(effect, kind == "R")})
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
