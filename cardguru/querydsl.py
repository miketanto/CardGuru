"""JSON query DSL for mechanical search over card ability graphs.

Query forms (composable):
  {"all":  [Q, ...]}                 every subquery matches
  {"any":  [Q, ...]}                 at least one matches
  {"not":  Q}                        negation (contributes no evidence)
  {"node": NodeSpec}                 some graph node matches
  {"chain": {"from": NodeSpec, "to": NodeSpec | [NodeSpec, ...],
             "via": [edgeType, ...]?}}
                                     a node matching `from` reaches a node
                                     matching `to` along graph edges; a list
                                     of `to` specs means ALL must be reachable
                                     from the SAME `from` node (optionally
                                     restricted to edge types; "ref:*"
                                     excluded unless listed)
  {"keyword": "Flying"}              card has keyword (name match)
  {"card": {"types": VP?, "name": VP?, "manaCost": VP?, "oracle": VP?}}
                                     card-level attribute predicates
  {"hook": "sac_outlet"}             semantic facet from the validated hook
                                     library (cardguru.recommend.HOOKS)
  {"role": "card_draw"}              deckbuilding role facet; suffix
                                     ":engine" / ":one_shot" to restrict
                                     repeatability (e.g. "card_draw:engine")

NodeSpec fields (all optional, AND-ed):
  kind      "A"|"T"|"S"|"R"|"K"|"SVar"|"SVarCount"|"SVarValue"  (VP allowed)
  api       effect API name, e.g. "Token"      (VP allowed)
  apiKind   "SP"|"AB"|"DB"
  mode      trigger/static mode, e.g. "DamageDone"  (VP allowed)
  keyword   keyword-node name (kind K)         (VP allowed)
  count     Count$ expression (kind SVarCount) (VP allowed)
  value     raw SVar value    (kind SVarValue) (VP allowed)
  params    {ParamName: VP}   parameter predicates

`value` is where arithmetic operators live. Doubling Season and Hardened
Scales are structurally identical on the counter branch — both are
R|Event$ AddCounter -> ReplaceWith -> api ReplaceCounter — and differ only in
the referenced SVarValue: "ReplaceCount$CounterNum/Twice" vs
".../Plus.1". Without this field, doubling-vs-incrementing is reachable only
by falling back to a card.oracle text regex, which defeats the point.

VP (value predicate): exact string, or
  {"contains": s} | {"icontains": s} | {"regex": r} | {"any": [VP, ...]} | true (key exists)
"""
from __future__ import annotations

import re
from collections import defaultdict


class QueryError(ValueError):
    pass


# ---------------------------------------------------------------- value preds

def match_value(pred, value) -> bool:
    if value is None:
        return False
    if pred is True:
        return True
    sval = value if isinstance(value, str) else str(value)
    if isinstance(pred, str):
        return sval == pred
    if isinstance(pred, dict):
        if "contains" in pred:
            return pred["contains"] in sval
        if "icontains" in pred:
            return pred["icontains"].lower() in sval.lower()
        if "regex" in pred:
            return re.search(pred["regex"], sval) is not None
        if "any" in pred:
            return any(match_value(p, sval) for p in pred["any"])
        raise QueryError(f"unknown value predicate: {pred}")
    raise QueryError(f"invalid value predicate: {pred!r}")


# ---------------------------------------------------------------- node spec

NODE_SPEC_KEYS = {"kind", "api", "apiKind", "mode", "keyword", "count", "value",
                  "params"}


def match_node(spec: dict, node: dict) -> bool:
    unknown = set(spec) - NODE_SPEC_KEYS
    if unknown:
        raise QueryError(f"unknown NodeSpec fields: {sorted(unknown)}")
    for f in ("kind", "api", "apiKind", "mode", "keyword", "count", "value"):
        if f in spec and not match_value(spec[f], node.get(f)):
            return False
    for pk, vp in (spec.get("params") or {}).items():
        if not match_value(vp, (node.get("params") or {}).get(pk)):
            return False
    return True


# ---------------------------------------------------------------- graph eval

class CardGraph:
    """Adjacency wrapper over a face record's nodes/edges."""

    def __init__(self, record: dict):
        self.record = record
        self.nodes = record["nodes"]
        self.by_id = {n["id"]: n for n in self.nodes}
        self.adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for e in record["edges"]:
            self.adj[e["src"]].append((e["dst"], e["type"]))

    def reachable(self, start: str, via: list[str] | None):
        """BFS; yields (node_id, path) where path is [start,...,node_id].
        Default: follow chain edges only (exclude 'ref:*') for precision."""
        seen = {start}
        frontier = [(start, [start])]
        while frontier:
            nxt = []
            for cur, path in frontier:
                for dst, etype in self.adj.get(cur, []):
                    if via is not None:
                        if etype not in via:
                            continue
                    elif etype.startswith("ref:"):
                        continue
                    if dst in seen:
                        continue
                    seen.add(dst)
                    p = path + [dst]
                    yield dst, p
                    nxt.append((dst, p))
            frontier = nxt


def evaluate(query: dict, graph: CardGraph):
    """Return (matched: bool, evidence: list). Evidence items:
    {"node": id} or {"path": [ids]} or {"keyword": name} or {"card": field}."""
    if not isinstance(query, dict) or len(query) != 1:
        raise QueryError(f"query must be a single-key object, got: {query!r}")
    (op, arg), = query.items()

    if op == "all":
        evidence = []
        for q in arg:
            ok, ev = evaluate(q, graph)
            if not ok:
                return False, []
            evidence += ev
        return True, evidence

    if op == "any":
        for q in arg:
            ok, ev = evaluate(q, graph)
            if ok:
                return True, ev
        return False, []

    if op == "not":
        ok, _ = evaluate(arg, graph)
        return (not ok), []

    if op == "node":
        ev = [{"node": n["id"]} for n in graph.nodes if match_node(arg, n)]
        return bool(ev), ev

    if op == "chain":
        frm, to = arg.get("from"), arg.get("to")
        if frm is None or to is None:
            raise QueryError('"chain" needs "from" and "to"')
        targets = to if isinstance(to, list) else [to]
        via = arg.get("via")
        ev = []
        for n in graph.nodes:
            if not match_node(frm, n):
                continue
            # Reachable set from this root (self included: the from-node may
            # itself satisfy a target).
            paths = {n["id"]: [n["id"]]}
            for dst, path in graph.reachable(n["id"], via):
                paths[dst] = path
            witness = []
            for tspec in targets:
                hit = next((p for nid, p in paths.items()
                            if match_node(tspec, graph.by_id[nid])), None)
                if hit is None:
                    witness = None
                    break
                witness.append({"path": hit})
            if witness:
                ev += witness               # one witness path per target
        return bool(ev), ev

    if op == "keyword":
        name = arg if isinstance(arg, str) else arg.get("name")
        ev = [{"keyword": n["keyword"], "node": n["id"]}
              for n in graph.nodes
              if n.get("kind") == "K" and match_value(name, n.get("keyword"))]
        return bool(ev), ev

    if op == "card":
        rec = graph.record
        fields = {"types": "types", "name": "name", "manaCost": "manaCost",
                  "oracle": "oracle", "pt": "pt"}
        for f, vp in arg.items():
            if f not in fields:
                raise QueryError(f"unknown card field: {f}")
            if not match_value(vp, rec.get(fields[f])):
                return False, []
        return True, [{"card": list(arg)}]

    if op == "hook":
        # semantic facet from the validated hook library ("is:sac_outlet")
        from .recommend import HOOKS, detect_hooks
        if arg not in HOOKS:
            raise QueryError(f"unknown hook: {arg} (see cardguru.recommend.HOOKS)")
        ok = arg in detect_hooks(graph.record)
        return ok, ([{"hook": arg}] if ok else [])

    if op == "role":
        # deckbuilding role facet, engine-vs-one-shot aware:
        # "card_draw" matches either; "card_draw:engine" requires an engine
        from .deck import ROLES, detect_roles
        name, _, kind = arg.partition(":")
        if name not in ROLES:
            raise QueryError(f"unknown role: {name} (one of {sorted(ROLES)})")
        got = detect_roles(graph.record).get(name)
        ok = got is not None and (not kind or got == kind)
        return ok, ([{"role": name, "kind": got}] if ok else [])

    raise QueryError(f"unknown query operator: {op}")


# ------------------------------------------------- pruning-token extraction

def _spec_tokens(spec: dict) -> set[str]:
    """Index tokens implied by a NodeSpec (only exact-match fields index)."""
    toks = set()
    if isinstance(spec.get("api"), str):
        toks.add(f"api:{spec['api']}")
    if isinstance(spec.get("mode"), str):
        toks.add(f"mode:{spec['mode']}")
    if isinstance(spec.get("keyword"), str):
        toks.add(f"kw:{spec['keyword']}")
    if isinstance(spec.get("kind"), str):
        toks.add(f"kind:{spec['kind']}")
    for pk in (spec.get("params") or {}):
        toks.add(f"pk:{pk}")
    return toks


def required_token_groups(query: dict) -> list[set[str]]:
    """CNF-ish pruning: a list of token-alternative groups; every group must
    have at least one token present on a candidate card. Conservative —
    returns [] (no pruning) where it can't be sure."""
    (op, arg), = query.items()
    if op == "all":
        groups = []
        for q in arg:
            groups += required_token_groups(q)
        return groups
    if op == "any":
        alts: set[str] = set()
        for q in arg:
            sub = required_token_groups(q)
            if not sub:
                return []                    # one un-indexable branch: no pruning
            # weakest form: union of one group per branch
            alts |= sub[0]
        return [alts] if alts else []
    if op == "node":
        toks = _spec_tokens(arg)
        return [ {t} for t in toks ]
    if op == "chain":
        groups = []
        for t in _spec_tokens(arg.get("from", {})):
            groups.append({t})
        to = arg.get("to", {})
        for tspec in (to if isinstance(to, list) else [to]):
            for t in _spec_tokens(tspec):
                groups.append({t})
        return groups
    if op == "keyword":
        if isinstance(arg, str):
            return [{f"kw:{arg}"}]
        return []
    return []                                # not / card: no pruning
