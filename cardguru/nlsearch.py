"""Natural-language-ish card search, driven by a lexicon mined from the corpus.

The premise: for most card-search questions the user is naming *values that are
printed on the cards* — a domain, a keyword, a type, a cost. Those values are
already enumerable from the card data itself, so the "compiler" does not need a
language model and does not need per-game code. It needs a lexicon.

    build_lexicon(corpus, profile)   every distinct facet value in the corpus
                                     becomes a searchable term, tagged with the
                                     facet it came from
    parse(question, lexicon)         longest-span match over that lexicon, plus
                                     a small closed grammar of connectives
                                     (in/with/without/or/no) and numeric
                                     comparators (costs 2 or less)
    run(query, corpus, profile)      filter + rank

Adding a game is a GameProfile (a JSON description of which fields are facets)
plus a card dump. No new code: point it at Riftbound cards with a `domain` facet
and "Calm" enters the lexicon by itself, the same way "Blue" does for Magic.

Deliberately NOT a graph query compiler. This answers "which cards have these
properties", which is the whole question for attribute-shaped games; questions
about card *structure* (cost-vs-effect, trigger chains) still belong in the
query DSL and its ability-graph index. See plan/no-llm-multigame.md.

Every parse returns its reading — the spans it consumed, the facet it bound
each one to, and a confidence — so a wrong interpretation is visible and
correctable rather than silent.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

# ------------------------------------------------------------------ text utils

WORD_RE = re.compile(r"[a-z0-9'+/-]+")

# Dropped before matching: they carry no facet information in any game.
STOPWORDS = {
    "a", "an", "the", "card", "cards", "show", "find", "me", "all", "any",
    "list", "some", "is", "are", "be", "was", "it", "its", "this", "these",
    "those", "please", "give", "get", "search", "for", "of",
}
# Words that mean "the next term is a value of THIS facet". Facets declare
# their own; these are the game-neutral defaults.
DEFAULT_PREPOSITIONS = {
    "in": None, "with": None, "has": None, "have": None, "having": None,
    "that": None, "which": None, "and": None,
}
NEGATIONS = {"without", "no", "not", "lacking", "lacks", "except", "excluding"}
DISJUNCTION = {"or"}

CMP_PHRASES = [
    (("or", "less"), "<="), (("or", "fewer"), "<="), (("or", "lower"), "<="),
    (("or", "more"), ">="), (("or", "greater"), ">="), (("or", "higher"), ">="),
    (("at", "least"), ">="), (("at", "most"), "<="),
    (("less", "than"), "<"), (("fewer", "than"), "<"), (("lower", "than"), "<"),
    (("more", "than"), ">"), (("greater", "than"), ">"), (("higher", "than"), ">"),
    (("cheaper", "than"), "<"), (("bigger", "than"), ">"),
    (("under",), "<"), (("over",), ">"), (("above",), ">"), (("below",), "<"),
    (("exactly",), "=="), (("equal", "to"), "=="),
]
CMP_SYMBOLS = {"<=": "<=", ">=": ">=", "<": "<", ">": ">", "=": "==", "==": "=="}


def norm(s: str) -> str:
    """Casefold + strip accents, so 'Bíonn' and 'bionn' are one term."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.casefold().strip()


def tokenize(s: str) -> list[str]:
    return WORD_RE.findall(norm(s))


def singularize(tok: str) -> str:
    if len(tok) > 3 and tok.endswith("es") and tok[-3] in "sxz":
        return tok[:-2]
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def stems(tok: str):
    """Surface forms to try for one token: as written, de-pluralized, and with
    a verbal suffix stripped ('costing' -> 'cost'). Cheap, language-specific,
    and enough — facet values are nouns and the connectives are a closed set."""
    seen = {tok}
    yield tok
    for cand in (singularize(tok),
                 tok[:-3] if len(tok) > 5 and tok.endswith("ing") else None,
                 tok[:-2] if len(tok) > 4 and tok.endswith("ed") else None):
        if cand and cand not in seen:
            seen.add(cand)
            yield cand


def _trigrams(s: str) -> set[str]:
    s = f"  {s} "
    return {s[i:i + 3] for i in range(len(s) - 2)}


def similarity(a: str, b: str) -> float:
    """Stdlib-only stand-in for an embedding: catches typos and morphology
    ('ambsh', 'flyng'), not synonymy. Trigram overlap is the cheap prefilter;
    SequenceMatcher does the actual scoring because it is far better at
    transpositions and dropped letters, which is what typos are.

    Real synonymy ('sneaky' -> Ambush) is the profile's `aliases` table, or a
    sentence embedding over these same lexicon entries — either way the
    Lexicon.lookup interface below does not change."""
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    if len(ta & tb) / min(len(ta), len(tb)) < 0.3:
        return 0.0                        # cheap reject before the O(nm) pass
    return difflib.SequenceMatcher(None, a, b).ratio()


FUZZY_FLOOR = 0.87          # below this a fuzzy hit is not offered at all
FUZZY_MAX_LEN_DELTA = 2     # a typo does not change a word's length much

# ------------------------------------------------------------------- profiles


@dataclass
class Facet:
    """One searchable dimension of a card (colors, keywords, domains, ...)."""
    name: str
    field: str
    multi: bool = True                    # field holds a list vs a scalar
    prepositions: tuple[str, ...] = ()    # words that steer a term to this facet
    aliases: dict = field(default_factory=dict)   # user word -> canonical value
    priority: int = 0                     # tie-break when a term fits 2 facets


@dataclass
class Numeric:
    name: str
    field: str
    aliases: tuple[str, ...] = ()


@dataclass
class GameProfile:
    game: str
    id_field: str = "name"
    text_fields: tuple[str, ...] = ("text",)
    facets: tuple[Facet, ...] = ()
    numerics: tuple[Numeric, ...] = ()

    @classmethod
    def from_dict(cls, d: dict) -> "GameProfile":
        facets = []
        for i, (name, spec) in enumerate(d.get("facets", {}).items()):
            facets.append(Facet(
                name=name, field=spec.get("field", name),
                multi=spec.get("multi", True),
                prepositions=tuple(spec.get("prepositions", ())),
                aliases={norm(k): ("" if v is None else v)
                     for k, v in (spec.get("aliases") or {}).items()},
                priority=spec.get("priority", i)))
        numerics = [Numeric(name=n, field=s.get("field", n),
                            aliases=tuple(s.get("aliases", ())))
                    for n, s in (d.get("numerics") or {}).items()]
        return cls(game=d.get("game", "unknown"),
                   id_field=d.get("id_field", "name"),
                   text_fields=tuple(d.get("text_fields", ("text",))),
                   facets=tuple(facets), numerics=tuple(numerics))

    @classmethod
    def load(cls, path: str) -> "GameProfile":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def facet_values(card: dict, facet: Facet) -> list:
    v = card.get(facet.field)
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, (list, tuple, set)) else [v]


# -------------------------------------------------------------------- lexicon


class Lexicon:
    """Normalized term -> [(facet_name, canonical_value, doc_frequency)].

    Built from the corpus, so it is exactly as current as the card data.
    """

    def __init__(self, profile: GameProfile):
        self.profile = profile
        self.terms: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
        self.max_span = 1
        self.prepositions: dict[str, set[str]] = defaultdict(set)
        for f in profile.facets:
            for p in f.prepositions:
                self.prepositions[norm(p)].add(f.name)
        self.numeric_alias: dict[str, str] = {}
        for n in profile.numerics:
            for a in (n.name,) + n.aliases:
                self.numeric_alias[norm(a)] = n.name

    def numeric_for(self, tok: str):
        """Numeric field named by this token, tolerating 'costs'/'costing'."""
        for st in stems(tok):
            if st in self.numeric_alias:
                return self.numeric_alias[st]
        return None

    def _add(self, term: str, facet: str, value, freq: int) -> None:
        term = norm(term)
        if not term:
            return
        for existing in self.terms[term]:
            if existing[0] == facet and existing[1] == value:
                return
        self.terms[term].append((facet, value, freq))
        self.max_span = max(self.max_span, len(term.split()))

    def lookup(self, phrase: str, fuzzy: bool = True):
        """Return (candidates, confidence). Exact first; then singularized;
        then nearest trigram neighbour above the floor."""
        key = norm(phrase)
        if key in self.terms:
            return self.terms[key], 1.0
        for variant in (" ".join(singularize(t) for t in key.split()),
                        " ".join(next(iter(stems(t)), t) for t in key.split())):
            if variant in self.terms:
                return self.terms[variant], 0.95
        if " " not in key:
            for st in stems(key):
                if st in self.terms:
                    return self.terms[st], 0.95
        if not fuzzy or len(key) < 4:
            return [], 0.0
        best, best_score = None, FUZZY_FLOOR
        for term in self.terms:
            if abs(len(term) - len(key)) > FUZZY_MAX_LEN_DELTA:
                continue
            s = similarity(term, key)
            if s > best_score:
                best, best_score = term, s
        if best is None:
            return [], 0.0
        return self.terms[best], round(best_score, 3)


def build_lexicon(corpus, profile: GameProfile) -> Lexicon:
    lex = Lexicon(profile)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for card in corpus:
        for f in profile.facets:
            for v in facet_values(card, f):
                counts[(f.name, str(v))] += 1
    for (facet, value), freq in counts.items():
        lex._add(value, facet, value, freq)
    for f in profile.facets:                      # authored synonyms
        for word, value in f.aliases.items():
            lex._add(word, f.name, value, counts.get((f.name, str(value)), 0))
    return lex


# --------------------------------------------------------------------- parsing


@dataclass
class Clause:
    kind: str                 # "facet" | "numeric" | "text"
    facet: str | None = None
    value: object = None
    op: str = "=="
    negated: bool = False
    span: str = ""
    confidence: float = 1.0
    alternatives: tuple = ()  # other facets the span could have meant

    def describe(self) -> str:
        if self.kind == "facet" and self.value in (None, ""):
            return f'{"NOT " if self.negated else ""}{self.facet} is empty'
        if self.kind == "text":
            return f'{"no " if self.negated else ""}text ~ "{self.value}"'
        neg = "NOT " if self.negated else ""
        if self.kind == "numeric":
            return f"{neg}{self.facet} {self.op} {self.value}"
        s = f"{neg}{self.facet} = {self.value}"
        if self.confidence < 1.0:
            s += f'  (~"{self.span}", {self.confidence})'
        return s


@dataclass
class ParsedQuery:
    clauses: list = field(default_factory=list)   # AND-ed; each may be a list = OR
    unparsed: list = field(default_factory=list)

    def describe(self) -> str:
        parts = []
        for c in self.clauses:
            if isinstance(c, list):
                parts.append("(" + " OR ".join(x.describe() for x in c) + ")")
            else:
                parts.append(c.describe())
        return " AND ".join(parts) if parts else "(everything)"


def _match_comparator(toks: list[str], i: int):
    """Longest comparator phrase starting at i -> (op, consumed)."""
    if toks[i] in CMP_SYMBOLS:
        return CMP_SYMBOLS[toks[i]], 1
    for words, op in sorted(CMP_PHRASES, key=lambda x: -len(x[0])):
        if tuple(toks[i:i + len(words)]) == words:
            return op, len(words)
    return None, 0


def parse(question: str, lex: Lexicon, fuzzy: bool = True) -> ParsedQuery:
    toks = tokenize(question)
    out = ParsedQuery()
    i = 0
    negate_next = False
    steer: set[str] | None = None      # facets a preposition just steered us to
    pending_or = False

    def emit(clause: Clause):
        nonlocal pending_or
        if pending_or and out.clauses:
            prev = out.clauses[-1]
            out.clauses[-1] = (prev if isinstance(prev, list) else [prev]) + [clause]
            pending_or = False
        else:
            out.clauses.append(clause)

    while i < len(toks):
        tok = toks[i]

        if tok in NEGATIONS:
            negate_next = True
            i += 1
            continue
        if tok in DISJUNCTION:
            pending_or = True
            i += 1
            continue
        if tok in lex.prepositions:
            steer = lex.prepositions[tok] or None
            i += 1
            continue
        if tok in DEFAULT_PREPOSITIONS:
            i += 1
            continue

        # numeric: "<alias> <cmp> <n>" or "<cmp> <n> <alias>" or "<alias> <n>"
        numeric_name = lex.numeric_for(tok)
        if numeric_name:
            name = numeric_name
            j = i + 1
            op, used = _match_comparator(toks, j) if j < len(toks) else (None, 0)
            j += used
            if j < len(toks) and toks[j].isdigit():
                n = int(toks[j])
                j += 1
                op2, used2 = _match_comparator(toks, j) if j < len(toks) else (None, 0)
                if op is None and op2 is not None:
                    op, j = op2, j + used2       # "cost 2 or less"
                emit(Clause("numeric", name, n, op or "==", negate_next,
                            " ".join(toks[i:j])))
                negate_next, steer, i = False, None, j
                continue

        if tok.isdigit():                        # "more than 3 power"
            j = i
            op, used = _match_comparator(toks, max(0, i - 2))
            n = int(tok)
            j += 1
            if j < len(toks) and lex.numeric_for(toks[j]):
                emit(Clause("numeric", lex.numeric_for(toks[j]), n,
                            op or "==", negate_next, " ".join(toks[i:j + 1])))
                negate_next, steer, i = False, None, j + 1
                continue

        # Lexicon match. Exact/singular wins at the longest span; fuzzy is
        # tried only on a SINGLE token, because a fuzzy multi-word match
        # silently eats the words next to it ("red creature" ~ "creature"
        # would drop the colour).
        hit = None
        for span_len in range(min(lex.max_span, len(toks) - i), 0, -1):
            phrase = " ".join(toks[i:i + span_len])
            if phrase in STOPWORDS:
                continue
            cands, conf = lex.lookup(phrase, fuzzy=False)
            if cands:
                hit = (cands, conf, span_len, phrase)
                break
        if hit is None and fuzzy and tok not in STOPWORDS:
            cands, conf = lex.lookup(tok, fuzzy=True)
            if cands:
                hit = (cands, conf, 1, tok)
        if hit:
            cands, conf, span_len, phrase = hit
            if steer:
                steered = [c for c in cands if c[0] in steer]
                cands = steered or cands
            prio = {f.name: f.priority for f in lex.profile.facets}
            # most specific reading first: rarest value, then declared priority
            cands = sorted(cands, key=lambda c: (c[2], prio.get(c[0], 99)))
            facet, value, _ = cands[0]
            emit(Clause("facet", facet, value, "==", negate_next, phrase, conf,
                        tuple((c[0], c[1]) for c in cands[1:3])))
            negate_next, steer, i = False, None, i + span_len
            continue

        if tok not in STOPWORDS:
            out.unparsed.append(tok)
            if negate_next:
                emit(Clause("text", None, tok, "==", True, tok))
        negate_next = False
        i += 1

    return out


# ------------------------------------------------------------------ evaluation


def _numeric(card: dict, fieldname: str):
    v = card.get(fieldname)
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _clause_matches(clause: Clause, card: dict, profile: GameProfile) -> bool:
    if clause.kind == "facet":
        facet = next((f for f in profile.facets if f.name == clause.facet), None)
        if facet is None:
            return False
        vals = {norm(v) for v in facet_values(card, facet)}
        if clause.value in (None, ""):
            return not vals            # alias -> null means "has no value here"
        return norm(clause.value) in vals
    if clause.kind == "numeric":
        num = next((n for n in profile.numerics if n.name == clause.facet), None)
        v = _numeric(card, num.field) if num else None
        if v is None:
            return False
        t = clause.value
        return {"==": v == t, "<": v < t, "<=": v <= t,
                ">": v > t, ">=": v >= t}[clause.op]
    blob = " ".join(norm(card.get(f) or "") for f in profile.text_fields)
    return norm(clause.value) in blob


def matches(query: ParsedQuery, card: dict, profile: GameProfile) -> bool:
    for c in query.clauses:
        if isinstance(c, list):
            if not any(_clause_matches(x, card, profile) != x.negated for x in c):
                return False
        elif _clause_matches(c, card, profile) == c.negated:
            return False
    return True


def _text_score(terms: list[str], card: dict, profile: GameProfile) -> float:
    if not terms:
        return 0.0
    name = norm(card.get(profile.id_field) or "")
    blob = " ".join(norm(card.get(f) or "") for f in profile.text_fields)
    score = 0.0
    for t in terms:
        if t in name:
            score += 2.0
        if t in blob:
            score += 1.0
    return score / len(terms)


def run(question: str, corpus, profile: GameProfile, lex: Lexicon | None = None,
        limit: int = 20, fuzzy: bool = True) -> dict:
    """Parse and execute. Returns the reading alongside the results, always."""
    corpus = list(corpus)
    lex = lex or build_lexicon(corpus, profile)
    q = parse(question, lex, fuzzy=fuzzy)
    residual = [t for t in q.unparsed]
    hits = []
    for card in corpus:
        if not matches(q, card, profile):
            continue
        s = _text_score(residual, card, profile)
        if residual and s == 0.0 and q.clauses:
            continue                       # unmatched words must mean something
        hits.append((s, card))
    if residual and not q.clauses:
        hits = [h for h in hits if h[0] > 0]
    hits.sort(key=lambda h: (-h[0], norm(h[1].get(profile.id_field) or "")))
    low = [c for c in q.clauses
           if not isinstance(c, list) and c.kind == "facet" and c.confidence < 1.0]
    return {
        "game": profile.game,
        "question": question,
        "interpretation": q.describe(),
        "clauses": [c.describe() if not isinstance(c, list)
                    else [x.describe() for x in c] for c in q.clauses],
        "unparsed": residual,
        "low_confidence": [{"span": c.span, "read_as": f"{c.facet} = {c.value}",
                            "confidence": c.confidence,
                            "alternatives": [f"{a}={b}" for a, b in c.alternatives]}
                           for c in low],
        "total": len(hits),
        "results": [h[1] for h in hits[:limit]],
    }


# ---------------------------------------------------------------- corpus load

def load_corpus(path: str) -> list[dict]:
    """Accept the three shapes card dumps actually ship in: a JSON list, a
    JSON object keyed by card name, or JSONL. Nothing game-specific here."""
    if path.endswith(".jsonl") or path.endswith(".jsonl.gz"):
        import gzip
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        if "cards" in data and isinstance(data["cards"], (list, dict)):
            data = data["cards"]
    if isinstance(data, dict):
        out = []
        for key, card in data.items():
            if isinstance(card, dict):
                card = dict(card)
                card.setdefault("name", key)
                out.append(card)
        return out
    return [c for c in data if isinstance(c, dict)]
