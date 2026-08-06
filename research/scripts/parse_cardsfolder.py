#!/usr/bin/env python3
"""Parse Forge's cardsfolder DSL into per-card ability graphs and mine the ontology.

Outputs (to research/data/):
  cards.jsonl        - one JSON object per card face: metadata + ability graph
  ontology.json      - mined vocabulary with frequency counts
  stats.json         - coverage / Count$ dependency stats
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

CARDSFOLDER = sys.argv[1] if len(sys.argv) > 1 else "/home/user/forge-src/forge-gui/res/cardsfolder"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "/home/user/CardGuru/research/data"

# Top-level line keys we understand. Everything else is recorded as "other".
ABILITY_KEYS = {"A", "T", "S", "R"}

API_RE = re.compile(r"^(SP|AB|DB)\$\s*(\w+)")

def parse_params(body):
    """Parse 'X$ v | Y$ w' pipe-delimited params into an ordered dict."""
    params = {}
    for chunk in body.split("|"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "$" in chunk:
            k, _, v = chunk.partition("$")
            params[k.strip()] = v.strip()
        else:
            params[chunk] = True
    return params

def parse_face(lines, source_file):
    card = {
        "name": None, "manaCost": None, "types": None, "pt": None,
        "oracle": None, "loyalty": None, "file": source_file,
        "abilities": [],   # nodes: {kind, api|mode, params}
        "svars": {},       # name -> raw value
        "keywords": [],
        "other": {},
    }
    for line in lines:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        key, _, rest = line.partition(":")
        if key == "Name":
            card["name"] = rest
        elif key == "ManaCost":
            card["manaCost"] = rest
        elif key == "Types":
            card["types"] = rest
        elif key == "PT":
            card["pt"] = rest
        elif key == "Loyalty":
            card["loyalty"] = rest
        elif key == "Oracle":
            card["oracle"] = rest
        elif key == "K":
            card["keywords"].append(rest)
        elif key == "SVar":
            name, _, val = rest.partition(":")
            card["svars"][name] = val
        elif key in ABILITY_KEYS:
            params = parse_params(rest)
            node = {"kind": key, "params": params}
            m = API_RE.match(rest)
            if m:
                node["apiKind"], node["api"] = m.group(1), m.group(2)
            card["abilities"].append(node)
        else:
            card["other"].setdefault(key, []).append(rest)
    return card

def build_graph(card):
    """Resolve SVar references into typed edges; classify SVar nodes."""
    nodes = []   # {id, kind, api/mode, params}
    edges = []   # {src, dst, type}
    svar_nodes = {}

    # Ability-line nodes
    for i, ab in enumerate(card["abilities"]):
        nid = f"ab{i}"
        node = {"id": nid, "kind": ab["kind"], "params": ab["params"]}
        if "api" in ab:
            node["api"] = ab["api"]
            node["apiKind"] = ab["apiKind"]
        elif "Mode" in ab["params"]:
            node["mode"] = ab["params"]["Mode"]
        nodes.append(node)

    # SVar nodes that are themselves abilities (DB$ ...) or static defs (Mode$ ...)
    for name, val in card["svars"].items():
        m = API_RE.match(val)
        params = parse_params(val)
        if m:
            node = {"id": name, "kind": "SVar", "api": m.group(2), "apiKind": m.group(1), "params": params}
        elif val.startswith("Mode$"):
            node = {"id": name, "kind": "SVar", "mode": params.get("Mode"), "params": params}
        elif val.startswith("Count$"):
            node = {"id": name, "kind": "SVarCount", "count": val[len("Count$"):]}
        else:
            node = {"id": name, "kind": "SVarValue", "value": val}
        svar_nodes[name] = node
        nodes.append(node)

    # Edges: params whose values name SVars
    EDGE_PARAMS = ("Execute", "SubAbility", "StaticAbilities", "AddTrigger",
                   "AddStaticAbility", "AddReplacementEffects", "ReplacementResult",
                   "Triggers", "svars")
    for node in nodes:
        params = node.get("params") or {}
        for pk, pv in params.items():
            if not isinstance(pv, str):
                continue
            for target in re.split(r"[,&\s]+", pv):
                if target in svar_nodes:
                    etype = pk if pk in EDGE_PARAMS else f"ref:{pk}"
                    edges.append({"src": node["id"], "dst": target, "type": etype})
    return nodes, edges

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    ontology = {
        "api": Counter(),          # SP$/AB$/DB$ effect names
        "api_by_kind": defaultdict(Counter),
        "trigger_modes": Counter(),
        "static_modes": Counter(),
        "replacement_events": Counter(),
        "keywords": Counter(),
        "param_keys": Counter(),
        "param_keys_by_api": defaultdict(Counter),
        "count_functions": Counter(),  # Count$<Fn> first token
    }
    stats = Counter()
    files = []
    for root, dirs, fnames in os.walk(CARDSFOLDER):
        # skip helper dirs? keep all .txt except tokens (none here) & scripts
        for fn in fnames:
            if fn.endswith(".txt"):
                files.append(os.path.join(root, fn))
    files.sort()
    stats["files"] = len(files)

    out = open(os.path.join(OUTDIR, "cards.jsonl"), "w")
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        rel = os.path.relpath(path, CARDSFOLDER)
        # Split multi-face files
        face_chunks = re.split(r"\n\s*(?:ALTERNATE|SPECIALIZE:?\w*)\s*\n", content)
        for chunk in face_chunks:
            lines = chunk.splitlines()
            if not any(l.startswith("Name:") for l in lines):
                continue
            card = parse_face(lines, rel)
            stats["faces"] += 1
            nodes, edges = build_graph(card)
            has_ability = bool(card["abilities"]) or bool(card["keywords"]) or any(
                n["kind"] == "SVar" for n in nodes)
            if card["abilities"] or card["keywords"]:
                stats["faces_with_scripting"] += 1
            else:
                stats["faces_no_ability_lines"] += 1
                # vanilla if oracle is empty or reminder-only
                if not card["oracle"]:
                    stats["faces_vanilla_empty_oracle"] += 1

            # Count$ dependency
            uses_count = False
            for name, val in card["svars"].items():
                if val.startswith("Count$"):
                    uses_count = True
                    fn = val[len("Count$"):]
                    fn_token = re.split(r"[ /$.]", fn)[0]
                    ontology["count_functions"][fn_token] += 1
            if uses_count:
                stats["faces_using_count"] += 1

            # Mine vocabulary
            for node in nodes:
                params = node.get("params") or {}
                if "api" in node:
                    ontology["api"][node["api"]] += 1
                    ontology["api_by_kind"][node.get("apiKind", "?")][node["api"]] += 1
                    for pk in params:
                        ontology["param_keys"][pk] += 1
                        ontology["param_keys_by_api"][node["api"]][pk] += 1
                elif "mode" in node and node["mode"]:
                    if node["kind"] == "T":
                        ontology["trigger_modes"][node["mode"]] += 1
                    elif node["kind"] in ("S", "SVar"):
                        ontology["static_modes"][node["mode"]] += 1
                    for pk in params:
                        ontology["param_keys"][pk] += 1
                if node["kind"] == "R":
                    ev = params.get("Event")
                    if ev:
                        ontology["replacement_events"][ev] += 1
                    for pk in params:
                        ontology["param_keys"][pk] += 1
            for kw in card["keywords"]:
                ontology["keywords"][kw.split(":")[0].split("$")[0].strip()] += 1

            rec = {
                "name": card["name"], "manaCost": card["manaCost"],
                "types": card["types"], "pt": card["pt"], "oracle": card["oracle"],
                "file": rel, "keywords": card["keywords"],
                "nodes": nodes, "edges": edges,
            }
            out.write(json.dumps(rec) + "\n")
    out.close()

    def top(c, n=None):
        return dict(c.most_common(n))
    onto_out = {
        "api": top(ontology["api"]),
        "api_by_kind": {k: top(v) for k, v in ontology["api_by_kind"].items()},
        "trigger_modes": top(ontology["trigger_modes"]),
        "static_modes": top(ontology["static_modes"]),
        "replacement_events": top(ontology["replacement_events"]),
        "keywords": top(ontology["keywords"]),
        "param_keys": top(ontology["param_keys"]),
        "count_functions": top(ontology["count_functions"]),
        "param_keys_by_api_top": {k: top(v, 15) for k, v in
                                  sorted(ontology["param_keys_by_api"].items())},
    }
    with open(os.path.join(OUTDIR, "ontology.json"), "w") as f:
        json.dump(onto_out, f, indent=1)
    with open(os.path.join(OUTDIR, "stats.json"), "w") as f:
        json.dump(dict(stats), f, indent=1)
    print(json.dumps(dict(stats), indent=1))
    print("distinct API effects:", len(ontology["api"]))
    print("distinct trigger modes:", len(ontology["trigger_modes"]))
    print("distinct static modes:", len(ontology["static_modes"]))
    print("distinct replacement events:", len(ontology["replacement_events"]))
    print("distinct keywords:", len(ontology["keywords"]))
    print("distinct param keys:", len(ontology["param_keys"]))
    print("distinct Count$ functions:", len(ontology["count_functions"]))

if __name__ == "__main__":
    main()
