"""Mine DISJUNCTIVE families: which api/mode names are alternative spellings
of one player-facing concept.

`shapes.py` answers "one mode name is several concepts — which param picks
one?". This is the opposite failure, and the one the A/B keeps losing to: one
concept is several api/mode names, and the compiler picks whichever it thought
of first. `{"api": "Destroy"}` silently drops the 364 `DestroyAll` nodes;
`{"api": "Dig"}` drops `DigUntil`, `PeekAndReveal` and `Discover`. Nothing in
the ontology says those names are related — it is a flat frequency table — so
the compiler has no way to know it just answered a narrower question than the
one it was asked.

A family is derived from two signals that fail in opposite directions, so a
group has to satisfy both:

1. ANCHOR (language). Forge writes a description on most nodes, and it is the
   same sentence a player reads. A word anchors a facet when it is
   *characteristic* of it (on >=30% of its nodes) and *specific* to it
   (>=4x the rate of that word among nodes of the same facet kind, measured
   per token so a verbose facet does not collect "the" and "your").

   Anchoring by language is what stops the classic distributional failure.
   `GainLife` and `LoseLife` have near-identical params, neighbours and card
   contexts; a cosine over any of those merges them, and the first version of
   this module did. Under an anchor they can only meet on a word they share, so
   "gain" selects one side and "lose" the other. They still meet under "life" —
   and that is the honest answer rather than a bug, because a question that
   says only "life" is genuinely ambiguous between the two. The digest carries
   the anchor, so the compiler sees `life: GainLife, LoseLife` next to
   `gain: GainLife` and has what it needs to choose.

2. SUBSTITUTABILITY (structure). Sharing a word is not enough: `Reveal` and
   `RevealHand` share one, and so do the two halves of a reveal chain. Members
   of a family are ALTERNATIVES, so they should appear on the same card no more
   often than chance. The cut is chance itself — a co-occurrence lift of 1 —
   which is why this signal has the decision boundary `near_misses` turned out
   not to have (see `research/execution-feedback.md` §2). Complements sit two
   orders of magnitude above it: the combat-trigger group measures 600x.

Anchors are additionally required to occur in the corpus's ORACLE text. Forge's
descriptions carry template tokens — `CARDNAME`, `EFFECTSOURCE` — that are
frequent, specific, and not words anyone would type into a search box. Oracle
text is the player-facing rendering, so requiring the word to survive there
keeps the anchor vocabulary to things a question can actually contain.

DERIVED, not written. Regenerate whenever the dataset is rebuilt; a new set's
api variants join their family with nobody editing a prompt.
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict

from . import dataset as ds

# Forge writes the player-facing sentence into one of these.
DESC_KEYS = ("SpellDescription", "TriggerDescription", "Description",
             "StackDescription", "AbilityDescription")

MIN_NODES = 20        # a facet below this cannot support a rate estimate
MIN_COVERAGE = 0.30   # the word is on >=30% of the facet's nodes
MIN_LIFT = 4.0        # ...at >=4x its rate among nodes of the same kind
MIN_WORD = 60         # the word occurs this often, so the family generalises
MAX_CO_LIFT = 3.0     # members co-occur on a card at most this far above chance
MERGE_JACCARD = 0.6   # families this similar are one family under two anchors

_WORD = re.compile(r"[a-z]+")


def _words(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if len(w) > 2]


def _facets(node: dict):
    """(kind, name) for every facet a node exposes. Mirrors shapes.py."""
    p = node.get("params") or {}
    out = []
    mode = p.get("Mode") or node.get("mode")
    if mode:
        out.append(("mode", mode))
    if node.get("api"):
        out.append(("api", node["api"]))
    return out


class _Counts:
    """One pass over the dataset, collecting everything both signals need."""

    def __init__(self):
        self.nodes = Counter()                    # facet -> nodes
        self.coverage = defaultdict(Counter)      # facet -> word -> nodes with it
        self.tokens = defaultdict(Counter)        # facet -> word -> token count
        self.kind_tokens = defaultdict(Counter)   # kind  -> word -> token count
        self.kind_total = Counter()               # kind  -> total tokens
        self.oracle = Counter()                   # word  -> cards whose oracle has it
        self.cards = Counter()                    # facet -> cards carrying it
        self.together = defaultdict(Counter)      # facet -> facet -> shared cards
        self.n_cards = 0

    def add(self, rec: dict):
        self.n_cards += 1
        self.oracle.update(set(_words(str(rec.get("oracle") or ""))))
        present = set()
        for node in rec.get("nodes") or []:
            p = node.get("params") or {}
            toks = _words(" ".join(str(p.get(k, "")) for k in DESC_KEYS))
            uniq = set(toks)
            for f in _facets(node):
                self.nodes[f] += 1
                self.tokens[f].update(toks)
                self.kind_tokens[f[0]].update(toks)
                self.kind_total[f[0]] += len(toks)
                for w in uniq:
                    self.coverage[f][w] += 1
                present.add(f)
        for f in present:
            self.cards[f] += 1
        for a in present:
            for b in present:
                if a != b:
                    self.together[a][b] += 1

    # -- signal 2 ---------------------------------------------------------
    def co_lift(self, a, b) -> float:
        """Cards carrying both facets, over what independence predicts.

        1.0 is chance. Substitutes land at or below it because a card that
        destroys one creature does not usually also destroy all of them;
        complements — the two ends of a chain — land far above.
        """
        expected = self.cards[a] * self.cards[b] / (self.n_cards or 1)
        return self.together[a][b] / expected if expected else 0.0


def _anchors(c: _Counts, keep: list) -> dict:
    """(word, kind) -> {facets it anchors}."""
    out = defaultdict(set)
    for f in keep:
        kind, total = f[0], c.nodes[f]
        facet_tokens = sum(c.tokens[f].values()) or 1
        for word, seen in c.coverage[f].items():
            if seen / total < MIN_COVERAGE:
                continue
            # Frequent enough to generalise, and a word players actually see.
            if c.kind_tokens[kind].get(word, 0) < MIN_WORD:
                continue
            if c.oracle.get(word, 0) < MIN_WORD:
                continue
            rate = c.tokens[f][word] / facet_tokens
            background = c.kind_tokens[kind][word] / (c.kind_total[kind] or 1)
            if background and rate / background >= MIN_LIFT:
                out[(word, kind)].add(f)
    return out


def _peel(c: _Counts, members) -> list:
    """Drop members until every surviving pair co-occurs at ~chance.

    Greedy on the worst offender, because one complement dragged in by a shared
    word (Reveal alongside RevealHand) should cost that member and not the
    family.

    A pair over the cut implicates BOTH its members equally, so the greedy step
    is a tie by construction and the tie-break decides which one leaves. Break
    it toward the rarer facet: the family is named for a concept its
    high-volume members carry, and a rare api that co-occurs with a common one
    is the rider. Breaking it arbitrarily instead dropped `Untap` (480 nodes)
    rather than `TapOrUntap` (50) from the [untap] family over a single pair at
    3.07 — discarding the member the family is about.

    Every ordering here is explicit. Iterating a set of facet tuples orders by
    string hash, which varies per interpreter run, and these ties were frequent
    enough to change the mined family COUNT between runs of the same command
    (89/90/91). A mined artifact that differs from itself cannot be diffed
    against a Forge bump, and silently voids any A/B that regenerates it
    between arms.
    """
    m = sorted(members)
    while len(m) >= 2:
        def worst_pair(f):
            return max(c.co_lift(f, g) for g in m if g != f)
        # highest co-lift first; among equals the rarer facet; then the name,
        # so nothing is left to set ordering.
        worst = max(m, key=lambda f: (worst_pair(f), -c.nodes[f], f))
        if worst_pair(worst) <= MAX_CO_LIFT:
            break
        m.remove(worst)
    return m


def _merge(groups: dict) -> list:
    """Fold families whose members mostly agree into one, keeping both anchors.

    "top" and "library" select the same look-at-your-deck group give or take a
    member; emitting both as separate lines spends prompt budget to say one
    thing twice.
    """
    items = [(kind, set(ms), sorted(words))
             for (kind, ms), words in groups.items()]
    # Largest first so a big family absorbs its near-duplicates rather than the
    # other way round; then a total order on the rest, so runs agree (see the
    # note in _peel).
    items.sort(key=lambda t: (-len(t[1]), t[0], sorted(t[1]), t[2]))
    merged: list = []
    for kind, ms, words in items:
        for i, (k2, ms2, w2) in enumerate(merged):
            if k2 != kind:
                continue
            j = len(ms & ms2) / len(ms | ms2)
            if j >= MERGE_JACCARD:
                merged[i] = (k2, ms2 | ms, sorted(set(w2) | set(words)))
                break
        else:
            merged.append((kind, ms, words))
    return merged


def mine(dataset_path: str) -> dict:
    meta, records = ds.load(dataset_path)
    c = _Counts()
    for rec in records:
        c.add(rec)

    keep = sorted(f for f, n in c.nodes.items() if n >= MIN_NODES)
    anchors_by_word = _anchors(c, keep)
    groups = defaultdict(list)
    for word, kind in sorted(anchors_by_word):
        members = anchors_by_word[(word, kind)]
        if len(members) < 2:
            continue
        survivors = _peel(c, members)
        if len(survivors) >= 2:
            groups[(kind, frozenset(survivors))].append(word)

    families = []
    for kind, members, anchors in _merge(groups):
        ordered = sorted(members, key=lambda f: (-c.nodes[f], f))
        pairs = [(a, b) for i, a in enumerate(ordered) for b in ordered[i + 1:]]
        volume = sum(c.nodes[f] for f in ordered)
        # Rarest anchor in oracle text. "destroy" is on 5% of cards and "may"
        # on 21%: both pass the anchor test, but only one of them is what a
        # question is about. Weighting by it costs nothing when the digest is
        # untruncated and decides what survives when it is.
        idf = max(math.log(c.n_cards / c.oracle[w]) for w in anchors)
        families.append({
            "kind": kind,
            "anchors": anchors,
            "members": [{"name": n, "nodes": c.nodes[(kind, n)]}
                        for _k, n in ordered],
            "volume": volume,
            "anchor_idf": round(idf, 2),
            "rank_score": round(volume * idf, 1),
            "max_co_lift": round(max(c.co_lift(a, b) for a, b in pairs), 2),
        })
    families.sort(key=lambda f: (-f["rank_score"], f["kind"], f["anchors"]))

    return {
        "families": families,
        "_meta": {
            "forge_pin": meta.get("source_pin"),
            "cards": c.n_cards,
            "facets_considered": len(keep),
            "families": len(families),
            "params": {"min_nodes": MIN_NODES, "min_coverage": MIN_COVERAGE,
                       "min_lift": MIN_LIFT, "min_word": MIN_WORD,
                       "max_co_lift": MAX_CO_LIFT,
                       "merge_jaccard": MERGE_JACCARD},
            "note": "Derived from the dataset. Regenerate on every Forge bump; "
                    "never hand-edit.",
        },
    }


def render(fams: dict, kind: str = None) -> list[str]:
    lines = []
    for f in fams.get("families", []):
        if kind and f["kind"] != kind:
            continue
        members = ", ".join(f"{m['name']}({m['nodes']})" for m in f["members"])
        lines.append(f"{f['kind']:4} [{'/'.join(f['anchors'])}]  co={f['max_co_lift']:.1f}"
                     f"  idf={f['anchor_idf']:.1f}  {members}")
    return lines


def digest(fams: dict, max_families: int = 50) -> str:
    """Prompt-sized rendering: anchors, then the names to disjoin over.

    Node counts are dropped — the compiler does not choose between members, it
    is being told to take all of them — but the ordering is by volume so a
    truncated digest keeps the families that cover the most cards.
    """
    lines = []
    for f in fams.get("families", [])[:max_families]:
        names = ", ".join(m["name"] for m in f["members"])
        lines.append(f"{f['kind']} {'/'.join(f['anchors'])}: {names}")
    return "\n".join(lines)


def load(path: str = "data/families.json") -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def build(dataset_path: str, out_path: str) -> dict:
    fams = mine(dataset_path)
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fams, f, indent=1, ensure_ascii=False)
        f.write("\n")
    fams["_meta"]["bytes"] = os.path.getsize(out_path)
    return fams
