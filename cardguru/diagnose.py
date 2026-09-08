"""Explain why a query returned nothing.

A query that returns 0 cards is the least informative possible answer: the
question could be unanswerable, the query could be wrong, or one clause out of
five could be silently zeroing an otherwise-good query. That last case is the
common one and is invisible without help — inside an `all`, a single zero-hit
branch forces the whole result to zero no matter how good the rest is.

This walks the query tree, runs every branch *independently*, and reports the
hit count for each, so the culprit names itself:

    all                              0
      card.types contains "White"    0   <- KILLER
      card.manaCost regex ...     8687
      any                          514
        node api=Counter           514
        node api=Discard          1064
"""
from __future__ import annotations

from collections import Counter

from .querydsl import QueryError, match_value

# Beyond this many branches we stop expanding: each one is a full scan, and a
# deeply nested query would otherwise turn one search into hundreds.
MAX_BRANCHES = 40


def _label(query: dict) -> str:
    """One-line human description of a query node."""
    if not isinstance(query, dict) or len(query) != 1:
        return "<malformed>"
    (op, arg), = query.items()
    if op in ("all", "any", "not"):
        return op
    if op == "keyword":
        name = arg if isinstance(arg, str) else (arg or {}).get("name")
        return f'keyword "{name}"'
    if op in ("hook", "role"):
        return f'{op} "{arg}"'
    if op == "card":
        parts = [f"{f} {_vp(v)}" for f, v in (arg or {}).items()]
        return "card " + ", ".join(parts)
    if op == "node":
        return "node " + _spec(arg)
    if op == "chain":
        via = f' via {arg.get("via")}' if isinstance(arg, dict) and arg.get("via") else ""
        to = arg.get("to") if isinstance(arg, dict) else None
        tos = to if isinstance(to, list) else [to]
        return (f"chain {_spec(arg.get('from'))} -> "
                f"{' + '.join(_spec(t) for t in tos)}{via}")
    return op


def _spec(spec) -> str:
    if not isinstance(spec, dict):
        return "?"
    return " ".join(f"{k}={_vp(v)}" for k, v in spec.items() if k != "params") + (
        (" params(" + ", ".join(f"{k} {_vp(v)}" for k, v in spec["params"].items()) + ")")
        if spec.get("params") else "")


def _vp(v) -> str:
    """Render a value predicate compactly."""
    if isinstance(v, str):
        return f'"{v}"'
    if v is True:
        return "<present>"
    if isinstance(v, dict):
        if "any" in v:
            return "any[" + ", ".join(_vp(x) for x in v["any"]) + "]"
        for k in ("contains", "icontains", "regex"):
            if k in v:
                return f'{k} "{v[k]}"'
    return str(v)


def diagnose(index, query: dict, limit_branches: int = MAX_BRANCHES) -> dict:
    """Evaluate every branch of `query` independently and report hit counts.

    Returns a nested {label, hits, killer, children} tree. `killer` marks a
    branch that is zero AND whose parent is an `all` — i.e. a branch that is
    solely responsible for the empty result.
    """
    budget = [limit_branches]

    def count(q) -> int:
        try:
            return sum(1 for _ in index.search(q))
        except Exception as e:               # a malformed branch shouldn't
            return -1                        # abort the whole diagnosis

    def walk(q, in_all: bool) -> dict:
        hits = count(q)
        node = {"label": _label(q), "hits": hits, "query": q,
                "killer": bool(in_all and hits == 0), "children": []}
        if not isinstance(q, dict) or len(q) != 1 or budget[0] <= 0:
            return node
        (op, arg), = q.items()
        if op in ("all", "any") and isinstance(arg, list):
            for sub in arg:
                if budget[0] <= 0:
                    node["truncated"] = True
                    break
                budget[0] -= 1
                node["children"].append(walk(sub, in_all=(op == "all")))
        elif op == "not":
            budget[0] -= 1
            node["children"].append(walk(arg, in_all=False))
        return node

    tree = walk(query, in_all=False)
    tree["killers"] = _killers(tree)
    return tree


def _killers(node: dict) -> list[str]:
    out = []
    if node.get("killer"):
        out.append(node["label"])
    for child in node.get("children", []):
        out += _killers(child)
    return out


def _spec_relaxations(spec):
    """(param, predicate, spec-without-that-param) for each param predicate."""
    if not isinstance(spec, dict):
        return
    params = spec.get("params") or {}
    for pname, vp in params.items():
        kept = {k: v for k, v in params.items() if k != pname}
        relaxed = {k: v for k, v in spec.items() if k != "params"}
        if kept:
            relaxed["params"] = kept
        yield pname, vp, relaxed


def query_relaxations(query):
    """Yield (param, predicate, query-with-exactly-that-one-predicate-dropped).

    Every NodeSpec in the query is reachable, not just `node` clauses directly
    under a top-level `all` — `chain` specs carry params too, and in this DSL
    most compiled queries are a chain. Branches under `not` are skipped: there,
    dropping a predicate narrows the result instead of widening it, so the
    "what does relaxing this unlock" reading would be backwards.
    """
    if not isinstance(query, dict) or len(query) != 1:
        return
    (op, arg), = query.items()
    if op in ("all", "any"):
        if isinstance(arg, list):
            for i, sub in enumerate(arg):
                for pname, vp, rsub in query_relaxations(sub):
                    yield pname, vp, {op: [rsub if j == i else c
                                           for j, c in enumerate(arg)]}
    elif op == "node":
        for pname, vp, rspec in _spec_relaxations(arg):
            yield pname, vp, {"node": rspec}
    elif op == "chain" and isinstance(arg, dict):
        for pname, vp, rspec in _spec_relaxations(arg.get("from")):
            yield pname, vp, {"chain": dict(arg, **{"from": rspec})}
        to = arg.get("to")
        targets = to if isinstance(to, list) else [to]
        for i, tspec in enumerate(targets):
            for pname, vp, rspec in _spec_relaxations(tspec):
                new = [rspec if j == i else t for j, t in enumerate(targets)]
                yield pname, vp, {"chain": dict(
                    arg, to=(new if isinstance(to, list) else new[0]))}


def near_misses(index, query: dict, max_params: int = 8, top: int = 8,
                min_unlock: int = 2) -> list[dict]:
    """For an over-NARROW query, show what values are actually there.

    Zero results explain themselves (see `diagnose`). The harder case is a
    query that returns a handful when it should return dozens — no clause is
    empty, so nothing looks wrong. "Lands that pay life to fetch lands"
    returned 2 of 12 because it filtered ChangeType on the string "Land", and
    the ten real fetchlands say "Plains,Island" / "Swamp,Mountain" — Forge
    names concrete types, never the category.

    So: drop one param predicate at a time, and report the values that param
    actually takes among the cards the rest of the query matches. The
    vocabulary comes from the data, not from anyone remembering it.

    Note what this deliberately does NOT claim: a param whose relaxation
    unlocks more cards is not thereby wrong. "ValidTgts$ Creature" on a
    counterspell query unlocks every counterspell and is still exactly what was
    asked for. These rows are evidence about the data, not a verdict.

    `max_params` bounds the total number of probes (each is a full scan).
    """
    base = sum(1 for _ in index.search(query))
    out = []
    for pname, vp, relaxed in query_relaxations(query):
        if len(out) >= max_params:
            break
        seen = Counter()
        reachable = 0
        for hit in index.search(relaxed):
            reachable += 1
            for node in hit["record"].get("nodes") or []:
                val = (node.get("params") or {}).get(pname)
                if val is not None:
                    seen[str(val)] += 1
        if not seen:
            continue
        # How many of the values this param really takes does the current
        # predicate accept? Zero means the predicate names something the data
        # never says — the strongest form of the vocabulary-mismatch signal.
        matched = 0
        for val in seen:
            try:
                if match_value(vp, val):
                    matched += 1
            except QueryError:
                matched += 1        # unjudgeable: assume it matches, stay quiet
        out.append({
            "param": pname,
            "current": _vp(vp),
            "predicate": vp,
            "values": seen.most_common(top),
            "distinct_values": len(seen),
            "matched_values": matched,
            "reachable": reachable,
        })
    # Rank by how much relaxing the param UNLOCKS: the biggest jump is the
    # over-narrow clause. Params whose relaxation changes nothing are noise.
    out = [r for r in out if r["reachable"] >= max(base * min_unlock, base + 1)]
    return sorted(out, key=lambda r: -r["reachable"])


def render_near_misses(rows: list[dict]) -> list[str]:
    lines = []
    for r in rows:
        lines.append(f"relaxing {r['param']} (currently {r['current']}) "
                     f"reaches {r['reachable']:,} cards; actual values:")
        for val, n in r["values"]:
            lines.append(f"    {n:5}  {val}")
        if r.get("matched_values") == 0:
            lines.append(f"    ^ {r['current']} matches NONE of the "
                         f"{r['distinct_values']} values {r['param']} takes here")
    return lines


def render(node: dict, indent: int = 0) -> list[str]:
    """Flatten the tree into aligned text lines."""
    lines = []
    hits = node["hits"]
    shown = "error" if hits < 0 else f"{hits:,}"
    mark = "  <- KILLER (zero, inside an all)" if node.get("killer") else ""
    lines.append(f"{'  ' * indent}{node['label']:<52} {shown:>9}{mark}")
    for child in node.get("children", []):
        lines += render(child, indent + 1)
    if node.get("truncated"):
        lines.append(f"{'  ' * (indent + 1)}... (branch budget exhausted)")
    return lines
