"""Phase 0a (v7 plan §2): validator for the WIRE-V7 contract (rl/WIRE-V7.md).

Checks a stream of newline-delimited JSON (a hello then consults, as the
engine writes it, replies optional) structurally and semantically:

  hello    wire == 7, card_emb, d_c, v7_dims / v7_rtypes / v7_ctypes /
           v7_zones equal to this file's constants (append-only tables),
           buffer sizes present
  consult  every v7_ key present and of the right shape; array lengths
           agree; widths match v7_dims; every float finite; one-hots sum to
           1 where WIRE-V7.md says one-hot; edges and refers inside the
           token index space (0 game, 1 me, 2 opp, 3.. entities); edge
           types < v7_rtypes; candidate types < v7_ctypes and equal to the
           row's leading one-hot; refers non-empty for every non-PASS
           candidate; v6 keys (g, e, r, c) still present with v6 widths
  reply    {"a": k} with 0 <= k < number of candidates

The first violation per message is reported with the key and position;
exit 1 if any file has a violation.  `--emit-schema PATH` writes the
structural part as JSON Schema (draft-07) for consumers that want it.

Run:  python rl/wire_validate.py rl/fixtures/v7/*.jsonl
      python rl/wire_validate.py --emit-schema rl/fixtures/v7/schema.json
"""
import argparse
import json
import math
import sys

WIRE = 7
DIMS = {"game": 24, "player": 16, "ent": 64, "cand": 40, "opp_hand": 8, "opp_deck": 6, "opp_action": 8}
RTYPES = 8
CTYPES = 8
ZONES = 7
MAXES = {"v7_emax": 160, "v7_kmax": 96, "v7_ohmax": 12, "v7_odmax": 64, "v7_oamax": 16}
V6 = {"gdim": 16, "edim": 48, "cdim": 94}
# one-hot spans (start, end exclusive) per row type, per WIRE-V7.md
ONEHOT = {
    "v7_game": [(2, 10), (12, 20)],
    "v7_ent": [(0, 7)],
    "v7_opp_hand": [(0, 4)],
    "v7_opp_actions": [(0, 7)],
}
CAND_TYPE_ONEHOT = (0, 8)
GAME, ME, OPP, ENT0 = 0, 1, 2, 3


class Violation(Exception):
    pass


def _finite_row(row, key, i, width):
    if not isinstance(row, list) or len(row) != width:
        raise Violation(f"{key}[{i}]: width {len(row) if isinstance(row, list) else 'n/a'} != {width}")
    for j, x in enumerate(row):
        if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
            raise Violation(f"{key}[{i}][{j}]: not a finite number ({x!r})")


def _onehot(row, key, i, spans):
    for a, b in spans:
        s = sum(row[a:b])
        if abs(s - 1.0) > 1e-6 or any(x not in (0, 1, 0.0, 1.0) for x in row[a:b]):
            raise Violation(f"{key}[{i}][{a}:{b}]: not one-hot (sum {s})")


def validate_hello(h):
    if h.get("t") != "hello":
        raise Violation("hello: t != 'hello'")
    if h.get("wire") != WIRE:
        raise Violation(f"hello.wire: {h.get('wire')!r} != {WIRE}")
    for k in ("card_emb", "d_c", "v7_dims", "v7_rtypes", "v7_ctypes", "v7_zones", *MAXES):
        if k not in h:
            raise Violation(f"hello.{k}: missing")
    if not isinstance(h["card_emb"], str) or not h["card_emb"].startswith("card_emb_v"):
        raise Violation(f"hello.card_emb: {h['card_emb']!r}")
    if h["d_c"] != 128:
        raise Violation(f"hello.d_c: {h['d_c']} != 128")
    if h["v7_dims"] != DIMS:
        raise Violation(f"hello.v7_dims: {h['v7_dims']} != {DIMS}")
    if h["v7_rtypes"] != RTYPES or h["v7_ctypes"] != CTYPES or h["v7_zones"] != ZONES:
        raise Violation("hello.v7_rtypes/ctypes/zones: mismatch")
    for k in V6:
        if h.get(k) != V6[k]:
            raise Violation(f"hello.{k}: {h.get(k)} != {V6[k]}")
    for k, v in MAXES.items():
        if not isinstance(h[k], int) or h[k] < 1:
            raise Violation(f"hello.{k}: {h[k]!r}")
    return h


def validate_consult(m, hello=None):
    if m.get("t") != "consult":
        raise Violation("consult: t != 'consult'")
    if m.get("wire") != WIRE:
        raise Violation(f"consult.wire: {m.get('wire')!r} != {WIRE}")
    maxes = {k: (hello[k] if hello else v) for k, v in MAXES.items()}
    # v6 keys keep v6 meaning
    for k in ("g", "e", "r", "c"):
        if k not in m:
            raise Violation(f"consult.{k}: missing (v6 key)")
    _finite_row(m["g"], "g", 0, V6["gdim"])
    for i, row in enumerate(m["e"]):
        _finite_row(row, "e", i, V6["edim"])
    for i, row in enumerate(m["c"]):
        _finite_row(row, "c", i, V6["cdim"])
    # game, players
    _finite_row(m.get("v7_game"), "v7_game", 0, DIMS["game"])
    _onehot(m["v7_game"], "v7_game", 0, ONEHOT["v7_game"])
    if not isinstance(m.get("v7_players"), list) or len(m["v7_players"]) != 2:
        raise Violation("v7_players: need exactly 2 rows")
    for i, row in enumerate(m["v7_players"]):
        _finite_row(row, "v7_players", i, DIMS["player"])
    # entities
    ents = m.get("v7_ent")
    names, toks = m.get("v7_ent_name"), m.get("v7_ent_token")
    if not isinstance(ents, list) or not isinstance(names, list) or not isinstance(toks, list):
        raise Violation("v7_ent / v7_ent_name / v7_ent_token: missing")
    if not (len(ents) == len(names) == len(toks)):
        raise Violation(f"v7_ent arrays: lengths differ ({len(ents)}, {len(names)}, {len(toks)})")
    if len(ents) > maxes["v7_emax"]:
        raise Violation(f"v7_ent: {len(ents)} > v7_emax {maxes['v7_emax']}")
    if "v7_ent_id" in m and len(m["v7_ent_id"]) != len(ents):
        raise Violation("v7_ent_id: length differs from v7_ent")
    for i, row in enumerate(ents):
        _finite_row(row, "v7_ent", i, DIMS["ent"])
        _onehot(row, "v7_ent", i, ONEHOT["v7_ent"])
        if not isinstance(names[i], str):
            raise Violation(f"v7_ent_name[{i}]: not a string")
        if toks[i] not in (0, 1):
            raise Violation(f"v7_ent_token[{i}]: {toks[i]!r}")
    n_tok = ENT0 + len(ents)
    # edges
    edges = m.get("v7_edges")
    if not isinstance(edges, list):
        raise Violation("v7_edges: missing")
    for i, e in enumerate(edges):
        if not (isinstance(e, list) and len(e) == 3 and all(isinstance(x, int) for x in e)):
            raise Violation(f"v7_edges[{i}]: not [src, dst, type] ints")
        s, d, t = e
        if not (0 <= s < n_tok and 0 <= d < n_tok):
            raise Violation(f"v7_edges[{i}]: endpoint outside token space 0..{n_tok - 1}")
        if not (0 <= t < RTYPES):
            raise Violation(f"v7_edges[{i}]: type {t} >= v7_rtypes {RTYPES}")
    # candidates
    ct, cr, cf = m.get("v7_cand_type"), m.get("v7_cand_refers"), m.get("v7_cand")
    if not (isinstance(ct, list) and isinstance(cr, list) and isinstance(cf, list)):
        raise Violation("v7_cand_type / v7_cand / v7_cand_refers: missing")
    if not (len(ct) == len(cr) == len(cf)):
        raise Violation("v7_cand arrays: lengths differ")
    if not (1 <= len(ct) <= maxes["v7_kmax"]):
        raise Violation(f"v7_cand: {len(ct)} candidates (need 1..{maxes['v7_kmax']})")
    if len(m["c"]) != len(ct):
        raise Violation(f"c vs v7_cand: {len(m['c'])} != {len(ct)}")
    for k in range(len(ct)):
        if not (isinstance(ct[k], int) and 0 <= ct[k] < CTYPES):
            raise Violation(f"v7_cand_type[{k}]: {ct[k]!r}")
        _finite_row(cf[k], "v7_cand", k, DIMS["cand"])
        a, b = CAND_TYPE_ONEHOT
        oh = cf[k][a:b]
        if sum(oh) != 1 or oh[ct[k]] != 1:
            raise Violation(f"v7_cand[{k}][0:8]: one-hot does not match v7_cand_type {ct[k]}")
        if not isinstance(cr[k], list) or not all(isinstance(x, int) for x in cr[k]):
            raise Violation(f"v7_cand_refers[{k}]: not a list of ints")
        for x in cr[k]:
            if not (ME <= x < n_tok):
                raise Violation(f"v7_cand_refers[{k}]: index {x} outside 1..{n_tok - 1}")
        if ct[k] != 0 and not cr[k]:
            raise Violation(f"v7_cand_refers[{k}]: empty for non-PASS candidate (type {ct[k]})")
    # opponent tokens (optional until 3d)
    if "v7_opp_hand" in m:
        oh, ohn = m["v7_opp_hand"], m.get("v7_opp_hand_name")
        if not isinstance(ohn, list) or len(ohn) != len(oh):
            raise Violation("v7_opp_hand_name: missing or length differs")
        if len(oh) > maxes["v7_ohmax"]:
            raise Violation(f"v7_opp_hand: {len(oh)} > v7_ohmax")
        for i, row in enumerate(oh):
            _finite_row(row, "v7_opp_hand", i, DIMS["opp_hand"])
            _onehot(row, "v7_opp_hand", i, ONEHOT["v7_opp_hand"])
            if (row[5] == 1) != (ohn[i] is not None):
                raise Violation(f"v7_opp_hand[{i}]: known flag {row[5]} disagrees with name {ohn[i]!r}")
    if "v7_opp_deck" in m:
        od, odn = m["v7_opp_deck"], m.get("v7_opp_deck_name")
        if not isinstance(odn, list) or len(odn) != len(od):
            raise Violation("v7_opp_deck_name: missing or length differs")
        if len(od) > maxes["v7_odmax"]:
            raise Violation(f"v7_opp_deck: {len(od)} > v7_odmax")
        for i, row in enumerate(od):
            _finite_row(row, "v7_opp_deck", i, DIMS["opp_deck"])
            if not isinstance(odn[i], str):
                raise Violation(f"v7_opp_deck_name[{i}]: not a string")
    if "v7_opp_actions" in m:
        oa, oar = m["v7_opp_actions"], m.get("v7_opp_action_refers")
        if not isinstance(oar, list) or len(oar) != len(oa):
            raise Violation("v7_opp_action_refers: missing or length differs")
        if len(oa) > maxes["v7_oamax"]:
            raise Violation(f"v7_opp_actions: {len(oa)} > v7_oamax")
        for i, row in enumerate(oa):
            _finite_row(row, "v7_opp_actions", i, DIMS["opp_action"])
            _onehot(row, "v7_opp_actions", i, ONEHOT["v7_opp_actions"])
            for x in oar[i]:
                if not (isinstance(x, int) and ME <= x < n_tok):
                    raise Violation(f"v7_opp_action_refers[{i}]: index {x!r} outside 1..{n_tok - 1}")
    ctr = m.get("v7_ctr")
    if not isinstance(ctr, dict) or "entityTrunc" not in ctr:
        raise Violation("v7_ctr: missing entityTrunc")
    return len(ct)


def validate_reply(r, n_cand):
    if not isinstance(r.get("a"), int) or not (0 <= r["a"] < n_cand):
        raise Violation(f"reply.a: {r.get('a')!r} outside 0..{n_cand - 1}")


def validate_stream(lines):
    """lines: iterable of JSON strings.  Returns (n_consults, first_error or None)."""
    hello, n_cand, n = None, None, 0
    for ln, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except json.JSONDecodeError as e:
            return n, f"line {ln}: not JSON ({e})"
        try:
            if "t" in m and m["t"] == "hello":
                hello = validate_hello(m)
            elif "t" in m and m["t"] == "consult":
                if hello is None:
                    raise Violation("consult before hello")
                n_cand = validate_consult(m, hello)
                n += 1
            elif "a" in m:
                if n_cand is None:
                    raise Violation("reply before any consult")
                validate_reply(m, n_cand)
            elif m.get("t") in ("end", "stats") or "ok" in m:
                pass
            else:
                raise Violation(f"unknown message {sorted(m)[:5]}")
        except Violation as v:
            return n, f"line {ln}: {v}"
    if hello is None:
        return n, "no hello in stream"
    return n, None


def json_schema():
    """Structural part only (draft-07); semantics live in validate_consult."""
    def arr(item, min_items=0):
        return {"type": "array", "items": item, "minItems": min_items}
    num = {"type": "number"}
    def row(w):
        return {"type": "array", "items": num, "minItems": w, "maxItems": w}
    ints = arr({"type": "integer"})
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "WIRE-V7 consult (structural)",
        "type": "object",
        "required": ["t", "wire", "g", "e", "r", "c", "v7_game", "v7_players", "v7_ent", "v7_ent_name",
                     "v7_ent_token", "v7_edges", "v7_cand_type", "v7_cand", "v7_cand_refers", "v7_ctr"],
        "properties": {
            "t": {"const": "consult"}, "wire": {"const": WIRE},
            "g": row(V6["gdim"]), "e": arr(row(V6["edim"])), "r": arr(ints), "c": arr(row(V6["cdim"]), 1),
            "oe": arr(arr(num)), "phi": num,
            "v7_game": row(DIMS["game"]), "v7_players": {"type": "array", "items": row(DIMS["player"]), "minItems": 2, "maxItems": 2},
            "v7_ent": arr(row(DIMS["ent"])), "v7_ent_name": arr({"type": "string"}),
            "v7_ent_token": arr({"enum": [0, 1]}), "v7_ent_id": ints,
            "v7_edges": arr({"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3}),
            "v7_cand_type": arr({"type": "integer", "minimum": 0, "maximum": CTYPES - 1}, 1),
            "v7_cand": arr(row(DIMS["cand"]), 1), "v7_cand_refers": arr(ints, 1),
            "v7_opp_hand": arr(row(DIMS["opp_hand"])), "v7_opp_hand_name": arr({"type": ["string", "null"]}),
            "v7_opp_deck": arr(row(DIMS["opp_deck"])), "v7_opp_deck_name": arr({"type": "string"}),
            "v7_opp_actions": arr(row(DIMS["opp_action"])), "v7_opp_action_refers": arr(ints),
            "v7_ctr": {"type": "object", "required": ["entityTrunc"]},
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--emit-schema")
    args = ap.parse_args()
    if args.emit_schema:
        with open(args.emit_schema, "w", encoding="utf-8") as f:
            json.dump(json_schema(), f, indent=1)
        print(f"schema -> {args.emit_schema}")
    bad = 0
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            n, err = validate_stream(f)
        if err:
            bad += 1
            print(f"FAIL {path}: {n} consults ok, then {err}")
        else:
            print(f"ok   {path}: {n} consults")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
