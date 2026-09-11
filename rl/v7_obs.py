"""Phase 4a (v7 plan §2): WIRE-V7 parse + validate on the server side.

`V7Obs` is what the v7 token builders (4b) consume: every token group as
a float tensor, card identity resolved to `cards_v1` face ids (rule 4 of
WIRE-V7.md: by name, `v7_ent_id` trusted when present), the typed edge
list as a dense (T, T) type matrix over the token index space (0 game,
1 me, 2 opp, 3.. entities), candidate `refers_to` as a (K, T) multi-hot,
and masks.  Nothing here has weights; `entattn_check.py` is untouched
because nothing here is imported by the v6 path.

    ids  = CardIds()                                  # cards_v1/index.json
    hello = check_hello_v7(msg, card_emb="card_emb_v8")
    obs  = parse_consult(msg, ids)                     # raises ValueError(reason) on a bad consult
    batch = collate([obs, ...])                        # padded tensors + masks for 4b/4g
    dims  = dims_record(hello)                         # goes into the checkpoint

CLI (gate 4a): every valid fixture parses, every broken fixture is
refused with the reason:

    python3 rl/v7_obs.py rl/fixtures/v7/*.jsonl
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass, field

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wire_validate as W                                       # noqa: E402

CARDS_INDEX = os.path.join(HERE, "artifacts", "cards_v1", "index.json")


def _norm(name):
    import unicodedata
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()


class CardIds:
    """name -> cards_v1 face id; -1 when unknown (the zero row + unknown flag)."""

    def __init__(self, path=CARDS_INDEX):
        idx = json.load(open(path, encoding="utf-8"))
        self.names = idx["names"]
        self.version = idx["version"]
        self.n = idx["n_ids"]
        self.unresolved = 0

    def resolve(self, name, token=0, given=None):
        if given is not None and given >= 0:
            return int(given)
        if name == "?" or not name:
            return -1
        k = _norm(name)
        if token:
            cid = self.names.get("token:" + k)
            if cid is None:
                cid = self.names.get(k + " token", self.names.get(k))
        else:
            cid = self.names.get(k)
            if cid is None and " // " in name:
                cid = self.names.get(_norm(name.split(" // ")[0]))
        if cid is None:
            self.unresolved += 1
            return -1
        return int(cid)


def check_hello_v7(msg, card_emb=None):
    """Raises ValueError with the reason; returns the hello dict."""
    try:
        W.validate_hello(msg)
    except W.Violation as v:
        raise ValueError(f"HANDSHAKE MISMATCH: {v}") from None
    if card_emb is not None and msg["card_emb"] != card_emb:
        raise ValueError(f"HANDSHAKE MISMATCH: engine card_emb {msg['card_emb']!r} vs server {card_emb!r}")
    return msg


def dims_record(hello):
    return {"wire": W.WIRE, "v7_dims": dict(W.DIMS), "v7_rtypes": W.RTYPES, "v7_ctypes": W.CTYPES,
            "v7_zones": W.ZONES, "card_emb": hello["card_emb"], "d_c": hello["d_c"]}


@dataclass
class V7Obs:
    game: torch.Tensor                 # [24]
    players: torch.Tensor              # [2, 16]
    ent: torch.Tensor                  # [N, 64]
    ent_id: torch.Tensor               # [N] long, -1 unknown
    ent_name: list
    edges: torch.Tensor                # [T, T] long, 0 = none, else type + 1  (T = 3 + N)
    cand_type: torch.Tensor            # [K] long
    cand: torch.Tensor                 # [K, 40]
    refers: torch.Tensor               # [K, T] float multi-hot
    opp_hand: torch.Tensor             # [H, 8]
    opp_hand_id: torch.Tensor          # [H] long, -1 unknown
    opp_deck: torch.Tensor             # [D, 6]
    opp_deck_id: torch.Tensor          # [D] long
    opp_act: torch.Tensor              # [A, 8]
    opp_act_refers: torch.Tensor       # [A, T] float
    ctr: dict = field(default_factory=dict)
    v6: dict = field(default_factory=dict)   # the untouched v6 keys (g, e, r, c, oe, phi) for the v6 path / critic

    @property
    def n_tokens(self):
        return 3 + self.ent.shape[0]


def parse_consult(msg, ids, hello=None, validate=True):
    if validate:
        try:
            W.validate_consult(msg, hello)
        except W.Violation as v:
            raise ValueError(f"bad v7 consult: {v}") from None
    f32 = lambda x: torch.tensor(x, dtype=torch.float32)          # noqa: E731
    N = len(msg["v7_ent"])
    T = 3 + N
    ent_id = torch.tensor([ids.resolve(n, t, (msg.get("v7_ent_id") or [None] * N)[i])
                           for i, (n, t) in enumerate(zip(msg["v7_ent_name"], msg["v7_ent_token"]))], dtype=torch.long)
    edges = torch.zeros(T, T, dtype=torch.long)
    for s, d, t in msg["v7_edges"]:
        edges[s, d] = t + 1
    K = len(msg["v7_cand_type"])
    refers = torch.zeros(K, T)
    for k, lst in enumerate(msg["v7_cand_refers"]):
        for x in lst:
            refers[k, x] = 1.0
    oh = msg.get("v7_opp_hand", [])
    ohn = msg.get("v7_opp_hand_name", [])
    od = msg.get("v7_opp_deck", [])
    odn = msg.get("v7_opp_deck_name", [])
    oa = msg.get("v7_opp_actions", [])
    oar = msg.get("v7_opp_action_refers", [])
    oa_ref = torch.zeros(len(oa), T)
    for j, lst in enumerate(oar):
        for x in lst:
            oa_ref[j, x] = 1.0
    return V7Obs(
        game=f32(msg["v7_game"]), players=f32(msg["v7_players"]),
        ent=f32(msg["v7_ent"]) if N else torch.zeros(0, W.DIMS["ent"]), ent_id=ent_id, ent_name=list(msg["v7_ent_name"]),
        edges=edges, cand_type=torch.tensor(msg["v7_cand_type"], dtype=torch.long), cand=f32(msg["v7_cand"]), refers=refers,
        opp_hand=f32(oh) if oh else torch.zeros(0, W.DIMS["opp_hand"]),
        opp_hand_id=torch.tensor([ids.resolve(n) if n else -1 for n in ohn], dtype=torch.long),
        opp_deck=f32(od) if od else torch.zeros(0, W.DIMS["opp_deck"]),
        opp_deck_id=torch.tensor([ids.resolve(n) for n in odn], dtype=torch.long),
        opp_act=f32(oa) if oa else torch.zeros(0, W.DIMS["opp_action"]), opp_act_refers=oa_ref,
        ctr=dict(msg.get("v7_ctr", {})),
        v6={k: msg[k] for k in ("g", "e", "r", "c", "oe", "phi") if k in msg},
    )


def collate(obs_list, emax=None, kmax=None):
    """Pad a list of V7Obs to common sizes; returns tensors + boolean masks.
    Token index space per row: 0 game, 1 me, 2 opp, 3..3+N-1 entities, rest padding."""
    B = len(obs_list)
    N = emax or max(o.ent.shape[0] for o in obs_list)
    K = kmax or max(o.cand.shape[0] for o in obs_list)
    H = max([o.opp_hand.shape[0] for o in obs_list] + [1])
    Dk = max([o.opp_deck.shape[0] for o in obs_list] + [1])
    A = max([o.opp_act.shape[0] for o in obs_list] + [1])
    T = 3 + N
    out = {
        "game": torch.stack([o.game for o in obs_list]),
        "players": torch.stack([o.players for o in obs_list]),
        "ent": torch.zeros(B, N, W.DIMS["ent"]), "ent_id": torch.full((B, N), -1, dtype=torch.long),
        "ent_mask": torch.zeros(B, N, dtype=torch.bool),
        "edges": torch.zeros(B, T, T, dtype=torch.long), "tok_mask": torch.zeros(B, T, dtype=torch.bool),
        "cand_type": torch.zeros(B, K, dtype=torch.long), "cand": torch.zeros(B, K, W.DIMS["cand"]),
        "cand_mask": torch.zeros(B, K, dtype=torch.bool), "refers": torch.zeros(B, K, T),
        "opp_hand": torch.zeros(B, H, W.DIMS["opp_hand"]), "opp_hand_id": torch.full((B, H), -1, dtype=torch.long),
        "opp_hand_mask": torch.zeros(B, H, dtype=torch.bool),
        "opp_deck": torch.zeros(B, Dk, W.DIMS["opp_deck"]), "opp_deck_id": torch.full((B, Dk), -1, dtype=torch.long),
        "opp_deck_mask": torch.zeros(B, Dk, dtype=torch.bool),
        "opp_act": torch.zeros(B, A, W.DIMS["opp_action"]), "opp_act_refers": torch.zeros(B, A, T),
        "opp_act_mask": torch.zeros(B, A, dtype=torch.bool),
    }
    for b, o in enumerate(obs_list):
        n, k, t = o.ent.shape[0], o.cand.shape[0], o.n_tokens
        out["ent"][b, :n] = o.ent; out["ent_id"][b, :n] = o.ent_id; out["ent_mask"][b, :n] = True
        out["edges"][b, :t, :t] = o.edges; out["tok_mask"][b, :t] = True
        out["cand_type"][b, :k] = o.cand_type; out["cand"][b, :k] = o.cand; out["cand_mask"][b, :k] = True
        out["refers"][b, :k, :t] = o.refers
        h, d, a = o.opp_hand.shape[0], o.opp_deck.shape[0], o.opp_act.shape[0]
        out["opp_hand"][b, :h] = o.opp_hand; out["opp_hand_id"][b, :h] = o.opp_hand_id; out["opp_hand_mask"][b, :h] = True
        out["opp_deck"][b, :d] = o.opp_deck; out["opp_deck_id"][b, :d] = o.opp_deck_id; out["opp_deck_mask"][b, :d] = True
        out["opp_act"][b, :a] = o.opp_act; out["opp_act_refers"][b, :a, :t] = o.opp_act_refers; out["opp_act_mask"][b, :a] = True
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--card-emb", default="card_emb_v8")
    args = ap.parse_args()
    ids = CardIds()
    bad = 0
    for path in args.files:
        if "reply" in os.path.basename(path):
            print(f"skip {os.path.basename(path)}: replies are the server's own output, checked by wire_validate.py")
            continue
        hello, n, err, resolved, total = None, 0, None, 0, 0
        with open(path, encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                m = json.loads(line)
                try:
                    if m.get("t") == "hello":
                        hello = check_hello_v7(m, args.card_emb)
                    elif m.get("t") == "consult":
                        if hello is None:
                            raise ValueError("consult before hello")
                        o = parse_consult(m, ids, hello)
                        n += 1; total += len(o.ent_id); resolved += int((o.ent_id >= 0).sum())
                except ValueError as e:
                    err = f"line {ln}: {e}"
                    break
        expect_fail = os.path.basename(path).startswith("broken_")
        ok = (err is None) != expect_fail
        bad += 0 if ok else 1
        tag = "ok  " if ok else "BAD "
        if err:
            print(f"{tag} {os.path.basename(path)}: refused ({err[:110]})")
        else:
            print(f"{tag} {os.path.basename(path)}: {n} consults, names resolved {resolved}/{total}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
