"""Parser for Forge's cardsfolder DSL into per-face ability graphs.

Node kinds:
  A / T / S / R  - ability lines (spell/activated, triggered, static, replacement)
  K              - keyword lines, structured as {name, args}; Chapter/Class/etc.
                   keyword args that reference SVars become edges
  SVar           - SVar whose value is an ability (DB$/AB$/SP$) or a Mode$ definition
  SVarCount      - SVar holding a Count$ expression (opaque dynamic quantity)
  SVarValue      - any other SVar (plain values, AI hints, script constants)

Edge types: the referencing parameter name, verbatim (Execute, SubAbility,
StaticAbilities, AddTrigger, ...). References found in non-standard params keep
the prefix "ref:" so structural queries can distinguish intentional chain edges
from incidental mentions.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

ABILITY_KEYS = ("A", "T", "S", "R")
API_RE = re.compile(r"^(SP|AB|DB)\$\s*(\w+)")
FACE_SPLIT_RE = re.compile(r"\n\s*(ALTERNATE|SPECIALIZE:?\w*)\s*\n")

# Parameters whose values are (lists of) SVar names forming the ability chain.
CHAIN_PARAMS = {
    "Execute", "SubAbility", "StaticAbilities", "AddTrigger", "AddStaticAbility",
    "AddReplacementEffects", "ReplacementResult", "Triggers", "AddAbility",
    "Abilities", "GainsAbilitiesOf", "Chapter", "Class",
    # promoted from empirical ref:-edge mining over the full pool (params whose
    # values name ability SVars and mean "then/instead execute"):
    "Choices", "ReplaceWith", "RepeatSubAbility", "ETBReplacement",
    "TrueSubAbility", "FalseSubAbility", "WinSubAbility", "LoseSubAbility",
    "ChosenPile", "UnchosenPile", "StaticEffect", "Visit",
}
# Keyword names whose colon-args reference SVar lists (sagas, classes, ...).
KEYWORD_SVAR_LISTS = {"Chapter", "Class"}

SVAR_LIST_SPLIT = re.compile(r"[,&]")
NAME_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass
class Face:
    name: str | None = None
    mana_cost: str | None = None
    types: str | None = None
    pt: str | None = None
    loyalty: str | None = None
    oracle: str | None = None
    file: str | None = None
    face_index: int = 0
    alternate_mode: str | None = None   # Split/Adventure/Meld/... (whole card)
    meld_pair: str | None = None
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    other: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "name": self.name, "manaCost": self.mana_cost, "types": self.types,
            "pt": self.pt, "loyalty": self.loyalty, "oracle": self.oracle,
            "file": self.file, "faceIndex": self.face_index,
            "alternateMode": self.alternate_mode, "meldPair": self.meld_pair,
            "nodes": self.nodes, "edges": self.edges, "other": self.other,
        }


def parse_params(body: str) -> dict:
    """Parse 'X$ v | Y$ w | Flag' into a dict (bare tokens become True)."""
    params: dict = {}
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


def parse_keyword(rest: str) -> dict:
    """Structure a K: line. 'Dash:1 R' -> {name: Dash, args: ['1 R']};
    'Class:2:1 G:AddTrigger$ X' -> {name: Class, args: ['2','1 G','AddTrigger$ X']}."""
    parts = rest.split(":")
    name = parts[0].strip()
    return {"name": name, "args": [p.strip() for p in parts[1:]], "raw": rest}


def _parse_face(lines: list[str], source_file: str, face_index: int) -> Face:
    face = Face(file=source_file, face_index=face_index)
    svars: dict[str, str] = {}
    keywords: list[dict] = []
    abilities: list[dict] = []

    for line in lines:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        key, _, rest = line.partition(":")
        if key == "Name":
            face.name = rest
        elif key == "ManaCost":
            face.mana_cost = rest
        elif key == "Types":
            face.types = rest
        elif key == "PT":
            face.pt = rest
        elif key == "Loyalty":
            face.loyalty = rest
        elif key == "Oracle":
            face.oracle = rest
        elif key == "AlternateMode":
            face.alternate_mode = rest.strip()
        elif key == "MeldPair":
            face.meld_pair = rest.strip()
        elif key == "K":
            keywords.append(parse_keyword(rest))
        elif key == "SVar":
            name, _, val = rest.partition(":")
            svars[name] = val
        elif key in ABILITY_KEYS:
            node = {"kind": key, "params": parse_params(rest)}
            m = API_RE.match(rest)
            if m:
                node["apiKind"], node["api"] = m.group(1), m.group(2)
            abilities.append(node)
        else:
            face.other.setdefault(key, []).append(rest)

    _build_graph(face, abilities, keywords, svars)
    return face


def _svar_node(name: str, val: str) -> dict:
    m = API_RE.match(val)
    params = parse_params(val)
    if m:
        return {"id": name, "kind": "SVar", "api": m.group(2),
                "apiKind": m.group(1), "params": params}
    if val.startswith("Mode$"):
        return {"id": name, "kind": "SVar", "mode": params.get("Mode"), "params": params}
    if val.startswith("Count$"):
        return {"id": name, "kind": "SVarCount", "count": val[len("Count$"):]}
    return {"id": name, "kind": "SVarValue", "value": val}


def _build_graph(face: Face, abilities: list[dict], keywords: list[dict],
                 svars: dict[str, str]) -> None:
    nodes: list[dict] = []
    edges: list[dict] = []

    for i, ab in enumerate(abilities):
        node = {"id": f"ab{i}", **ab}
        if "api" not in node and "Mode" in node.get("params", {}):
            node["mode"] = node["params"]["Mode"]
        nodes.append(node)

    for i, kw in enumerate(keywords):
        nodes.append({"id": f"kw{i}", "kind": "K", "keyword": kw["name"],
                      "args": kw["args"], "raw": kw["raw"]})

    svar_ids = set(svars)
    for name, val in svars.items():
        nodes.append(_svar_node(name, val))

    def add_ref_edges(src_id: str, pk: str, pv: str) -> None:
        for target in SVAR_LIST_SPLIT.split(pv):
            target = target.strip()
            if target in svar_ids:
                etype = pk if pk in CHAIN_PARAMS else f"ref:{pk}"
                edges.append({"src": src_id, "dst": target, "type": etype})

    # Edges out of ability/SVar nodes via params
    for node in nodes:
        params = node.get("params")
        if not params:
            continue
        for pk, pv in params.items():
            if isinstance(pv, str):
                add_ref_edges(node["id"], pk, pv)

    # Edges out of keyword nodes: embedded 'X$ Name' args (Class levels) and
    # bare SVar-name lists (Chapter).
    for node in nodes:
        if node["kind"] != "K":
            continue
        for arg in node.get("args", []):
            if "$" in arg:
                pk, _, pv = arg.partition("$")
                add_ref_edges(node["id"], pk.strip(), pv.strip())
            elif node["keyword"] in KEYWORD_SVAR_LISTS or all(
                    NAME_TOKEN.match(t.strip()) and t.strip() in svar_ids
                    for t in arg.split(",") if t.strip()):
                add_ref_edges(node["id"], node["keyword"], arg)

    face.nodes = nodes
    face.edges = edges


def parse_file(path: str, relroot: str | None = None) -> list[Face]:
    """Parse one card script file into its faces."""
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    rel = os.path.relpath(path, relroot) if relroot else path
    faces = []
    chunks = FACE_SPLIT_RE.split(content)
    # FACE_SPLIT_RE keeps the separator tokens at odd indices; drop them.
    face_texts = chunks[0::2]
    alt_mode = None
    for idx, text in enumerate(face_texts):
        lines = text.splitlines()
        if not any(l.startswith("Name:") for l in lines):
            continue
        face = _parse_face(lines, rel, idx)
        if face.alternate_mode:
            alt_mode = face.alternate_mode
        faces.append(face)
    for face in faces:                       # AlternateMode appears on face 0 only
        face.alternate_mode = alt_mode
    return faces


def parse_cardsfolder(root: str):
    """Yield Face objects for every card script under root."""
    paths = []
    for dirpath, _dirs, fnames in os.walk(root):
        for fn in fnames:
            if fn.endswith(".txt"):
                paths.append(os.path.join(dirpath, fn))
    paths.sort()
    for path in paths:
        yield from parse_file(path, relroot=root)
