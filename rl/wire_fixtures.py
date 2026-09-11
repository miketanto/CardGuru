"""Phase 0a (v7 plan §2): synthetic, schema-valid WIRE-V7 streams for Lane C
to build against before Lane B emits anything, plus deliberately broken
streams the validator must reject naming the field.

Writes rl/fixtures/v7/:
  valid_<decision>.jsonl   hello + 20 consults + replies, one file per
                           decision type (pass, land, spell, activate,
                           target, attack, block), the last three with
                           opponent tokens present
  broken_<what>.jsonl      one violation each (see BROKEN)
  schema.json              structural JSON Schema from wire_validate.py

Names are real cards_v1 names (so the server's id resolution works on the
fixtures); numbers are random but consistent with the tables in
WIRE-V7.md (one-hots, index spaces, refers coverage).  Deterministic
(seed 0).  No engine involved: fixtures are the contract, not a game.

Run:  python rl/wire_fixtures.py
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wire_validate as W                                   # noqa: E402

OUT = os.path.join(HERE, "fixtures", "v7")
DECISIONS = ["pass", "land", "spell", "activate", "target", "attack", "block"]
CARDS_INDEX = os.path.join(HERE, "artifacts", "cards_v1", "index.json")


def hello(episodes=4):
    return {"t": "hello", "mode": "train", "episodes": episodes, "sdim": 32, "cdim": 94, "phi": 0,
            "gdim": 16, "edim": 48, "emax": 96, "rtypes": 6,
            "wire": 7, "card_emb": "card_emb_v8", "d_c": 128, "v7_dims": dict(W.DIMS),
            "v7_rtypes": W.RTYPES, "v7_ctypes": W.CTYPES, "v7_zones": W.ZONES, **W.MAXES,
            "v7_decks": {"me": [["Lightning Bolt", 4], ["Mountain", 20]], "opp": [["Counterspell", 4], ["Island", 20]]}}


def _names():
    try:
        idx = json.load(open(CARDS_INDEX, encoding="utf-8"))["names"]
        names = [n for n in idx if not n.startswith("token:") and " // " not in n]
        random.Random(1).shuffle(names)
        return [n.title() for n in names[:400]]
    except FileNotFoundError:
        return ["Lightning Bolt", "Counterspell", "Grizzly Bears", "Island", "Mountain"]


NAMES = _names()


def onehot(n, k):
    v = [0.0] * n
    v[k] = 1.0
    return v


def consult(g, decision, with_opp):
    dtype = DECISIONS.index(decision)
    n_ent = g.randint(6, 30)
    ents, names, toks, ids = [], [], [], []
    zones = []
    for i in range(n_ent):
        z = g.choice([0, 0, 0, 1, 2, 3, 4, 5]) if i > 1 else 0          # mostly battlefield
        zones.append(z)
        row = [0.0] * W.DIMS["ent"]
        row[0:7] = onehot(7, z)
        row[7] = float(g.random() < 0.5)                                 # mine
        row[8] = 0.0
        row[9] = (g.randint(0, 3) / 4.0) if z == 2 else 0.0
        creature = g.random() < 0.6
        if creature:
            p, t = g.randint(0, 6), g.randint(1, 6)
            row[10], row[11] = p / 6, t / 6
            dmg = g.randint(0, t - 1)
            row[12], row[13] = dmg / 6, (t - dmg) / 6
            row[14], row[15] = p / 6, t / 6
        row[17] = g.randint(0, 6) / 6
        row[22] = float(g.random() < 0.3)                                # tapped
        row[29] = float(creature)
        for j in range(34, 52):
            row[j] = float(g.random() < 0.08)
        row[52] = float(z == 1 and g.random() < 0.5)                     # castable (hand only)
        row[55] = float(creature and z == 0 and row[22] == 0)            # can attack
        row[56] = row[55]
        ents.append(row)
        names.append(g.choice(NAMES))
        toks.append(int(g.random() < 0.1))
        ids.append(-1)
    n_tok = W.ENT0 + n_ent
    edges = []
    for i, z in enumerate(zones):
        if z == 0:
            edges.append([W.ME if ents[i][7] == 1 else W.OPP, W.ENT0 + i, 4])   # controls
    creatures_bf = [i for i, z in enumerate(zones) if z == 0 and ents[i][29] == 1]
    if decision == "block" and len(creatures_bf) >= 2:
        att, blk = creatures_bf[0], creatures_bf[1]
        edges.append([W.ENT0 + att, W.ME, 2])                                   # attacking me
        edges.append([W.ENT0 + blk, W.ENT0 + att, 6])                            # can_block
    stack = [i for i, z in enumerate(zones) if z == 2]
    for a, b in zip(stack, stack[1:]):
        edges.append([W.ENT0 + a, W.ENT0 + b, 7])                               # stack_above
    # candidates
    n_c = g.randint(2, 8)
    ctype, cf, cr = [], [], []
    for k in range(n_c):
        t = 0 if k == 0 else dtype if dtype != 0 else 7                          # first candidate is PASS
        row = [0.0] * W.DIMS["cand"]
        row[0:8] = onehot(8, t)
        refers = []
        if t in (1, 2, 3):
            i = g.randrange(n_ent); refers = [W.ENT0 + i]
            row[8] = g.randint(0, 6) / 6; row[10] = 1.0
        elif t == 4:
            if g.random() < 0.3:
                refers = [g.choice([W.ME, W.OPP])]; row[8] = 1.0
            else:
                i = g.randrange(n_ent); refers = [W.ENT0 + i]; row[11] = ents[i][29]
        elif t == 5:
            pool = creatures_bf or [0]
            refers = [W.ENT0 + i for i in g.sample(pool, g.randint(1, min(3, len(pool))))]
            row[8] = g.randint(0, 10) / 10
        elif t == 6:
            pool = creatures_bf or [0, 1]
            refers = [W.ENT0 + i for i in pool[:2]]
            row[8] = g.randint(0, 6) / 6
        elif t == 7:
            refers = [W.ENT0 + g.randrange(n_ent)]
        ctype.append(t); cf.append(row); cr.append(refers)
    game = [0.0] * W.DIMS["game"]
    game[0] = g.randint(1, 20) / 30; game[1] = float(g.random() < 0.5)
    game[2:10] = onehot(8, {"attack": 3, "block": 4}.get(decision, 2))
    game[10] = 1.0; game[11] = len(stack) / 4
    game[12:20] = onehot(8, dtype)
    game[20] = n_c / 32; game[21] = g.randint(0, 100) / 200; game[22] = 1.0; game[23] = 1.0
    players = []
    for _ in range(2):
        p = [0.0] * W.DIMS["player"]
        p[0] = g.randint(1, 20) / 20; p[2] = g.randint(0, 7) / 10; p[3] = g.randint(20, 53) / 60
        p[12] = g.randint(0, 6) / 10; p[13] = p[12]
        players.append(p)
    m = {"t": "consult", "wire": 7,
         "g": [0.0] * 16, "e": [[0.0] * 48 for _ in range(min(n_ent, 96))], "r": [], "c": [[0.0] * 94 for _ in range(n_c)],
         "v7_game": game, "v7_players": players,
         "v7_ent": ents, "v7_ent_name": names, "v7_ent_token": toks, "v7_ent_id": ids,
         "v7_edges": edges, "v7_cand_type": ctype, "v7_cand": cf, "v7_cand_refers": cr,
         "v7_ctr": {"entityTrunc": 0, "unknownId": 0}}
    if with_opp:
        oh, ohn = [], []
        for _ in range(g.randint(0, 7)):
            known = g.random() < 0.3
            row = [0.0] * 8
            row[0:4] = onehot(4, g.randrange(4)); row[4] = g.randint(0, 8) / 10; row[5] = float(known); row[6] = float(known)
            oh.append(row); ohn.append(g.choice(NAMES) if known else None)
        od, odn = [], []
        for _ in range(g.randint(5, 20)):
            od.append([g.randint(1, 4) / 4, g.random() * 0.1, float(g.random() < 0.3), g.randint(0, 6) / 6, float(g.random() < 0.4), 0.0])
            odn.append(g.choice(NAMES))
        oa, oar = [], []
        for _ in range(g.randint(0, 5)):
            row = [0.0] * 8
            row[0:7] = onehot(7, g.randrange(7)); row[7] = g.randint(0, 20) / 20
            oa.append(row); oar.append([W.ENT0 + g.randrange(n_ent)] if g.random() < 0.7 else [])
        m.update({"v7_opp_hand": oh, "v7_opp_hand_name": ohn, "v7_opp_deck": od, "v7_opp_deck_name": odn,
                  "v7_opp_actions": oa, "v7_opp_action_refers": oar})
    return m


def write_stream(path, msgs):
    with open(path, "w", encoding="utf-8") as f:
        for m in msgs:
            f.write(json.dumps(m, separators=(",", ":")) + "\n")


def valid_stream(decision, seed, n=20, with_opp=False):
    g = random.Random(seed)
    out = [hello()]
    for _ in range(n):
        c = consult(g, decision, with_opp)
        out.append(c)
        out.append({"a": g.randrange(len(c["v7_cand_type"]))})
    out.append({"t": "end", "r": 1.0})
    return out


def _break(msgs, what):
    """Return a copy of a valid stream with exactly one violation."""
    msgs = json.loads(json.dumps(msgs))
    h, c = msgs[0], msgs[1]
    if what == "hello_no_wire":
        del h["wire"]
    elif what == "hello_dims":
        h["v7_dims"]["ent"] = 63
    elif what == "ent_width":
        c["v7_ent"][0].append(0.0)
    elif what == "ent_zone_onehot":
        c["v7_ent"][0][0] = 1.0; c["v7_ent"][0][1] = 1.0
    elif what == "edge_type":
        c["v7_edges"].append([W.ENT0, W.ENT0 + 1, W.RTYPES])
    elif what == "edge_endpoint":
        c["v7_edges"].append([W.ENT0, W.ENT0 + len(c["v7_ent"]) + 5, 0])
    elif what == "refers_out_of_range":
        c["v7_cand_refers"][1] = [W.ENT0 + len(c["v7_ent"])]
    elif what == "refers_empty_nonpass":
        c["v7_cand_refers"][1] = []
    elif what == "cand_type_mismatch":
        c["v7_cand"][1][0:8] = [1.0] + [0.0] * 7
    elif what == "nan":
        c["v7_game"][0] = float("nan")
    elif what == "name_missing":
        c["v7_ent_name"] = c["v7_ent_name"][:-1]
    elif what == "reply_range":
        msgs[2]["a"] = len(c["v7_cand_type"])
    elif what == "opp_known_flag":
        c["v7_opp_hand"] = [[1.0, 0, 0, 0, 0.1, 1.0, 1.0, 0.0]]; c["v7_opp_hand_name"] = [None]
    elif what == "v6_key_missing":
        del c["g"]
    else:
        raise ValueError(what)
    return msgs


BROKEN = ["hello_no_wire", "hello_dims", "ent_width", "ent_zone_onehot", "edge_type", "edge_endpoint",
          "refers_out_of_range", "refers_empty_nonpass", "cand_type_mismatch", "nan", "name_missing",
          "reply_range", "opp_known_flag", "v6_key_missing"]


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, d in enumerate(DECISIONS):
        write_stream(os.path.join(OUT, f"valid_{d}.jsonl"), valid_stream(d, seed=i, with_opp=(i >= 4)))
    base = valid_stream("spell", seed=100, n=3, with_opp=True)
    for what in BROKEN:
        write_stream(os.path.join(OUT, f"broken_{what}.jsonl"), _break(base, what))
    with open(os.path.join(OUT, "schema.json"), "w", encoding="utf-8") as f:
        json.dump(W.json_schema(), f, indent=1)
    print(f"wrote {len(DECISIONS)} valid + {len(BROKEN)} broken streams + schema.json -> {OUT}")


if __name__ == "__main__":
    main()
