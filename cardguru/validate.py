"""Validate mechanical-search queries against the mined Forge ontology.

The ontology (research/data/ontology.json) is the closed vocabulary: every
exact-match api/mode/keyword/param token in a query must exist in it. This is
the gate that makes an LLM-compiled query trustworthy — a query that names
vocabulary outside the ontology is rejected before it ever runs.

Predicates that can't be vocabulary-checked (contains/icontains/regex) pass
through; structural errors reuse the querydsl rules.
"""
from __future__ import annotations

import json

from .querydsl import NODE_SPEC_KEYS

QUERY_OPS = {"all", "any", "not", "node", "chain", "keyword", "card"}
CARD_FIELDS = {"name", "types", "manaCost", "oracle", "pt"}
KINDS = {"A", "T", "S", "R", "K", "SVar", "SVarCount", "SVarValue"}
API_KINDS = {"SP", "AB", "DB"}


class Ontology:
    def __init__(self, data: dict):
        self.apis = set(data.get("api", {}))
        self.modes = set(data.get("trigger_modes", {})) | set(data.get("static_modes", {}))
        self.keywords = set(data.get("keywords", {}))
        self.param_keys = set(data.get("param_keys", {}))
        self.replacement_events = set(data.get("replacement_events", {}))

    @classmethod
    def load(cls, path: str) -> "Ontology":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))


def _exact_values(vp):
    """Exact string values inside a value predicate (checkable ones)."""
    if isinstance(vp, str):
        return [vp]
    if isinstance(vp, dict) and "any" in vp:
        out = []
        for sub in vp["any"]:
            out += _exact_values(sub)
        return out
    return []  # contains/icontains/regex/True — not vocabulary-checkable


def _check_node_spec(spec, onto: Ontology, path: str, errors: list):
    if not isinstance(spec, dict):
        errors.append(f"{path}: NodeSpec must be an object")
        return
    unknown = set(spec) - NODE_SPEC_KEYS
    if unknown:
        errors.append(f"{path}: unknown NodeSpec fields {sorted(unknown)}")
    for v in _exact_values(spec.get("kind")):
        if v not in KINDS:
            errors.append(f"{path}.kind: unknown kind '{v}'")
    for v in _exact_values(spec.get("apiKind")):
        if v not in API_KINDS:
            errors.append(f"{path}.apiKind: unknown apiKind '{v}'")
    for v in _exact_values(spec.get("api")):
        if v not in onto.apis:
            errors.append(f"{path}.api: '{v}' is not in the ontology")
    for v in _exact_values(spec.get("mode")):
        if v not in onto.modes:
            errors.append(f"{path}.mode: '{v}' is not in the ontology")
    for v in _exact_values(spec.get("keyword")):
        if v not in onto.keywords:
            errors.append(f"{path}.keyword: '{v}' is not in the ontology")
    params = spec.get("params")
    if params is not None:
        if not isinstance(params, dict):
            errors.append(f"{path}.params: must be an object")
        else:
            for pk, pv in params.items():
                if pk not in onto.param_keys:
                    errors.append(f"{path}.params: unknown parameter '{pk}'")
                if pk == "Event":
                    for v in _exact_values(pv):
                        if v not in onto.replacement_events:
                            errors.append(
                                f"{path}.params.Event: '{v}' is not a replacement event")


def validate(query, onto: Ontology, path: str = "$") -> list[str]:
    """Return a list of human-readable errors; empty list = valid."""
    errors: list[str] = []
    if not isinstance(query, dict) or len(query) != 1:
        errors.append(f"{path}: query must be a single-key object")
        return errors
    (op, arg), = query.items()
    if op not in QUERY_OPS:
        errors.append(f"{path}: unknown operator '{op}'")
        return errors

    if op in ("all", "any"):
        if not isinstance(arg, list) or not arg:
            errors.append(f"{path}.{op}: must be a non-empty array")
        else:
            for i, sub in enumerate(arg):
                errors += validate(sub, onto, f"{path}.{op}[{i}]")
    elif op == "not":
        errors += validate(arg, onto, f"{path}.not")
    elif op == "node":
        _check_node_spec(arg, onto, f"{path}.node", errors)
    elif op == "chain":
        if not isinstance(arg, dict) or "from" not in arg or "to" not in arg:
            errors.append(f'{path}.chain: needs "from" and "to"')
        else:
            _check_node_spec(arg["from"], onto, f"{path}.chain.from", errors)
            targets = arg["to"] if isinstance(arg["to"], list) else [arg["to"]]
            for i, t in enumerate(targets):
                _check_node_spec(t, onto, f"{path}.chain.to[{i}]", errors)
            unknown = set(arg) - {"from", "to", "via"}
            if unknown:
                errors.append(f"{path}.chain: unknown fields {sorted(unknown)}")
    elif op == "keyword":
        name = arg if isinstance(arg, str) else (arg or {}).get("name")
        for v in _exact_values(name):
            if v not in onto.keywords:
                errors.append(f"{path}.keyword: '{v}' is not in the ontology")
    elif op == "card":
        if not isinstance(arg, dict):
            errors.append(f"{path}.card: must be an object")
        else:
            for f in set(arg) - CARD_FIELDS:
                errors.append(f"{path}.card: unknown field '{f}'")
    return errors
