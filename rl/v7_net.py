"""Phase 4b (v7 plan §2): the v7 token builders (design L3).

Shared identity in, zone-specific MLP out.  Every token type has its own
MLP: `MLP(x) = Linear(512 -> 256)(GELU(Linear(in -> 512)(LN(x))))`; no
pooling anywhere; padding is masked by the caller (`V7Obs` masks).

    table  = CardTable("card_emb_v8")            # frozen e_card rows + a trainable Linear(128,128) adapter
    build  = TokenBuilders(table)                 # or TokenBuilders(CardTable(random=True)) for shape tests
    toks   = build(batch)                         # batch = v7_obs.collate([...]);  dict of [B, n, 256] + masks

Token groups produced (all d = 256):
    game [B,1]  players [B,2]  ent [B,N]  cand [B,K]  opp_hand [B,H]  opp_deck [B,D]  opp_act [B,A]

Identity: `c'` for a card is `adapter(e_card[id])` (a zero row for id -1
plus an unknown flag); an optional per-game override table (`ctx`) lets
the deck-context vectors `c'_i` (deck_ctx_v1) replace `e_card` for the
cards of the two decks, and the pooled deck vectors `D_me`, `D_opp`
join the game token, exactly as the design's L1 says.  With no `ctx`
the game token gets zeros there.

The faithfulness probe (rl/probes/faithfulness.py) is applied to the
outputs of this stage in tests/test_v7_net.py: every planted input
field must be linearly recoverable after the MLPs.
"""
import os
import sys

import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wire_validate as W                                   # noqa: E402

D_TOK = 256
D_C = 128
ZONES = ["battlefield", "hand", "stack", "graveyard", "exile", "library", "command"]


class MLPSkip(nn.Module):
    """MLP_z(x) = Linear(512 -> d)(GELU(Linear(in -> 512)(LN(x))))  +  Linear(in -> d)(x)

    The linear skip is the information-preservation guarantee (design principle
    3): every input field stays linearly recoverable from the token regardless
    of what the nonlinear path learns, so the faithfulness probe after L3 is a
    property of the architecture, not of a training run.  tests/test_v7_net.py
    measured an MLP-only builder attenuating planted fields (tapped, power R^2
    0.89) before this skip existed."""

    def __init__(self, d_in, d_out=D_TOK, hidden=512):
        super().__init__()
        self.body = nn.Sequential(nn.LayerNorm(d_in), nn.Linear(d_in, hidden), nn.GELU(), nn.Linear(hidden, d_out))
        self.skip = nn.Linear(d_in, d_out)
        # Start as the linear image of the inputs: the body's output layer is zero at
        # init, so an untrained token is exactly Linear(x) and the nonlinear facts are
        # learned on top of a faithful base rather than in competition with it.
        nn.init.zeros_(self.body[-1].weight)
        nn.init.zeros_(self.body[-1].bias)

    def forward(self, x):
        return self.body(x) + self.skip(x)


def mlp(d_in, d_out=D_TOK, hidden=512):
    return MLPSkip(d_in, d_out, hidden)


class CardTable(nn.Module):
    """Frozen e_card rows (row n = the unknown card, zeros) + trainable adapter."""

    def __init__(self, version="card_emb_v8", random=False, n_random=1000, d_c=D_C):
        super().__init__()
        if random:
            emb = torch.randn(n_random, d_c) * 0.5
            self.version = "random"
        else:
            path = os.path.join(HERE, "artifacts", version, "emb.pt")
            emb = torch.load(path).float()
            self.version = version
        self.register_buffer("table", torch.cat([emb, torch.zeros(1, emb.shape[1])]))   # last row = unknown
        self.n = emb.shape[0]
        self.adapter = nn.Linear(emb.shape[1], d_c)
        with torch.no_grad():                        # start as identity: e_card passes through untouched
            self.adapter.weight.copy_(torch.eye(d_c, emb.shape[1]))
            self.adapter.bias.zero_()

    def forward(self, ids, ctx=None):
        """ids [...] long (-1 unknown) -> (c' [..., d_c], unknown flag [..., 1])."""
        idx = torch.where(ids < 0, torch.full_like(ids, self.n), ids.clamp(max=self.n))
        e = self.table[idx]
        if ctx is not None:                           # per-game override: {card_id: c'_i}
            e = ctx(ids, e)
        unk = (ids < 0).to(e.dtype).unsqueeze(-1)
        return self.adapter(e) * (1.0 - unk), unk


class TokenBuilders(nn.Module):
    def __init__(self, table, d=D_TOK, n_ctypes=W.CTYPES):
        super().__init__()
        self.table = table
        d_c = table.adapter.out_features
        self.zone_mlps = nn.ModuleList(mlp(d_c + 1 + W.DIMS["ent"], d) for _ in ZONES)
        self.player_mlp = mlp(W.DIMS["player"] + 1, d)                    # + side flag (me / opp)
        self.game_mlp = mlp(W.DIMS["game"] + 2 * d_c, d)                  # + D_me + D_opp
        self.ctype_emb = nn.Embedding(n_ctypes, 16)
        self.cand_mlp = mlp(16 + W.DIMS["cand"], d)
        self.opp_hand_mlp = mlp(d_c + 1 + W.DIMS["opp_hand"], d)
        self.opp_deck_mlp = mlp(d_c + 1 + W.DIMS["opp_deck"], d)
        self.opp_act_mlp = mlp(W.DIMS["opp_action"], d)
        self.unknown_hand = nn.Parameter(torch.zeros(d_c))                # identity vector of an unknown hand card
        self.d = d

    def forward(self, b, ctx=None, D_me=None, D_opp=None):
        """b: the dict from v7_obs.collate (tensors on this module's device)."""
        B = b["game"].shape[0]
        d_c = self.table.adapter.out_features
        dev = b["game"].device
        # entities: identity + fields, routed by zone
        c, unk = self.table(b["ent_id"], ctx)                              # [B, N, d_c], [B, N, 1]
        x = torch.cat([c, unk, b["ent"]], -1)                               # [B, N, d_c + 1 + 64]
        zone = b["ent"][..., :W.ZONES].argmax(-1)                            # [B, N]
        outs = torch.stack([m(x) for m in self.zone_mlps], 0)                # [Z, B, N, d]
        ent = outs.gather(0, zone.unsqueeze(0).unsqueeze(-1).expand(1, B, x.shape[1], self.d)).squeeze(0)
        ent = ent * b["ent_mask"].unsqueeze(-1).to(ent.dtype)
        # players
        side = torch.tensor([[0.0], [1.0]], device=dev).unsqueeze(0).expand(B, 2, 1)
        players = self.player_mlp(torch.cat([b["players"], side], -1))
        # game
        zeros = torch.zeros(B, d_c, device=dev)
        game = self.game_mlp(torch.cat([b["game"], D_me if D_me is not None else zeros,
                                        D_opp if D_opp is not None else zeros], -1)).unsqueeze(1)
        # candidates
        cand = self.cand_mlp(torch.cat([self.ctype_emb(b["cand_type"]), b["cand"]], -1))
        cand = cand * b["cand_mask"].unsqueeze(-1).to(cand.dtype)
        # opponent tokens
        ch, unk_h = self.table(b["opp_hand_id"], ctx)
        ch = ch + unk_h * self.unknown_hand                                 # unknown slot -> learned identity
        opp_hand = self.opp_hand_mlp(torch.cat([ch, unk_h, b["opp_hand"]], -1)) * b["opp_hand_mask"].unsqueeze(-1).float()
        cd, unk_d = self.table(b["opp_deck_id"], ctx)
        opp_deck = self.opp_deck_mlp(torch.cat([cd, unk_d, b["opp_deck"]], -1)) * b["opp_deck_mask"].unsqueeze(-1).float()
        opp_act = self.opp_act_mlp(b["opp_act"]) * b["opp_act_mask"].unsqueeze(-1).float()
        return {"game": game, "players": players, "ent": ent, "cand": cand,
                "opp_hand": opp_hand, "opp_deck": opp_deck, "opp_act": opp_act,
                "ent_mask": b["ent_mask"], "cand_mask": b["cand_mask"], "tok_mask": b["tok_mask"],
                "opp_hand_mask": b["opp_hand_mask"], "opp_deck_mask": b["opp_deck_mask"], "opp_act_mask": b["opp_act_mask"],
                "edges": b["edges"], "refers": b["refers"], "opp_act_refers": b["opp_act_refers"]}

    def all_tokens(self, toks):
        """Concatenate in the token index space: [game | me | opp | ent...] -> [B, T, d], mask [B, T]."""
        seq = torch.cat([toks["game"], toks["players"], toks["ent"]], 1)
        return seq, toks["tok_mask"]
