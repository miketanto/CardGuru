"""Minimal HTTP server for the mechanical search.

Stdlib only. The index takes ~0.6 s to load and queries run in milliseconds,
so the whole design is: load once at startup, hold it in memory, answer from
RAM. That is why this is a resident server and not a CGI script.

    python -m cardguru serve            # http://127.0.0.1:8000

Endpoints
    GET  /                 the page
    GET  /api/questions    the compiled question library (benchmark rows)
    POST /api/search       {"query": <DSL>}  -> hits with evidence
    POST /api/ask          {"question": "..."} -> compiles NL, then searches.
                           Requires ANTHROPIC_API_KEY; returns 503 without it
                           so the UI can disable the box instead of failing.

Bound to 127.0.0.1 by default: this serves an unauthenticated query endpoint
and has no business on a public interface.
"""
from __future__ import annotations

import json
import os
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .cardstore import CardStore
from .index import SearchIndex, explain

def log(*parts):
    """Debug output. flush=True is load-bearing: stdout is block-buffered when
    redirected to a file, so without it `tail -f server.log` shows nothing
    until the process exits — useless for the one job these lines have."""
    print(*parts, flush=True)


HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "static", "index.html")
MAX_HITS = 300
# Below this, a result is suspicious enough to explain itself.
NARROW_THRESHOLD = 5


class State:
    """Everything loaded once, shared across requests."""

    def __init__(self, dataset: str, carddb: str, questions: str,
                 ontology: str | None, verbose: bool = False,
                 signals: str = "zero"):
        self.verbose = verbose
        self.signals = signals      # execution feedback: off | zero | full
        self.index = SearchIndex.load(dataset)
        self.store = CardStore.open(carddb)
        self.meta = getattr(self.index, "meta", {}) or {}
        self.ontology_path = ontology if ontology and os.path.exists(ontology) else None
        self.questions = self._load_questions(questions)

    @staticmethod
    def _load_questions(path: str) -> list[dict]:
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        out = []
        for r in rows:
            if not r.get("query"):
                continue        # unexpressible rows have no query to run
            out.append({
                "id": r["id"], "question": r["question"],
                "status": r.get("status", "compiled"),
                "gap": r.get("gap"), "query": r["query"],
                "area": r.get("mechanical_area", ""),
            })
        return out

    def validate(self, query) -> list[str]:
        if not self.ontology_path:
            return []
        from .validate import Ontology, validate
        return validate(query, Ontology.load(self.ontology_path))

    def run(self, query, limit: int = MAX_HITS) -> dict:
        if self.verbose:
            log("  query: " + json.dumps(query))
        errors = self.validate(query)
        if errors:
            if self.verbose:
                log("  REJECTED by validator: " + "; ".join(errors))
            return {"ok": False, "errors": errors}
        hits, total = [], 0
        for hit in self.index.search(query):
            total += 1
            if len(hits) >= limit:
                continue
            rec = hit["record"]
            row = {
                "name": rec.get("name"),
                "types": rec.get("types"),
                "manaCost": rec.get("manaCost"),
                "pt": rec.get("pt"),
                "evidence": explain(rec, hit["evidence"]),
            }
            if self.store:
                sf = self.store.resolve(rec.get("name") or "")
                if sf is not None:
                    row["manaCost"] = sf["mana_cost"] or row["manaCost"]
                    row["types"] = sf["type_line"] or row["types"]
                    row["rarity"] = sf["rarity"]
                    row["scryfall_uri"] = sf["scryfall_uri"]
                    row["join"] = "joined"
                else:
                    # Honest state: the graph result stands, the card data
                    # is simply absent. Never fake it.
                    row["join"] = "unjoined"
            hits.append(row)
        out = {"ok": True, "total": total, "shown": len(hits), "hits": hits,
               "truncated": total > len(hits)}
        # An over-narrow query is harder to spot than an empty one: nothing
        # looks broken. Surface what the filtered params actually contain.
        if 0 < total <= NARROW_THRESHOLD:
            from .diagnose import near_misses, render_near_misses
            rows = near_misses(self.index, query)
            if rows:
                out["near_misses"] = {"lines": render_near_misses(rows),
                                      "params": [r["param"] for r in rows]}
                if self.verbose:
                    log(f"  only {total} hits - near misses:")
                    for line in out["near_misses"]["lines"]:
                        log("    " + line)
        if total == 0:
            # An empty result is the least informative answer possible. Say
            # which branch zeroed it rather than making the user guess.
            from .diagnose import diagnose, render
            tree = diagnose(self.index, query)
            out["diagnosis"] = {"lines": render(tree), "killers": tree["killers"]}
            if self.verbose:
                log("  0 hits - diagnosis:")
                for line in out["diagnosis"]["lines"]:
                    log("    " + line)
        return out


class Handler(BaseHTTPRequestHandler):
    state: State = None          # set by serve()
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        log(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

    # -- helpers ---------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict):
        self._send(code, json.dumps(payload).encode(), "application/json")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # -- routes ----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            try:
                with open(PAGE, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(500, b"static/index.html missing", "text/plain")
        elif path == "/api/questions":
            self._json(200, {
                "questions": self.state.questions,
                "meta": {
                    "forge_pin": self.state.meta.get("source_pin"),
                    "faces": len(self.state.index.records),
                    "scryfall": (self.state.store.meta.get("scryfall_snapshot")
                                 if self.state.store else None),
                    "nl_enabled": bool(os.environ.get("ANTHROPIC_API_KEY")),
                },
            })
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            if path == "/api/search":
                query = self._body().get("query")
                if not isinstance(query, dict):
                    return self._json(400, {"ok": False,
                                            "errors": ["body needs a 'query' object"]})
                self._json(200, self.state.run(query))
            elif path == "/api/ask":
                self._ask()
            else:
                self._json(404, {"error": "not found"})
        except json.JSONDecodeError as e:
            self._json(400, {"ok": False, "errors": [f"invalid JSON: {e}"]})
        except Exception as e:                       # never 500 silently
            traceback.print_exc()
            self._json(500, {"ok": False, "errors": [f"{type(e).__name__}: {e}"]})

    # "cards like X" / "similar to X" is a card-anchored question: it needs the
    # named card's own graph, which the NL compiler never sees. Route it.
    LIKE_RE = re.compile(
        r"^\s*(?:cards?|things?|anything|what)?\s*(?:that (?:are|is)\s+)?"
        r"(?:like|similar to|同)\s+(.+?)\s*\??$", re.I)

    def _similar(self, question: str):
        m = self.LIKE_RE.match(question)
        if not m:
            return None
        from .similar import similar

        try:
            rec, query, hits, exact, opts = similar(self.state.index, m.group(1))
        except SystemExit:
            # Genuinely not a card name ("like a cheap counterspell") — the
            # compiler is the right handler. A near-miss name is corrected
            # above rather than reaching here.
            return None
        if self.state.verbose:
            log(f"  similar-to {rec['name']!r}: {json.dumps(query)}")
        out = self.state.run(query)
        out["compiled"] = query
        out["anchor"] = rec.get("name")
        out["abilities"] = [{"reaches": o["reaches"], "spec": o["spec"]}
                            for o in opts]
        if not exact:
            out["anchor_note"] = (f"No card named {m.group(1)!r}; showing cards "
                                  f"like {rec.get('name')!r}.")
        out["hits"] = [h for h in out["hits"] if h["name"] != rec.get("name")]
        out["total"] = max(0, out["total"] - 1)
        return out

    def _ask(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return self._json(503, {
                "ok": False,
                "errors": ["Natural-language questions need ANTHROPIC_API_KEY. "
                           "Pick a question from the library, or write a query "
                           "by hand."]})
        question = (self._body().get("question") or "").strip()
        if not question:
            return self._json(400, {"ok": False, "errors": ["empty question"]})
        routed = self._similar(question)
        if routed is not None:
            return self._json(200, routed)
        from .nl_compiler import compile_question
        from .repair import make_checker
        if self.state.verbose:
            log(f"  ask: {question!r}")
        # The compile loop executes each candidate and repairs on the result,
        # instead of only seeing validation errors.
        checker = make_checker(self.state.index, self.state.signals)
        result = compile_question(question, self.state.ontology_path,
                                  checker=checker)
        if self.state.verbose:
            log("  compiled: " + json.dumps(result.query)
                + f"  ({len(result.attempts)} attempt(s)"
                + (f", execution {result.checks}" if result.checks else "")
                + (", best-effort: retries exhausted" if result.exhausted else "")
                + ")")
        if not result.ok:
            return self._json(200, {"ok": False, "errors": result.errors})
        out = self.state.run(result.query)
        out["compiled"] = result.query
        self._json(200, out)


def serve(dataset: str, carddb: str, questions: str, ontology: str | None,
          host: str = "127.0.0.1", port: int = 8000, verbose: bool = False,
          signals: str = "zero"):
    print(f"loading index from {dataset} ...")
    Handler.state = State(dataset, carddb, questions, ontology, verbose=verbose,
                          signals=signals)
    st = Handler.state
    print(f"  {len(st.index.records):,} faces"
          f"{'  + scryfall card store' if st.store else '  (no card store)'}"
          f"  |  {len(st.questions)} preset questions"
          f"{'' if st.ontology_path else '  (no ontology: queries unvalidated)'}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  note: ANTHROPIC_API_KEY unset - the English question box is "
              "disabled; the preset library and hand-written queries work.")
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"\n  ready:  http://{host}:{port}\n  ctrl-c to stop\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        srv.server_close()
