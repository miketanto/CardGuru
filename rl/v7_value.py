"""Phase 4e (v7 plan §2): the value trunk (design decision 6: fully separate).

Own token builders (a second `TokenBuilders`, sharing only the frozen card
table), its own 4-layer encoder, and the privileged rows — the v6 critic
channel `oe` and, from 3d on, `v7_oe_hand` (the true opponent hand) — enter
HERE and only here, as extra tokens.  The value is read off the encoded
game token.

    critic = ValueTrunk(table)
    v = critic(batch, oe_rows, opp_hand_true_ids)      # [B]

Leak gate (tests/test_v7_value.py, rl/probes/leak.py levels 1-3): the
policy path never receives the privileged keys (level 1: `V7Obs.v6`
carries `oe` for the critic only and the token builders do not read it),
the policy logits are bit-identical under a swap of the privileged
content (level 2), and this critic's value moves under the same swap
(level 3), so the channel is contained AND live.
"""
import os
import sys

import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v7_net as N               # noqa: E402
import v7_encoder as E           # noqa: E402

OE_DIM = 48                      # v6 oracle rows are entity rows of the opponent's hidden zones (edim 48)


class ValueTrunk(nn.Module):
    def __init__(self, table, d=N.D_TOK, layers=4, oe_dim=OE_DIM):
        super().__init__()
        self.build = N.TokenBuilders(table, d=d)                       # its own copies of every builder
        self.enc = E.StateGraphEncoder(d=d, layers=layers)
        self.oe_mlp = N.mlp(oe_dim, d)                                  # privileged v6 rows -> tokens
        self.true_hand_mlp = N.mlp(table.adapter.out_features + 1, d)   # privileged true opponent hand (3d+)
        self.value = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, d), nn.GELU(), nn.Linear(d, 1))
        self.d = d

    def privileged_tokens(self, b, oe_rows=None, true_hand_ids=None):
        """oe_rows: [B, M, OE_DIM] float + mask [B, M]; true_hand_ids: [B, Hh] long (-1 pad)."""
        B = b["game"].shape[0]
        dev = b["game"].device
        toks, masks = [], []
        if oe_rows is not None:
            rows, m = oe_rows
            toks.append(self.oe_mlp(rows) * m.unsqueeze(-1).to(rows.dtype)); masks.append(m)
        if true_hand_ids is not None:
            c, unk = self.build.table(true_hand_ids)
            m = true_hand_ids >= 0
            toks.append(self.true_hand_mlp(torch.cat([c, unk], -1)) * m.unsqueeze(-1).to(c.dtype)); masks.append(m)
        if not toks:
            return torch.zeros(B, 0, self.d, device=dev), torch.zeros(B, 0, dtype=torch.bool, device=dev)
        return torch.cat(toks, 1), torch.cat(masks, 1)

    def forward(self, b, oe_rows=None, true_hand_ids=None, ctx=None, D_me=None, D_opp=None):
        toks = self.build(b, ctx=ctx, D_me=D_me, D_opp=D_opp)
        priv, pmask = self.privileged_tokens(b, oe_rows, true_hand_ids)
        # append the privileged tokens as one more group; the encoder's assembler
        # treats extra groups like opponent-action tokens (no wire edges)
        toks = dict(toks)
        toks["opp_act"] = torch.cat([toks["opp_act"], priv], 1)
        toks["opp_act_mask"] = torch.cat([toks["opp_act_mask"], pmask], 1)
        T = toks["opp_act_refers"].shape[2]
        toks["opp_act_refers"] = torch.cat([toks["opp_act_refers"],
                                            torch.zeros(priv.shape[0], priv.shape[1], T, dtype=toks["opp_act_refers"].dtype,
                                                        device=priv.device)], 1)
        enc = self.enc(toks, ent_raw=b["ent"])
        return self.value(enc["game"][:, 0]).squeeze(-1)
