"""v5 graph channel (design L0 "v1.5"): the ability tree itself, not its
68-column readout.

Every Forge face is a small graph: ability nodes (A activated / spell,
T trigger, S static, R replacement, K keyword, SVar sub-abilities,
SVarCount / SVarValue variables) with typed edges (Execute, SubAbility,
ref:<param> ...).  The conditions the readout bag cannot express live in
the node params: Spell Snare is `Counter` with `ValidTgts: Card.cmcEQ2`,
Force Spike is `Counter` with `UnlessCost: 1`; Elektra and Ravenous
Chupacabra share the subtree `T ChangesZone -> SVar Destroy
(Creature.OppCtrl)`.

Tokenisation (deterministic, hash-based, no fitted vocabulary):
  node   = kind ⊕ api ⊕ apiKind ⊕ mode ⊕ keyword          (small vocabs, exact)
         + mean over structural params of  E_key[key] ⊙ E_val[piece]
           where a value like "Creature.OppCtrl+powerLE3" is split into
           pieces ("Creature", "OppCtrl", "powerLE", "[N3]") and numbers
           are bucketed exactly as in the text channel; description-like
           params (SpellDescription, TgtPrompt, ...) are dropped — text is
           the text channel's job.
  edges  = [N, N] edge-type id (hashed), used as an attention bias.

`build_trees()` encodes every cards_v1 face id once (dataset records +
tokenscripts + extra_scripts) and caches rl/artifacts/cards_v1/trees.pt.
`struct_key(tree, printed)` is the canonical string the v2+ objective
uses to decide which cards count as structurally identical.
"""
import gzip
import hashlib
import json
import os
import re
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)
from data import bucket_number, CARDS_V1                         # noqa: E402

KINDS = ["<pad>", "A", "T", "S", "R", "K", "SVar", "SVarCount", "SVarValue", "<other>"]
KIND_ID = {k: i for i, k in enumerate(KINDS)}
API_KINDS = ["<none>", "SP", "AB", "DB", "<other>"]
DROP_PARAMS = {"SpellDescription", "TriggerDescription", "TgtPrompt", "Description", "ValidTgtsDesc",
               "StackDescription", "AILogic", "AIPreference", "PrecostDesc", "CostDesc", "StaticAbilities",
               "SVars", "DefinedDesc", "ValidDesc", "DescriptionDefined"}
MAX_NODES = 24
MAX_PAIRS = 24            # (key, value-piece) pairs per node
N_KEY_BUCKETS = 2048
N_VAL_BUCKETS = 16384
N_EDGE_BUCKETS = 128
N_API_BUCKETS = 512
N_MODE_BUCKETS = 512
N_KW_BUCKETS = 1024

_SPLIT = re.compile(r"[.,+ /<>$:|;]+")
_NUM = re.compile(r"\d+")


def _h(s, n):
    """Stable hash into 1..n-1 (0 is padding)."""
    return 1 + int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16) % (n - 1)


def value_pieces(v):
    v = str(v)
    v = _NUM.sub(lambda m: bucket_number(m.group(0)), v)
    return [p for p in _SPLIT.split(v) if p][:8]


def encode_node(n):
    kind = n.get("kind")
    p = n.get("params") or {}
    row = {
        "kind": KIND_ID.get(kind, KIND_ID["<other>"]),
        "api": _h(str(n.get("api") or p.get("SP") or p.get("DB") or p.get("AB") or ""), N_API_BUCKETS) if (n.get("api") or p.get("SP") or p.get("DB") or p.get("AB")) else 0,
        "api_kind": {"SP": 1, "AB": 2, "DB": 3}.get(n.get("apiKind") or ("SP" if "SP" in p else "AB" if "AB" in p else "DB" if "DB" in p else ""), 0),
        "mode": _h(str(p.get("Mode") or n.get("mode")), N_MODE_BUCKETS) if (p.get("Mode") or n.get("mode")) else 0,
        "kw": _h(str(n.get("keyword")), N_KW_BUCKETS) if n.get("keyword") else 0,
    }
    pairs = []
    items = list(p.items())
    if kind == "K":
        items += [("KWARG", a) for a in (n.get("args") or [])]
    if kind == "SVarCount":
        items.append(("Count", n.get("count", "")))
    if kind == "SVarValue":
        items.append(("Value", n.get("value", "")))
    for k, v in items:
        if k in DROP_PARAMS or k in ("SP", "AB", "DB", "Mode"):
            continue
        kid = _h(k, N_KEY_BUCKETS)
        for piece in value_pieces(v):
            pairs.append((kid, _h(piece, N_VAL_BUCKETS)))
            if len(pairs) >= MAX_PAIRS:
                break
        if len(pairs) >= MAX_PAIRS:
            break
    row["pairs"] = pairs
    return row


def canonical(n):
    p = n.get("params") or {}
    keep = {k: value_pieces(v) for k, v in sorted(p.items()) if k not in DROP_PARAMS}
    return json.dumps([n.get("kind"), n.get("api"), n.get("apiKind"), n.get("mode"), n.get("keyword"),
                       n.get("args"), n.get("count"), n.get("value"), keep], sort_keys=True)


def encode_tree(rec):
    """rec: a Forge record (nodes, edges).  Returns a dict of small tensors."""
    nodes = (rec.get("nodes") or [])[:MAX_NODES]
    ids = {n.get("id"): i for i, n in enumerate(nodes)}
    N = max(1, len(nodes))
    kind = torch.zeros(N, dtype=torch.long); api = torch.zeros(N, dtype=torch.long)
    api_kind = torch.zeros(N, dtype=torch.long); mode = torch.zeros(N, dtype=torch.long)
    kw = torch.zeros(N, dtype=torch.long)
    pairs = torch.zeros(N, MAX_PAIRS, 2, dtype=torch.long)
    for i, n in enumerate(nodes):
        r = encode_node(n)
        kind[i], api[i], api_kind[i], mode[i], kw[i] = r["kind"], r["api"], r["api_kind"], r["mode"], r["kw"]
        for j, (a, b) in enumerate(r["pairs"]):
            pairs[i, j, 0], pairs[i, j, 1] = a, b
    edges = torch.zeros(N, N, dtype=torch.long)
    for e in rec.get("edges") or []:
        s, d = ids.get(e.get("src")), ids.get(e.get("dst"))
        if s is not None and d is not None:
            edges[s, d] = _h(str(e.get("type")), N_EDGE_BUCKETS)
    key = hashlib.sha1("|".join(sorted(canonical(n) for n in nodes)).encode("utf-8")).hexdigest()[:16]
    return {"kind": kind, "api": api, "api_kind": api_kind, "mode": mode, "kw": kw,
            "pairs": pairs, "edges": edges, "n": len(nodes), "key": key}


def collate_trees(trees):
    B = len(trees)
    N = max(max(t["kind"].shape[0] for t in trees), 1)
    out = {k: torch.zeros(B, N, dtype=torch.long) for k in ("kind", "api", "api_kind", "mode", "kw")}
    out["pairs"] = torch.zeros(B, N, MAX_PAIRS, 2, dtype=torch.long)
    out["edges"] = torch.zeros(B, N, N, dtype=torch.long)
    out["mask"] = torch.zeros(B, N, dtype=torch.bool)
    for b, t in enumerate(trees):
        n = t["kind"].shape[0]
        for k in ("kind", "api", "api_kind", "mode", "kw"):
            out[k][b, :n] = t[k]
        out["pairs"][b, :n] = t["pairs"]
        out["edges"][b, :n, :n] = t["edges"]
        out["mask"][b, :max(1, t["n"])] = True          # an empty tree keeps one (all-zero) node
    return out


# --- v8: the ability tree serialised as text (UniXcoder-style, CARDEMB-RESEARCH.md §2c) ---

_DIGITS = re.compile(r"\d+")


def script_text(rec, max_chars=1200):
    """Flatten a Forge record's ability nodes into one string the pretrained
    text encoder reads next to the oracle text.  Node ids that other nodes
    reference (SVar names) are kept as literal tokens so Execute=TrigDestroy
    and the TrigDestroy node share a token; description params are dropped;
    numbers are bucketed exactly as in the oracle text channel."""
    parts = []
    for n in rec.get("nodes") or []:
        kind = n.get("kind")
        p = n.get("params") or {}
        head = [str(kind)]
        nid = str(n.get("id") or "")
        if nid and not nid.startswith(("ab", "kw")):
            head.append(nid)
        api = n.get("api") or p.get("SP") or p.get("AB") or p.get("DB")
        if api:
            head.append(str(api))
        mode = p.get("Mode") or n.get("mode")
        if mode:
            head.append("Mode=" + str(mode))
        if n.get("keyword"):
            head.append("Keyword=" + str(n["keyword"]) + ("(" + " ".join(map(str, n.get("args") or [])) + ")" if n.get("args") else ""))
        if kind == "SVarCount":
            head.append("Count=" + str(n.get("count")))
        if kind == "SVarValue":
            head.append("Value=" + str(n.get("value")))
        kv = [f"{k}={v}" for k, v in p.items() if k not in DROP_PARAMS and k not in ("SP", "AB", "DB", "Mode")]
        parts.append(" ".join(head + kv))
    t = " ; ".join(parts)
    t = _DIGITS.sub(lambda m: bucket_number(m.group(0)), t)
    return t[:max_chars]


def build_scripts(cards_dir=CARDS_V1, dataset_path=os.path.join(REPO, "data", "dataset.jsonl.gz"),
                  tokenscripts_dir=None, extra_dir=os.path.join(REPO, "rl", "cards", "extra_scripts"),
                  out_path=None):
    """One script string per cards_v1 face id; cached to <cards_dir>/scripts.json.gz."""
    out_path = out_path or os.path.join(cards_dir, "scripts.json.gz")
    if os.path.exists(out_path):
        with gzip.open(out_path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    by_key = {}
    for fk, fi, r in _forge_records(dataset_path, tokenscripts_dir, extra_dir):
        by_key[(fk, fi)] = r
    scripts = []
    with gzip.open(os.path.join(cards_dir, "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            f = json.loads(line)
            r = by_key.get((f.get("file"), f.get("face_index") or 0)) or {}
            scripts.append(script_text(r))
    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        json.dump(scripts, fh)
    print(f"scripts: {len(scripts)} serialised -> {out_path}")
    return scripts


# --- building the per-id cache ----------------------------------------------------

def _forge_records(dataset_path, tokenscripts_dir, extra_dir):
    """Yield (file_key, faceIndex, record) for every source cards_v1 was built from."""
    from cardguru.dataset import load
    from cardguru.answers import load_token_scripts
    from cardguru.forge_parser import parse_file
    _, recs = load(dataset_path)
    for r in recs:
        yield r.get("file") or r["name"], r.get("faceIndex") or 0, r
    for script, r in load_token_scripts(tokenscripts_dir).items():
        yield script + ".txt", 0, r
    if extra_dir and os.path.isdir(extra_dir):
        for fn in sorted(os.listdir(extra_dir)):
            if fn.endswith(".txt"):
                for face in parse_file(os.path.join(extra_dir, fn), relroot=extra_dir):
                    r = face.to_record()
                    yield "extra/" + fn, r.get("faceIndex") or 0, r


def build_trees(cards_dir=CARDS_V1, dataset_path=os.path.join(REPO, "data", "dataset.jsonl.gz"),
                tokenscripts_dir=None, extra_dir=os.path.join(REPO, "rl", "cards", "extra_scripts"),
                out_path=None):
    """Encode a tree for every cards_v1 face id; cache to <cards_dir>/trees.pt."""
    out_path = out_path or os.path.join(cards_dir, "trees.pt")
    if os.path.exists(out_path):
        return torch.load(out_path)
    by_key = {}
    for fk, fi, r in _forge_records(dataset_path, tokenscripts_dir, extra_dir):
        by_key[(fk, fi)] = r
    trees = []
    missing = 0
    with gzip.open(os.path.join(cards_dir, "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            f = json.loads(line)
            r = by_key.get((f.get("file"), f.get("face_index") or 0))
            if r is None:
                missing += 1
                r = {}
            trees.append(encode_tree(r))
    torch.save(trees, out_path)
    print(f"trees: {len(trees)} encoded, {missing} without a source record -> {out_path}")
    return trees


if __name__ == "__main__":
    import data as D
    recs, names = D.load_cards()
    scripts = build_scripts(tokenscripts_dir=os.environ.get("CARDGURU_TOKENSCRIPTS"))
    for q in ("spell snare", "force spike", "elektra, daughter of the hand", "requiting hex"):
        print(f"{recs[names[q]].name:32s} :: {scripts[names[q]][:200]}")
    trees = build_trees(tokenscripts_dir=os.environ.get("CARDGURU_TOKENSCRIPTS"))
    for q in ("spell snare", "force spike", "elektra, daughter of the hand", "ravenous chupacabra",
              "requiting hex", "cut down", "counterspell", "cancel"):
        i = names[q]
        t = trees[i]
        print(f"{recs[i].name:32s} nodes={t['n']} key={t['key']} kinds={t['kind'].tolist()} "
              f"pairs0={t['pairs'][0][:6].tolist()}")
    keys = {}
    for t in trees:
        keys.setdefault(t["key"], 0)
        keys[t["key"]] += 1
    print("distinct tree keys", len(keys), "of", len(trees))
