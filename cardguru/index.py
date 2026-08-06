"""In-memory search index: postings for candidate pruning + full DSL evaluation."""
from __future__ import annotations

from collections import defaultdict

from . import dataset as ds
from .querydsl import CardGraph, evaluate, required_token_groups


def _face_tokens(rec: dict):
    for n in rec["nodes"]:
        kind = n.get("kind")
        if kind:
            yield f"kind:{kind}"
        if n.get("api"):
            yield f"api:{n['api']}"
        if n.get("mode"):
            yield f"mode:{n['mode']}"
        if kind == "K" and n.get("keyword"):
            yield f"kw:{n['keyword']}"
        for pk in (n.get("params") or {}):
            yield f"pk:{pk}"


class SearchIndex:
    def __init__(self, records: list[dict]):
        self.records = records
        self.postings: dict[str, set[int]] = defaultdict(set)
        for i, rec in enumerate(records):
            for tok in set(_face_tokens(rec)):
                self.postings[tok].add(i)

    @classmethod
    def load(cls, path: str) -> "SearchIndex":
        meta, records = ds.load(path)
        idx = cls(list(records))
        idx.meta = meta
        return idx

    def candidates(self, query: dict):
        groups = required_token_groups(query)
        if not groups:
            return range(len(self.records))
        result: set[int] | None = None
        for group in groups:
            hits: set[int] = set()
            for tok in group:
                hits |= self.postings.get(tok, set())
            result = hits if result is None else (result & hits)
            if not result:
                return set()
        return result

    def search(self, query: dict, limit: int | None = None):
        """Yield {"record", "evidence"} for each matching face."""
        n = 0
        for i in sorted(self.candidates(query)):
            rec = self.records[i]
            ok, evidence = evaluate(query, CardGraph(rec))
            if ok:
                yield {"record": rec, "evidence": evidence}
                n += 1
                if limit is not None and n >= limit:
                    return


def explain(rec: dict, evidence: list) -> list[str]:
    """Human-readable 'why it matched' lines from evidence items."""
    by_id = {n["id"]: n for n in rec["nodes"]}

    def describe(nid: str) -> str:
        n = by_id.get(nid, {})
        if n.get("kind") == "K":
            return f"{nid}[K:{n.get('keyword')}]"
        label = n.get("api") or n.get("mode") or n.get("count") or n.get("kind", "?")
        return f"{nid}[{n.get('kind')}:{label}]"

    lines = []
    for ev in evidence:
        if "path" in ev:
            lines.append(" -> ".join(describe(x) for x in ev["path"]))
        elif "node" in ev:
            lines.append(describe(ev["node"]))
        elif "keyword" in ev:
            lines.append(f"keyword {ev['keyword']}")
        elif "card" in ev:
            lines.append(f"card fields: {', '.join(ev['card'])}")
    return lines
